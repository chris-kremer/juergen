"""
Portfolio dashboard for displaying user's portfolio overview
"""

from html import escape
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from typing import List, Dict
from price_fetcher import (
    PriceFetcher,
    fetch_stock_history_eur,
    get_return_base_price_eur,
)
from config import ASSET_SNAPSHOT_DATE, STOCKS
from ownership import (
    get_ownership_percentage,
    get_unit_balances,
    get_unit_price,
    get_user_portfolio_value,
)
from translations import format_user_display_name, get_language, get_text, format_currency, format_currency_change
from celebration import (
    build_annika_2500_celebration_html,
    build_doubling_celebration_html,
    resolve_doubling_celebration_return,
    should_show_annika_2500_celebration,
    should_show_celebration_divider,
)
from ui_theme import build_dashboard_header

pio.templates.default = "plotly_white"
px.defaults.template = "plotly_white"

BENCHMARK_ISIN = "IE00B4L5Y983"
BENCHMARK_LABEL = "MSCI World"


def _is_benchmark(stock: Dict) -> bool:
    return stock.get("isin") == BENCHMARK_ISIN


def _stock_key(stock: Dict) -> str:
    return stock.get("isin") or stock.get("symbol") or stock.get("wkn") or stock["name"]


def _display_symbol(stock: Dict) -> str:
    return stock.get("symbol") or stock.get("wkn") or stock["name"]


def _user_percentage(user: Dict) -> float:
    return get_ownership_percentage(user["username"])


def build_portfolio_heatmap_rows(
    stocks: List[Dict],
    user_percentage: float = 1.0,
    include_cash: bool = True,
    color_mode: str = "daily",
) -> List[Dict]:
    """Return leaf data for a value-sized, return-colored portfolio treemap."""
    if color_mode not in {"daily", "since_purchase"}:
        raise ValueError(f"Unsupported heatmap color mode: {color_mode}")

    rows = []
    for stock in stocks:
        is_cash = stock.get("symbol") == "CASH"
        if is_cash and not include_cash:
            continue

        current_price = float(stock.get("current_price", stock.get("price", 0.0)))
        position_value = float(stock.get("quantity", 0.0)) * current_price
        user_value = position_value * user_percentage
        if user_value <= 0:
            continue

        if color_mode == "daily":
            previous_close = stock.get("previous_close")
            performance = (
                (current_price - float(previous_close)) / float(previous_close) * 100
                if previous_close is not None and float(previous_close) > 0
                else 0.0
            )
        else:
            cost_basis = float(stock.get("cost_basis_eur", 0.0))
            performance = (
                (position_value - cost_basis) / cost_basis * 100
                if cost_basis > 0
                else 0.0
            )

        rows.append({
            "key": _stock_key(stock),
            "symbol": _display_symbol(stock),
            "name": stock.get("name", _display_symbol(stock)),
            "industry": "Cash" if is_cash else (stock.get("industry") or "Other"),
            "value_eur": user_value,
            "performance_pct": performance,
            "quantity": float(stock.get("quantity", 0.0)) * user_percentage,
        })

    return rows


def get_confirmed_portfolio_capital_events(users: List[Dict]) -> List[Dict]:
    """Collect the owner ledger's net capital events without double-counting initials."""
    events = []
    for owner in users:
        if owner.get("username") == "user":
            continue

        payments = owner.get("payments")
        if payments is not None:
            for payment in payments:
                events.append({
                    "date": payment["date"],
                    "amount_eur": float(payment["amount"]),
                    "owner": owner["username"],
                })
        elif owner.get("paid_date") and owner.get("initial_investment") is not None:
            events.append({
                "date": owner["paid_date"],
                "amount_eur": float(owner["initial_investment"]),
                "owner": owner["username"],
            })

    return sorted(events, key=lambda event: event["date"])


def get_confirmed_user_investment(username: str, users: List[Dict]) -> float:
    """Return confirmed net invested capital for one owner or the whole pool."""
    events = get_confirmed_portfolio_capital_events(users)
    if username == "user":
        return sum(event["amount_eur"] for event in events)
    return sum(
        event["amount_eur"]
        for event in events
        if event["owner"] == username
    )


def build_confirmed_capital_series(users: List[Dict], as_of) -> pd.DataFrame:
    """Return month-level cumulative net capital attributed to all owners."""
    events = get_confirmed_portfolio_capital_events(users)
    if not events:
        return pd.DataFrame(columns=["Date", "Net Pay-ins", "Cumulative Pay-ins"])

    event_frame = pd.DataFrame(events)
    event_frame["Date"] = (
        pd.to_datetime(event_frame["date"])
        .dt.to_period("M")
        .dt.to_timestamp()
    )
    monthly = (
        event_frame.groupby("Date", as_index=False)["amount_eur"]
        .sum()
        .rename(columns={"amount_eur": "Net Pay-ins"})
        .sort_values("Date")
    )
    current_month = pd.Timestamp(as_of).to_period("M").to_timestamp()
    if current_month not in set(monthly["Date"]):
        monthly = pd.concat([
            monthly,
            pd.DataFrame([{"Date": current_month, "Net Pay-ins": 0.0}]),
        ]).sort_values("Date")
    monthly["Cumulative Pay-ins"] = monthly["Net Pay-ins"].cumsum()
    return monthly.reset_index(drop=True)


def calculate_tax_simulation(
    stocks: List[Dict],
    user_percentage: float = 1.0,
    tax_rate: float = 0.25,
    invested_capital_eur: float = 0.0,
    allocated_tax_eur=None,
) -> Dict:
    """Estimate liquidation tax and a gain-only 25% equivalent value."""
    if not 0 <= tax_rate < 1:
        raise ValueError("Tax rate must be between zero and one")

    gross_value = 0.0
    cost_basis = 0.0
    for stock in stocks:
        current_price = float(stock.get("current_price", stock.get("price", 0.0)))
        gross_value += float(stock.get("quantity", 0.0)) * current_price
        cost_basis += float(stock.get("cost_basis_eur", 0.0))

    gross_value *= user_percentage
    cost_basis *= user_percentage
    taxable_gain = max(gross_value - cost_basis, 0.0)
    economic_gain = max(gross_value - invested_capital_eur, 0.0)
    pooled_tax_share = taxable_gain * tax_rate
    estimated_tax = (
        pooled_tax_share
        if allocated_tax_eur is None
        else max(float(allocated_tax_eur), 0.0)
    )
    net_liquidation_value = gross_value - estimated_tax

    # Find the hypothetical gross value whose gain above the user's investment,
    # taxed at 25%, leaves exactly the simulated net liquidation value.
    equivalent_tax_rate = 0.25
    if net_liquidation_value > invested_capital_eur:
        tax_equivalent_value = invested_capital_eur + (
            (net_liquidation_value - invested_capital_eur)
            / (1.0 - equivalent_tax_rate)
        )
    else:
        tax_equivalent_value = net_liquidation_value

    standard_tax_on_economic_gain = economic_gain * equivalent_tax_rate
    effective_tax_burden = (
        estimated_tax / economic_gain
        if economic_gain > 0
        else 0.0
    )
    return {
        "gross_value_eur": gross_value,
        "cost_basis_eur": cost_basis,
        "invested_capital_eur": invested_capital_eur,
        "taxable_gain_eur": taxable_gain,
        "economic_gain_eur": economic_gain,
        "pooled_tax_share_eur": pooled_tax_share,
        "estimated_tax_eur": estimated_tax,
        "net_liquidation_value_eur": net_liquidation_value,
        "standard_tax_on_economic_gain_eur": standard_tax_on_economic_gain,
        "tax_equivalent_value_eur": tax_equivalent_value,
        "effective_tax_burden": effective_tax_burden,
        "tax_rate": tax_rate,
    }


def allocate_tax_by_earnings(total_tax_eur: float, earnings_by_owner: Dict) -> Dict:
    """Allocate one pooled tax liability in proportion to positive owner earnings."""
    positive_earnings = {
        owner: max(float(earnings), 0.0)
        for owner, earnings in earnings_by_owner.items()
    }
    total_earnings = sum(positive_earnings.values())
    if total_earnings <= 0:
        return {owner: 0.0 for owner in positive_earnings}
    return {
        owner: float(total_tax_eur) * earnings / total_earnings
        for owner, earnings in positive_earnings.items()
    }


def cap_pooled_tax_to_economic_gains(
    tax_from_portfolio_basis_eur: float,
    total_economic_gains_eur: float,
    tax_rate: float,
) -> float:
    """Do not tax the owner pool above the selected rate on its economic gains."""
    return min(
        max(float(tax_from_portfolio_basis_eur), 0.0),
        max(float(total_economic_gains_eur), 0.0) * tax_rate,
    )


def calculate_historical_portfolio_peak(histories: Dict, stocks: List[Dict]):
    """Return the peak daily-close value for the current portfolio composition."""
    non_cash_stocks = [stock for stock in stocks if stock.get("symbol") != "CASH"]
    if any(
        _stock_key(stock) not in histories
        or histories[_stock_key(stock)] is None
        or histories[_stock_key(stock)].empty
        for stock in non_cash_stocks
    ):
        return None

    position_series = []
    for stock in non_cash_stocks:
        closes = histories[_stock_key(stock)]["Close"].astype(float)
        closes.name = _stock_key(stock)
        position_series.append(closes * stock["quantity"])

    if not position_series:
        return None

    # Only compare dates where every current holding has a valid close. This
    # avoids falsely declaring a high from a partially loaded history.
    portfolio_history = pd.concat(position_series, axis=1).sort_index().ffill().dropna()
    if portfolio_history.empty:
        return None

    cash_value = sum(
        stock["quantity"] * stock.get("price", 1.0)
        for stock in stocks
        if stock.get("symbol") == "CASH"
    )
    daily_totals = portfolio_history.sum(axis=1) + cash_value
    return float(daily_totals.max())


def is_portfolio_all_time_high(current_value: float, historical_peak) -> bool:
    """Return True only when a trustworthy historical peak is available."""
    return historical_peak is not None and current_value >= historical_peak


def resolve_all_time_high_state(
    current_value: float,
    historical_peak,
    preview_requested: bool = False,
) -> bool:
    """Resolve the real or explicitly simulated all-time-high display state."""
    return preview_requested or is_portfolio_all_time_high(current_value, historical_peak)


class PortfolioDashboard:
    def __init__(self, price_fetcher: PriceFetcher):
        self.price_fetcher = price_fetcher

    def _plotly_chart(self, fig, **kwargs):
        """Render Plotly charts with the restrained portfolio theme."""
        fig.update_layout(
            template="plotly_white",
            dragmode=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#ffffff",
            font=dict(color="#171c18", family="Inter, sans-serif"),
            title_font=dict(color="#171c18", size=19),
            colorway=["#176b4d", "#a6782d", "#54706a", "#7b6d8d", "#ba6f52", "#4878a8"],
            hoverlabel=dict(
                bgcolor="#171c18",
                font_color="#ffffff",
                bordercolor="#171c18",
            ),
            legend=dict(
                bgcolor="rgba(255,255,255,0.86)",
                bordercolor="rgba(201,208,200,.8)",
                borderwidth=1,
                font=dict(color="#37413a"),
            ),
            margin=dict(l=40, r=24, t=56, b=44),
        )
        fig.update_xaxes(
            fixedrange=True,
            color="#68736b",
            gridcolor="#edf0ec",
            zerolinecolor="#c9d0c8",
            linecolor="#c9d0c8",
        )
        fig.update_yaxes(
            fixedrange=True,
            color="#68736b",
            gridcolor="#edf0ec",
            zerolinecolor="#c9d0c8",
            linecolor="#c9d0c8",
        )
        requested_config = kwargs.pop("config", {}) or {}
        chart_config = {
            **requested_config,
            "displayModeBar": False,
            "scrollZoom": False,
            "doubleClick": False,
            "showAxisDragHandles": False,
            "showAxisRangeEntryBoxes": False,
            "editable": False,
            # Preserve hover labels and intentional legend clicks.
            "staticPlot": False,
            "responsive": True,
        }
        st.plotly_chart(
            fig,
            use_container_width=True,
            theme=None,
            config=chart_config,
            **kwargs,
        )

    def _show_metric_grid(self, metrics: List[Dict]):
        """Render responsive metric cards without Streamlit column truncation."""
        cards = []
        has_all_time_high = False
        for metric in metrics:
            label = escape(str(metric["label"]))
            value = escape(str(metric["value"]))
            delta = metric.get("delta")
            delta_html = ""
            if delta:
                delta_text = str(delta)
                if delta_text.strip().startswith("+") or delta_text.strip().startswith("↑"):
                    delta_class = "positive"
                    prefix = "↑ "
                elif delta_text.strip().startswith("-") or delta_text.strip().startswith("↓"):
                    delta_class = "negative"
                    prefix = "↓ "
                else:
                    delta_class = "neutral"
                    prefix = ""
                explicit_delta_class = metric.get("delta_class")
                if explicit_delta_class in {"positive", "negative", "neutral"}:
                    delta_class = explicit_delta_class
                delta_html = f'<div class="metric-delta {delta_class}">{prefix}{escape(delta_text)}</div>'

            is_all_time_high = bool(metric.get("all_time_high"))
            has_all_time_high = has_all_time_high or is_all_time_high
            celebration_text = metric.get("celebration_text")
            celebration_html = (
                f'<div class="ath-celebration-copy">{escape(str(celebration_text))}</div>'
                if is_all_time_high and celebration_text
                else ""
            )
            card_class = "metric-card metric-card--all-time-high" if is_all_time_high else "metric-card"
            interactive = (
                f' tabindex="0" role="button" aria-label="{label}: {escape(str(delta or ""))}"'
                if is_all_time_high
                else ""
            )
            cards.append(
                f'<div class="{card_class}"{interactive}>'
                f'<div class="metric-label">{label}</div>'
                f'<div class="metric-value">{value}</div>'
                f'{delta_html}'
                f'{celebration_html}'
                f'</div>'
            )

        confetti_html = ""
        if has_all_time_high:
            palette = ("#176b4d", "#d7a83f", "#ec6b5f", "#4f83cc", "#8b68b8", "#f0c85b")
            pieces = []
            for index in range(30):
                left = (index * 37 + 7) % 100
                drift = ((index * 29) % 31) - 15
                delay = (index % 8) * 0.045
                duration = 1.35 + (index % 5) * 0.13
                rotation = 260 + (index % 7) * 70
                pieces.append(
                    '<span style="'
                    f'--ath-x:{left}vw;--ath-drift:{drift}vw;--ath-delay:{delay:.3f}s;'
                    f'--ath-duration:{duration:.2f}s;--ath-rotation:{rotation}deg;'
                    f'--ath-color:{palette[index % len(palette)]}'
                    '"></span>'
                )
            confetti_html = f'<div class="ath-confetti-layer" aria-hidden="true">{"".join(pieces)}</div>'

        st.markdown(
            f'<div class="metric-grid">{"".join(cards)}{confetti_html}</div>',
            unsafe_allow_html=True,
        )

    def _get_user_historical_portfolio_peak(self, stocks: List[Dict], user: Dict):
        """Calculate the user's peak daily-close value since their first investment."""
        from datetime import date, datetime, timedelta

        investment_dates = [
            payment.get("date")
            for payment in user.get("payments", [])
            if payment.get("date")
        ]
        if user.get("paid_date"):
            investment_dates.append(user["paid_date"])
        if not investment_dates:
            return None

        start_date = datetime.strptime(min(investment_dates), "%Y-%m-%d").date()
        end_date = date.today() + timedelta(days=1)
        histories = {}
        for stock in stocks:
            if stock.get("symbol") == "CASH":
                continue
            histories[_stock_key(stock)] = fetch_stock_history_eur(
                stock,
                start=start_date,
                end=end_date,
            )

        total_peak = calculate_historical_portfolio_peak(histories, stocks)
        if total_peak is None:
            return None
        return get_user_portfolio_value(user["username"], total_peak)
    
    def show_dashboard(self, user: Dict, stocks_with_prices: List[Dict], failed_symbols: List[str]):
        """Display the main portfolio dashboard"""
        
        lang = get_language(user['username'])
        preview_requested = bool(
            st.session_state.pop('kremer_doubling_preview_requested', False)
        )
        all_time_high_preview_requested = bool(
            st.session_state.pop('all_time_high_preview_requested', False)
        )
        
        # Branded dashboard header
        st.markdown(
            build_dashboard_header(user['username'], lang),
            unsafe_allow_html=True,
        )
        
        # Show price fetch status
        if failed_symbols:
            with st.expander(get_text('price_fetch_status', lang), expanded=False):
                st.warning(get_text('could_not_fetch', lang, len(failed_symbols)))
                for symbol in failed_symbols:
                    st.text(f"• {symbol}")
        
        # Calculate portfolio metrics
        total_portfolio_value = self.price_fetcher.get_portfolio_value(stocks_with_prices)
        user_portfolio_value = get_user_portfolio_value(user['username'], total_portfolio_value)

        # Calculate returns from tranches (not from initial_investment field)
        total_invested, total_return_amount, total_return_percentage = self._calculate_tranche_returns(user, total_portfolio_value)

        # Fallback to initial_investment if no tranches configured
        if total_invested == 0:
            initial_investment = user.get('initial_investment', 0)
            total_return_amount = user_portfolio_value - initial_investment
            total_return_percentage = (total_return_amount / initial_investment * 100) if initial_investment > 0 else 0
        
        # Calculate total daily change
        total_daily_change = sum([
            self.price_fetcher.get_user_daily_change_value(stock, _user_percentage(user))
            for stock in stocks_with_prices
        ])
        
        # Calculate daily percentage change
        daily_percentage = (total_daily_change / user_portfolio_value * 100) if user_portfolio_value > 0 else 0
        
        # Calculate top performers for metrics row
        stock_changes = []
        for stock in stocks_with_prices:
            if stock.get('symbol') == 'CASH':
                continue
            daily_change_pct = self.price_fetcher.get_daily_change_percentage(stock)
            daily_change_value = self.price_fetcher.get_user_daily_change_value(stock, _user_percentage(user))
            if stock.get('price_source') == 'live':
                stock_changes.append({
                    'symbol': _display_symbol(stock),
                    'name': stock['name'],
                    'daily_change_pct': daily_change_pct,
                    'daily_change_value': daily_change_value,
                    'current_price': stock.get('current_price', stock['price'])
                })

        live_count = len([s for s in stocks_with_prices if s.get('price_source') == 'live'])
        top_pct_stock = max(stock_changes, key=lambda x: x['daily_change_pct']) if stock_changes else None
        top_value_stock = max(stock_changes, key=lambda x: x['daily_change_value']) if stock_changes else None

        historical_peak = None
        if not failed_symbols and not all_time_high_preview_requested:
            historical_peak = self._get_user_historical_portfolio_peak(stocks_with_prices, user)
        all_time_high_active = resolve_all_time_high_state(
            user_portfolio_value,
            historical_peak,
            preview_requested=all_time_high_preview_requested,
        )
        all_time_high_label = get_text('all_time_high', lang) if all_time_high_active else None

        self._show_metric_grid([
            {
                "label": get_text('your_portfolio_value', lang),
                "value": format_currency(user_portfolio_value, lang),
                "delta": all_time_high_label,
                "delta_class": "positive",
                "all_time_high": bool(all_time_high_label),
                "celebration_text": get_text('all_time_high_celebration', lang),
            },
            {
                "label": get_text('total_return', lang),
                "value": format_currency_change(total_return_amount, lang),
                "delta": f"{total_return_percentage:+.1f}%" if total_return_percentage != 0 else None,
            },
            {
                "label": get_text('daily_change', lang),
                "value": format_currency_change(total_daily_change, lang),
                "delta": f"{daily_percentage:+.2f}%" if daily_percentage != 0 else None,
            },
            {
                "label": get_text('live_prices', lang),
                "value": f"{live_count}/{len(stocks_with_prices)-1}",  # -1 for cash
            },
            {
                "label": get_text('top_daily_pct', lang),
                "value": top_pct_stock['name'] if top_pct_stock else "N/A",
                "delta": f"{top_pct_stock['daily_change_pct']:+.2f}%" if top_pct_stock else None,
            },
            {
                "label": get_text('top_daily_value', lang),
                "value": top_value_stock['name'] if top_value_stock else "N/A",
                "delta": format_currency_change(top_value_stock['daily_change_value'], lang) if top_value_stock else None,
            },
        ])

        celebration_return = resolve_doubling_celebration_return(
            user['username'],
            total_return_percentage,
            preview_requested=preview_requested,
        )
        if celebration_return is not None:
            st.balloons()
            st.markdown(
                build_doubling_celebration_html(celebration_return),
                unsafe_allow_html=True,
            )

        if should_show_annika_2500_celebration(
            user['username'], user_portfolio_value
        ):
            st.balloons()
            st.markdown(
                build_annika_2500_celebration_html(user_portfolio_value),
                unsafe_allow_html=True,
            )

        if should_show_celebration_divider(celebration_return):
            st.markdown("---")

        self.show_portfolio_heatmap(stocks_with_prices, user, lang)

        st.markdown("---")

        self.show_tax_overview(stocks_with_prices, user, lang)

        st.markdown("---")

        # Investment tranche performance (moved up for better visibility)
        self.show_investment_tranches(user, stocks_with_prices, lang)

        st.markdown("---")

        # Show user overview if this is the "user" account
        if user['username'] == 'user':
            self.show_all_users_overview(stocks_with_prices, lang)
            st.markdown("---")

            self.show_admin_aum_chart(stocks_with_prices, lang)
            st.markdown("---")

            # Show login statistics for admin
            self.show_login_statistics(lang)
            st.markdown("---")

        # Historical portfolio performance chart
        self.show_historical_performance_chart(user, lang)

        st.markdown("---")

        # Individual stock yearly performance chart
        self.show_individual_stock_performance_chart(user, lang)

        st.markdown("---")

        # Multi-period returns chart
        self.show_returns_chart(user, lang)

        st.markdown("---")
        
        # Portfolio breakdown charts
        self.show_portfolio_breakdown(stocks_with_prices, user, lang)
        
        # Detailed holdings table
        self.show_holdings_table(stocks_with_prices, user, lang)

        # Keep the temporary replay control out of the normal dashboard flow.
        if user['username'] == 'kremer':
            with st.expander('⋯', expanded=False):
                st.button(
                    get_text('preview_doubling_celebration', lang),
                    key='kremer_doubling_preview_button',
                    on_click=lambda: st.session_state.__setitem__(
                        'kremer_doubling_preview_requested', True
                    ),
                )
                st.button(
                    get_text('preview_all_time_high', lang),
                    key='all_time_high_preview_button',
                    on_click=lambda: st.session_state.__setitem__(
                        'all_time_high_preview_requested', True
                    ),
                )

    def show_all_users_overview(self, stocks_with_prices: List[Dict], lang: str):
        """Show overview of all users' portfolio values (only for 'user' account)"""
        from config import USERS
        
        st.subheader(get_text('all_users_overview', lang))
        

        
        # Calculate total portfolio value
        total_portfolio_value = self.price_fetcher.get_portfolio_value(stocks_with_prices)
        unit_balances = get_unit_balances()
        current_unit_price = get_unit_price(total_portfolio_value)
        
        # Prepare data for all users
        user_data = []
        for user_info in USERS:
            if user_info['username'] != 'user':  # Skip the overview user itself
                user_value = get_user_portfolio_value(user_info['username'], total_portfolio_value)
                initial_investment = user_info.get('initial_investment', 0)
                total_return = user_value - initial_investment
                return_percentage = (total_return / initial_investment * 100) if initial_investment > 0 else 0
                
                user_data.append({
                    'User': format_user_display_name(user_info['username']),
                    'Units': float(unit_balances[user_info['username']]),
                    'Portfolio Value': user_value,
                    'Initial Investment': initial_investment,
                    'Total Return': total_return,
                    'Return %': return_percentage,
                    'Share %': get_ownership_percentage(user_info['username']) * 100
                })
        
        # Sort by portfolio value descending
        user_data.sort(key=lambda x: x['Portfolio Value'], reverse=True)
        
        # Create DataFrame
        df = pd.DataFrame(user_data)
        
        # Format for display
        formatted_df = df.copy()
        formatted_df['Units'] = formatted_df['Units'].apply(lambda x: f"{x:,.2f}")
        formatted_df['Portfolio Value'] = formatted_df['Portfolio Value'].apply(lambda x: format_currency(x, lang))
        formatted_df['Initial Investment'] = formatted_df['Initial Investment'].apply(lambda x: format_currency(x, lang))
        formatted_df['Total Return'] = formatted_df['Total Return'].apply(lambda x: format_currency_change(x, lang))
        formatted_df['Return %'] = formatted_df['Return %'].apply(lambda x: f"{x:+.1f}%")
        formatted_df['Share %'] = formatted_df['Share %'].apply(lambda x: f"{x:.1f}%")
        
        # Style the dataframe
        def color_returns(val):
            if '+' in str(val):
                return 'color: green'
            elif '-' in str(val):
                return 'color: red'
            else:
                return 'color: gray'
        
        styled_df = formatted_df.style.map(color_returns, subset=['Total Return', 'Return %'])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_users = len(user_data)
            st.metric("Active Users", total_users)
        
        with col2:
            total_invested = sum([u['Initial Investment'] for u in user_data])
            st.metric("Total Invested", format_currency(total_invested, lang))
        
        with col3:
            current_total = sum([u['Portfolio Value'] for u in user_data])
            st.metric(
                "Current Total",
                format_currency(current_total, lang),
                f"Unit price {format_currency(float(current_unit_price), lang)}",
            )

    def show_admin_aum_chart(self, stocks_with_prices: List[Dict], lang: str):
        """Show exact current AUM decomposed against the confirmed capital ledger."""
        from config import USERS

        total_aum = self.price_fetcher.get_portfolio_value(stocks_with_prices)
        capital_events = get_confirmed_portfolio_capital_events(USERS)
        confirmed_capital = sum(event["amount_eur"] for event in capital_events)
        earnings = total_aum - confirmed_capital
        earnings_pct = earnings / confirmed_capital * 100 if confirmed_capital else 0.0

        st.subheader(get_text("aum_decomposition", lang))
        st.caption(get_text("aum_decomposition_description", lang))

        self._show_metric_grid([
            {
                "label": get_text("assets_under_management", lang),
                "value": format_currency(total_aum, lang),
            },
            {
                "label": get_text("confirmed_net_payins", lang),
                "value": format_currency(confirmed_capital, lang),
            },
            {
                "label": get_text("earnings_residual", lang),
                "value": format_currency_change(earnings, lang),
                "delta": f"{earnings_pct:+.1f}%" if confirmed_capital else None,
            },
        ])

        bridge = go.Figure(go.Waterfall(
            orientation="v",
            measure=["relative", "relative", "total"],
            x=[
                get_text("confirmed_net_payins", lang),
                get_text("earnings_residual", lang),
                get_text("assets_under_management", lang),
            ],
            y=[confirmed_capital, earnings, 0],
            text=[
                format_currency(confirmed_capital, lang),
                format_currency_change(earnings, lang),
                format_currency(total_aum, lang),
            ],
            textposition="outside",
            connector=dict(line=dict(color="#9aa59d", width=1.5, dash="dot")),
            increasing=dict(marker=dict(color="#176b4d")),
            decreasing=dict(marker=dict(color="#b42318")),
            totals=dict(marker=dict(color="#294b43")),
            hovertemplate="%{x}<br>EUR %{y:,.2f}<extra></extra>",
        ))
        bridge.update_layout(
            title=get_text("aum_bridge_title", lang),
            yaxis_title="EUR",
            height=430,
            showlegend=False,
        )
        self._plotly_chart(bridge, key="admin_aum_bridge")

        capital_series = build_confirmed_capital_series(USERS, ASSET_SNAPSHOT_DATE)
        if not capital_series.empty:
            capital_chart = go.Figure()
            capital_chart.add_trace(go.Scatter(
                x=capital_series["Date"],
                y=capital_series["Cumulative Pay-ins"],
                mode="lines",
                name=get_text("confirmed_net_payins", lang),
                line=dict(color="#54706a", width=3, shape="hv"),
                fill="tozeroy",
                fillcolor="rgba(84, 112, 106, 0.14)",
                hovertemplate="%{x|%b %Y}<br>EUR %{y:,.2f}<extra></extra>",
            ))
            current_date = pd.Timestamp(ASSET_SNAPSHOT_DATE)
            capital_chart.add_trace(go.Scatter(
                x=[current_date],
                y=[total_aum],
                mode="markers",
                name=get_text("current_aum", lang),
                marker=dict(color="#176b4d", size=14, symbol="diamond"),
                hovertemplate="%{x|%d %b %Y}<br>EUR %{y:,.2f}<extra></extra>",
            ))
            capital_chart.add_trace(go.Scatter(
                x=[current_date, current_date],
                y=[confirmed_capital, total_aum],
                mode="lines",
                name=get_text("earnings_residual", lang),
                line=dict(color="#a6782d", width=3, dash="dot"),
                hoverinfo="skip",
            ))
            capital_chart.update_layout(
                title=get_text("capital_timeline_title", lang),
                xaxis_title=get_text("date", lang),
                yaxis_title="EUR",
                height=430,
                hovermode="x unified",
            )
            self._plotly_chart(capital_chart, key="admin_capital_timeline")

        st.info(get_text("aum_history_limit", lang))

    def show_tax_overview(
        self,
        stocks_with_prices: List[Dict],
        user: Dict,
        lang: str,
    ):
        """Show a simple, explicitly caveated tax and liquidation simulation."""
        from config import USERS

        st.subheader(get_text("tax_overview", lang))
        st.caption(get_text("tax_overview_description", lang))

        tax_model = st.radio(
            get_text("tax_model", lang),
            options=["capital_gains", "capital_gains_soli"],
            format_func=lambda model: get_text(
                "tax_model_25" if model == "capital_gains" else "tax_model_26375",
                lang,
            ),
            horizontal=True,
            key=f"tax_model_{user['username']}",
        )
        tax_rate = 0.25 if tax_model == "capital_gains" else 0.26375

        total_simulation = calculate_tax_simulation(
            stocks_with_prices,
            user_percentage=1.0,
            tax_rate=tax_rate,
            invested_capital_eur=get_confirmed_user_investment("user", USERS),
        )
        owner_inputs = {}
        for owner in USERS:
            if owner["username"] == "user":
                continue
            owner_investment = get_confirmed_user_investment(owner["username"], USERS)
            owner_preview = calculate_tax_simulation(
                stocks_with_prices,
                user_percentage=get_ownership_percentage(owner["username"]),
                tax_rate=tax_rate,
                invested_capital_eur=owner_investment,
            )
            owner_inputs[owner["username"]] = {
                "investment": owner_investment,
                "earnings": owner_preview["economic_gain_eur"],
            }
        earnings_by_owner = {
            username: inputs["earnings"]
            for username, inputs in owner_inputs.items()
        }
        payable_pooled_tax = cap_pooled_tax_to_economic_gains(
            total_simulation["estimated_tax_eur"],
            sum(earnings_by_owner.values()),
            tax_rate,
        )
        owner_tax_allocations = allocate_tax_by_earnings(
            payable_pooled_tax,
            earnings_by_owner,
        )

        invested_capital = get_confirmed_user_investment(user["username"], USERS)
        allocated_tax = (
            payable_pooled_tax
            if user["username"] == "user"
            else owner_tax_allocations[user["username"]]
        )
        simulation = calculate_tax_simulation(
            stocks_with_prices,
            user_percentage=_user_percentage(user),
            tax_rate=tax_rate,
            invested_capital_eur=invested_capital,
            allocated_tax_eur=allocated_tax,
        )

        self._show_metric_grid([
            {
                "label": get_text("gross_asset_value", lang),
                "value": format_currency(simulation["gross_value_eur"], lang),
            },
            {
                "label": get_text("confirmed_investment", lang),
                "value": format_currency(simulation["invested_capital_eur"], lang),
            },
            {
                "label": get_text("gain_over_investment", lang),
                "value": format_currency_change(simulation["economic_gain_eur"], lang),
            },
            {
                "label": get_text("estimated_tax", lang),
                "value": format_currency_change(-simulation["estimated_tax_eur"], lang),
                "delta": get_text(
                    "tax_share_of_gain",
                    lang,
                    simulation["effective_tax_burden"] * 100,
                ) if simulation["economic_gain_eur"] else None,
            },
            {
                "label": get_text("net_liquidation_value", lang),
                "value": format_currency(simulation["net_liquidation_value_eur"], lang),
            },
            {
                "label": get_text("tax_equivalent_value", lang),
                "value": format_currency(simulation["tax_equivalent_value_eur"], lang),
            },
        ])

        comparison = go.Figure(go.Bar(
            x=[
                get_text("gross_asset_value", lang),
                get_text("net_liquidation_value", lang),
                get_text("tax_equivalent_short", lang),
            ],
            y=[
                simulation["gross_value_eur"],
                simulation["net_liquidation_value_eur"],
                simulation["tax_equivalent_value_eur"],
            ],
            marker_color=["#54706a", "#176b4d", "#a6782d"],
            text=[
                format_currency(simulation["gross_value_eur"], lang),
                format_currency(simulation["net_liquidation_value_eur"], lang),
                format_currency(simulation["tax_equivalent_value_eur"], lang),
            ],
            textposition="outside",
            hovertemplate="%{x}<br>EUR %{y:,.2f}<extra></extra>",
        ))
        comparison.update_layout(
            title=get_text("tax_value_comparison", lang),
            yaxis_title="EUR",
            height=430,
            showlegend=False,
        )
        self._plotly_chart(
            comparison,
            key=f"tax_value_comparison_{user['username']}_{tax_model}",
        )

        if user["username"] == "user":
            owner_rows = []
            for owner in USERS:
                if owner["username"] == "user":
                    continue
                owner_simulation = calculate_tax_simulation(
                    stocks_with_prices,
                    user_percentage=get_ownership_percentage(owner["username"]),
                    tax_rate=tax_rate,
                    invested_capital_eur=get_confirmed_user_investment(
                        owner["username"],
                        USERS,
                    ),
                    allocated_tax_eur=owner_tax_allocations[owner["username"]],
                )
                owner_rows.append({
                    get_text("username", lang): format_user_display_name(owner["username"]),
                    get_text("gross_asset_value", lang): owner_simulation["gross_value_eur"],
                    get_text("confirmed_investment", lang): owner_simulation["invested_capital_eur"],
                    get_text("gain_over_investment", lang): owner_simulation["economic_gain_eur"],
                    get_text("estimated_tax", lang): owner_simulation["estimated_tax_eur"],
                    get_text("net_liquidation_value", lang): owner_simulation["net_liquidation_value_eur"],
                    get_text("tax_equivalent_short", lang): owner_simulation["tax_equivalent_value_eur"],
                })

            owner_tax_frame = pd.DataFrame(owner_rows)
            currency_columns = list(owner_tax_frame.columns[1:])
            formatted_tax_frame = owner_tax_frame.copy()
            for column in currency_columns:
                formatted_tax_frame[column] = formatted_tax_frame[column].apply(
                    lambda value: format_currency(value, lang)
                )
            st.dataframe(
                formatted_tax_frame,
                use_container_width=True,
                hide_index=True,
            )

    def show_portfolio_heatmap(
        self,
        stocks_with_prices: List[Dict],
        user: Dict,
        lang: str,
    ):
        """Show a Finviz-style map of the user's actual portfolio positions."""
        st.subheader(get_text("portfolio_heatmap", lang))
        st.caption(get_text("portfolio_heatmap_description", lang))

        control_col, cash_col = st.columns([2, 1])
        with control_col:
            color_mode = st.radio(
                get_text("heatmap_color_by", lang),
                options=["daily", "since_purchase"],
                format_func=lambda mode: get_text(
                    "heatmap_daily" if mode == "daily" else "heatmap_since_purchase",
                    lang,
                ),
                horizontal=True,
                key=f"portfolio_heatmap_color_{user['username']}",
            )
        with cash_col:
            include_cash = st.checkbox(
                get_text("heatmap_include_cash", lang),
                value=True,
                key=f"portfolio_heatmap_cash_{user['username']}",
            )

        rows = build_portfolio_heatmap_rows(
            stocks_with_prices,
            user_percentage=_user_percentage(user),
            include_cash=include_cash,
            color_mode=color_mode,
        )
        if not rows:
            st.info(get_text("heatmap_no_positions", lang))
            return

        group_rows = {}
        for row in rows:
            translated_industry = get_text(row["industry"], lang)
            group = group_rows.setdefault(
                translated_industry,
                {"value_eur": 0.0, "weighted_return": 0.0},
            )
            group["value_eur"] += row["value_eur"]
            group["weighted_return"] += row["value_eur"] * row["performance_pct"]

        total_value = sum(row["value_eur"] for row in rows)
        portfolio_return = (
            sum(row["value_eur"] * row["performance_pct"] for row in rows)
            / total_value
        )

        ids = ["portfolio"]
        labels = [get_text("portfolio", lang)]
        parents = [""]
        values = [total_value]
        colors = [portfolio_return]
        names = [get_text("portfolio", lang)]

        for industry, group in sorted(group_rows.items()):
            industry_id = f"industry::{industry}"
            ids.append(industry_id)
            labels.append(industry)
            parents.append("portfolio")
            values.append(group["value_eur"])
            colors.append(group["weighted_return"] / group["value_eur"])
            names.append(industry)

        for row in sorted(rows, key=lambda item: item["value_eur"], reverse=True):
            translated_industry = get_text(row["industry"], lang)
            ids.append(f"position::{row['key']}")
            labels.append(row["symbol"])
            parents.append(f"industry::{translated_industry}")
            values.append(row["value_eur"])
            colors.append(row["performance_pct"])
            names.append(row["name"])

        color_bound = max(3.0, min(25.0, max(abs(value) for value in colors)))
        return_label = get_text(
            "heatmap_daily" if color_mode == "daily" else "heatmap_since_purchase",
            lang,
        )
        fig = go.Figure(go.Treemap(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            marker=dict(
                colors=colors,
                colorscale=[
                    [0.00, "#991b1b"],
                    [0.30, "#dc4c4c"],
                    [0.50, "#52615a"],
                    [0.70, "#2f9469"],
                    [1.00, "#087443"],
                ],
                cmin=-color_bound,
                cmax=color_bound,
                line=dict(color="#f6f8fb", width=2),
                colorbar=dict(
                    title=f"{return_label} (%)",
                    ticksuffix="%",
                    tickformat=".2f",
                    thickness=14,
                    len=0.72,
                ),
            ),
            customdata=list(zip(names, colors)),
            texttemplate="<b>%{label}</b><br>%{customdata[1]:+.2f}%",
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                + get_text("your_value", lang)
                + ": EUR %{value:,.2f}<br>"
                + return_label
                + ": %{customdata[1]:+.2f}%<extra></extra>"
            ),
            textfont=dict(color="#ffffff", size=15),
            tiling=dict(packing="squarify", pad=2),
            pathbar=dict(visible=True),
            root=dict(color="#52615a"),
        ))
        fig.update_layout(
            height=650,
            margin=dict(l=8, r=8, t=12, b=8),
            uniformtext=dict(minsize=10, mode="hide"),
        )
        self._plotly_chart(
            fig,
            key=f"portfolio_heatmap_{user['username']}_{color_mode}_{include_cash}",
        )
    
    def show_historical_performance_chart(self, user: Dict, lang: str):
        """Show historical portfolio performance vs the MSCI World holding."""
        
        st.subheader(get_text('historical_performance', lang))
        
        # Add controls for timeframe and granularity
        col1, col2 = st.columns(2)
        
        with col1:
            timeframe_options = {
                '1w': get_text('period_1w', lang),
                '1m': get_text('period_1m', lang),
                '3m': get_text('period_3m', lang),
                '6m': get_text('period_6m', lang),
                '1y': get_text('period_1y', lang)
            }
            selected_timeframe = st.selectbox(
                get_text('timeframe', lang),
                options=list(timeframe_options.keys()),
                format_func=lambda x: timeframe_options[x],
                index=4  # Default to 1y
            )
        
        with col2:
            granularity_options = {
                'daily': get_text('daily', lang),
                'weekly': get_text('weekly', lang),
                'monthly': get_text('monthly', lang)
            }
            selected_granularity = st.selectbox(
                get_text('granularity', lang),
                options=list(granularity_options.keys()),
                format_func=lambda x: granularity_options[x],
                index=2  # Default to monthly
            )
        
        # Create containers for dynamic updates
        chart_container = st.empty()
        progress_container = st.empty()
        metrics_container = st.empty()
        
        # Calculate date range based on selected timeframe
        from datetime import datetime, timedelta
        end_date = datetime.now()
        
        timeframe_days = {
            '1w': 7,
            '1m': 30,
            '3m': 90,
            '6m': 180,
            '1y': 365
        }
        
        start_date = end_date - timedelta(days=timeframe_days[selected_timeframe])
        
        # Create sample dates based on granularity
        sample_dates = []
        current_date = start_date
        
        if selected_granularity == 'daily':
            interval_days = 1
        elif selected_granularity == 'weekly':
            interval_days = 7
        else:  # monthly
            interval_days = 30
            
        while current_date <= end_date:
            sample_dates.append(current_date)
            current_date += timedelta(days=interval_days)
        
        # Initialize chart with all values at 100
        initial_portfolio_values = [100] * len(sample_dates)
        initial_urth_values = [100] * len(sample_dates)
        
        # Create initial chart
        fig = go.Figure()
        
        portfolio_trace = fig.add_trace(go.Scatter(
            x=sample_dates,
            y=initial_portfolio_values,
            mode='lines',
            name='Your Portfolio',
            line=dict(color='#1f77b4', width=3),
            hovertemplate="%{x|%d %b %Y}<br>%{y:.2f}<extra></extra>",
        ))
        
        urth_trace = fig.add_trace(go.Scatter(
            x=sample_dates,
            y=initial_urth_values,
            mode='lines',
            name=f'{BENCHMARK_LABEL} Benchmark',
            line=dict(color='#ff7f0e', width=2, dash='dash'),
            hovertemplate="%{x|%d %b %Y}<br>%{y:.2f}<extra></extra>",
        ))
        
        # Add baseline at 100
        fig.add_hline(
            y=100, 
            line_dash="dot", 
            line_color="gray", 
            opacity=0.5,
            annotation_text="Baseline (100)"
        )
        
        # Customize layout
        fig.update_layout(
            title=get_text('portfolio_vs_benchmark', lang),
            xaxis_title="Date",
            yaxis_title=get_text('relative_performance', lang),
            yaxis_tickformat=".2f",
            height=400,
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left", 
                x=0.01
            )
        )
        
        # Initialize arrays for progressive loading
        portfolio_values = [100] * len(sample_dates)
        urth_values = [100] * len(sample_dates)
        
        # Progressive data loading
        total_points = len(sample_dates)
        
        with progress_container.container():
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        history_by_symbol = self._get_history_for_dates(sample_dates)

        # Load data for each date
        for i, date in enumerate(sample_dates):
            # Format date display based on granularity
            if selected_granularity == 'daily':
                date_str = date.strftime('%Y-%m-%d')
            elif selected_granularity == 'weekly':
                date_str = date.strftime('%Y-W%U')
            else:  # monthly
                date_str = date.strftime('%B %Y')
                
            status_text.text(f"Loading data for {date_str}... ({i+1}/{total_points})")
            
            # Get real data for this date
            portfolio_value, urth_value = self._get_single_date_data(date, user, history_by_symbol)
            
            # Store the actual values
            if i == 0:
                # First point establishes the base
                portfolio_base = portfolio_value
                urth_base = urth_value
                portfolio_values[i] = 100
                urth_values[i] = 100
            else:
                # Calculate relative values
                portfolio_values[i] = (portfolio_value / portfolio_base) * 100 if portfolio_base > 0 else 100
                urth_values[i] = (urth_value / urth_base) * 100 if urth_base > 0 else 100
            
            # Update progress
            progress_bar.progress((i + 1) / total_points)
        
        # Final update with complete data
        fig.data[0].y = portfolio_values
        fig.data[1].y = urth_values
        
        with chart_container.container():
            self._plotly_chart(fig, key="historical_chart_final")
        
        # Clear progress indicators
        progress_container.empty()
        
        # Show final metrics
        if len(portfolio_values) > 1:
            portfolio_change = portfolio_values[-1] - 100
            urth_change = urth_values[-1] - 100
            
            with metrics_container.container():
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Your Performance", 
                        f"{portfolio_values[-1]:.2f}",
                        f"{portfolio_change:+.2f}"
                    )
                
                with col2:
                    st.metric(
                        f"{BENCHMARK_LABEL} Performance",
                        f"{urth_values[-1]:.2f}",
                        f"{urth_change:+.2f}"
                    )
                
                with col3:
                    outperformance = portfolio_change - urth_change
                    st.metric(
                        "Outperformance",
                        f"{outperformance:+.2f}",
                        delta_color="normal" if outperformance >= 0 else "inverse"
                    )
    
    def _get_history_for_dates(self, dates):
        """Fetch each stock's historical window once for a whole chart."""
        from datetime import timedelta

        if not dates:
            return {}

        start_date = min(dates) - timedelta(days=5)
        end_date = max(dates) + timedelta(days=5)

        histories = {}
        for stock in STOCKS:
            if stock.get('symbol') == 'CASH':
                continue
            histories[_stock_key(stock)] = fetch_stock_history_eur(
                stock,
                start=start_date,
                end=end_date,
            )
        return histories

    def _get_price_from_history_window(self, hist, start_date, end_date):
        """Use the last close in a date window, matching the previous lookup behavior."""
        if hist is None or hist.empty:
            return None

        window = hist.copy()
        window.index = pd.to_datetime(window.index).tz_localize(None)
        start_ts = pd.Timestamp(start_date).tz_localize(None)
        end_ts = pd.Timestamp(end_date).tz_localize(None)
        window = window[(window.index >= start_ts) & (window.index < end_ts)]
        if window.empty:
            return None

        return float(window['Close'].iloc[-1])

    def _get_single_date_data(self, date, user, history_by_symbol=None):
        """Get portfolio and benchmark values for a single date, all in EUR."""
        try:
            from datetime import timedelta
            
            total_portfolio_value = 0
            urth_price = None
            
            # Get data for each stock on this date
            for stock in STOCKS:
                if stock.get('symbol') == 'CASH':
                    total_portfolio_value += stock['quantity'] * 1.0
                    continue
                
                try:
                    start_date = date - timedelta(days=5)
                    end_date = date + timedelta(days=5)

                    if history_by_symbol is not None:
                        hist = history_by_symbol.get(_stock_key(stock))
                    else:
                        hist = fetch_stock_history_eur(stock, start=start_date, end=end_date)

                    price = self._get_price_from_history_window(hist, start_date, end_date)
                    if price is None:
                        price = stock['price']
                    
                    if _is_benchmark(stock):
                        urth_price = price
                    
                    total_portfolio_value += stock['quantity'] * price
                    
                except:
                    # Use default price if error
                    price = stock['price']
                    if _is_benchmark(stock):
                        urth_price = price
                    total_portfolio_value += stock['quantity'] * price
            
            # Calculate user's portfolio value
            user_portfolio_value = get_user_portfolio_value(user['username'], total_portfolio_value)
            
            # If no benchmark price was available, use its EUR snapshot price.
            if urth_price is None:
                urth_price = next((s['price'] for s in STOCKS if _is_benchmark(s)), 100)
            
            return user_portfolio_value, urth_price
            
        except Exception as e:
            # Return default values on error
            default_portfolio = get_user_portfolio_value(
                user['username'],
                sum(s['quantity'] * s['price'] for s in STOCKS),
            )
            default_urth = next((s['price'] for s in STOCKS if _is_benchmark(s)), 100)
            return default_portfolio, default_urth
    
    def show_individual_stock_performance_chart(self, user: Dict, lang: str):
        """Show yearly performance graph for each individual stock in the portfolio"""
        # Note: user parameter kept for consistency with other chart methods

        st.subheader(get_text('individual_stock_performance', lang))

        # We can reuse the historical data that was already loaded for the portfolio performance
        # Get 1-year data for all stocks
        from datetime import datetime, timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        # Create a progress indicator
        progress_text = st.empty()
        progress_bar = st.progress(0)

        # Get all non-cash stocks
        non_cash_stocks = [s for s in STOCKS if s.get('symbol') != 'CASH']
        total_stocks = len(non_cash_stocks)

        # Collect data for all stocks
        all_stock_data = []

        for idx, stock in enumerate(non_cash_stocks):
            display_symbol = _display_symbol(stock)
            progress_text.text(f"Loading data for {display_symbol}... ({idx + 1}/{total_stocks})")
            progress_bar.progress((idx + 1) / total_stocks)

            try:
                hist = fetch_stock_history_eur(stock, start=start_date, end=end_date)

                if not hist.empty and len(hist) > 1:
                    # Normalize to percentage change from start
                    base_price = get_return_base_price_eur(stock, hist)
                    dates = hist.index.tolist()
                    normalized_values = [((float(price) - base_price) / base_price * 100) for price in hist['Close']]

                    all_stock_data.append({
                        'symbol': display_symbol,
                        'name': stock['name'],
                        'dates': dates,
                        'values': normalized_values
                    })
            except Exception:
                # Skip stocks that fail to load
                continue

        # Clear progress indicators
        progress_text.empty()
        progress_bar.empty()

        # Create the chart with all stocks
        if all_stock_data:
            fig = go.Figure()

            for stock_data in all_stock_data:
                fig.add_trace(go.Scatter(
                    x=stock_data['dates'],
                    y=stock_data['values'],
                    mode='lines',
                    name=stock_data['symbol'],
                    hovertemplate=f"<b>{stock_data['symbol']}</b><br>" +
                                  "Date: %{x}<br>" +
                                  "Return: %{y:.2f}%<extra></extra>"
                ))

            # Add baseline at 0
            fig.add_hline(
                y=0,
                line_dash="dot",
                line_color="gray",
                opacity=0.5,
                annotation_text="Baseline (0%)"
            )

            # Customize layout
            fig.update_layout(
                title=get_text('yearly_stock_performance', lang),
                xaxis_title="Date",
                yaxis_title=get_text('return_percentage', lang),
                yaxis_tickformat=".2f",
                height=500,
                hovermode='x unified',
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="right",
                    x=0.99
                )
            )

            self._plotly_chart(fig)

            # Summary stats
            col1, col2, col3 = st.columns(3)

            # Calculate final returns for each stock
            final_returns = [(s['symbol'], s['values'][-1]) for s in all_stock_data]
            final_returns.sort(key=lambda x: x[1], reverse=True)

            with col1:
                if final_returns:
                    best_stock, best_return = final_returns[0]
                    st.metric(
                        get_text('best_performer', lang),
                        best_stock,
                        f"{best_return:+.2f}%"
                    )

            with col2:
                if final_returns:
                    worst_stock, worst_return = final_returns[-1]
                    st.metric(
                        get_text('worst_performer', lang),
                        worst_stock,
                        f"{worst_return:+.2f}%"
                    )

            with col3:
                avg_return = sum([r[1] for r in final_returns]) / len(final_returns) if final_returns else 0
                st.metric(
                    get_text('average_return', lang),
                    f"{avg_return:+.2f}%"
                )
        else:
            st.warning(get_text('no_yearly_data_available', lang))

    def show_returns_chart(self, user: Dict, lang: str):
        """Show position returns chart with time period selector"""
        # Note: user parameter kept for consistency with other chart methods

        st.subheader(get_text('position_returns', lang))
        
        # Time period selector
        col1, col2 = st.columns([3, 1])
        
        with col2:
            period_options = ['1d', '1w', '1m', '1y']
            period_labels = {
                '1d': get_text('period_1d', lang),
                '1w': get_text('period_1w', lang), 
                '1m': get_text('period_1m', lang),
                '1y': get_text('period_1y', lang)
            }
            
            selected_period = st.selectbox(
                "Period",
                period_options,
                index=3,  # Default to 1y (index 3)
                format_func=lambda x: period_labels[x],
                key="returns_period"
            )
        
        # Fetch historical data for selected period
        with st.spinner(f"Loading {period_labels[selected_period]} data..."):
            historical_stocks = self.price_fetcher.get_historical_data(STOCKS, selected_period)
        
        # Prepare data for chart
        returns_data = []
        for stock in historical_stocks:
            if stock.get('symbol') == 'CASH':  # Skip cash
                continue
                
            change_percentage = stock.get('historical_change', 0)
            
            # Only include positions with meaningful changes or if they have live prices
            if abs(change_percentage) > 0.01 or stock.get('price_source') == 'live':
                # Special color for the portfolio's MSCI World benchmark holding.
                if _is_benchmark(stock):
                    color = '#1f77b4'  # Blue for benchmark
                else:
                    color = '#00AA00' if change_percentage >= 0 else '#FF4444'  # Green/red for others
                
                returns_data.append({
                    'Symbol': _display_symbol(stock),
                    'Name': stock['name'],
                    'Return (%)': change_percentage,
                    'Color': color,
                    'Is_Benchmark': _is_benchmark(stock)
                })
        
        if returns_data:
            # Put the benchmark holding before all other positions.
            urth_data = [x for x in returns_data if x['Is_Benchmark']]
            other_data = [x for x in returns_data if not x['Is_Benchmark']]
            
            # Sort other stocks by return percentage (highest gain to highest loss)
            other_data.sort(key=lambda x: x['Return (%)'], reverse=True)
            
            # Put the benchmark first, then the other positions.
            returns_data = urth_data + other_data
            
            df = pd.DataFrame(returns_data)
            
            # Create the bar chart
            fig = px.bar(
                df,
                x='Symbol',
                y='Return (%)',
                title=f"{get_text('position_returns', lang)} - {period_labels[selected_period]}",
                color='Color',
                color_discrete_map='identity',  # Use the colors as provided
                hover_data={
                    'Name': True,
                    'Return (%)': ':.2f'
                }
            )
            
            # Customize the chart
            fig.update_layout(
                xaxis_title="",
                yaxis_title="Return (%)",
                yaxis_tickformat=".2f",
                showlegend=False,
                height=400,
                xaxis_tickangle=-45
            )
            
            # Add zero line
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            # Add the MSCI World benchmark line.
            urth_return = next((item['Return (%)'] for item in returns_data if item['Is_Benchmark']), None)
            if urth_return is not None:
                fig.add_hline(
                    y=urth_return, 
                    line_dash="dot", 
                    line_color="#1f77b4", 
                    opacity=0.7,
                    annotation_text=f"{BENCHMARK_LABEL} Benchmark: {urth_return:.2f}%",
                    annotation_position="top right"
                )
            
            self._plotly_chart(fig)
            
            # Summary stats
            winners = len([x for x in returns_data if x['Return (%)'] > 0])
            losers = len([x for x in returns_data if x['Return (%)'] < 0])
            unchanged = len([x for x in returns_data if x['Return (%)'] == 0])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Gainers", winners, delta=None)
            with col2:
                st.metric("Losers", losers, delta=None)  
            with col3:
                st.metric("Unchanged", unchanged, delta=None)
        else:
            st.info(f"No {period_labels[selected_period].lower()} data available (all using default prices)")
    
    def show_portfolio_breakdown(self, stocks: List[Dict], user: Dict, lang: str):
        """Show portfolio breakdown charts"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(get_text('portfolio_allocation', lang))
            
            # Prepare data for pie chart
            chart_data = []
            for stock in stocks:
                value = self.price_fetcher.get_stock_value(stock) * _user_percentage(user)
                if value > 0:  # Only show non-zero values
                    chart_data.append({
                        'Symbol': _display_symbol(stock),
                        'Name': stock['name'],
                        'Value': value,
                        'Industry': stock.get('industry', 'Other')
                    })
            
            df = pd.DataFrame(chart_data)
            
            if not df.empty:
                fig = px.pie(
                    df, 
                    values='Value', 
                    names='Symbol',
                    hover_data=['Name', 'Industry'],
                    title=get_text('holdings_distribution', lang)
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                self._plotly_chart(fig)
    
    def _show_all_users_tranches(self, stocks_with_prices: List[Dict], lang: str):
        """Show tranche-level performance for every user in a single table (admin overview)"""
        from datetime import datetime
        from config import USERS

        total_portfolio_value = self.price_fetcher.get_portfolio_value(stocks_with_prices)
        today = datetime.now()

        tranche_rows = []
        total_invested = 0
        total_current_value = 0

        for user_config in USERS:
            # Skip the aggregate "user" entry to focus on actual participants
            if user_config['username'] == 'user':
                continue

            user_tranches = []

            if 'payments' in user_config:
                for payment in user_config['payments']:
                    user_tranches.append({
                        'date': payment['date'],
                        'amount': payment['amount'],
                        'type': payment.get('type', get_text('additional_payment', lang))
                    })
            elif 'paid_date' in user_config:
                user_tranches.append({
                    'date': user_config['paid_date'],
                    'amount': user_config.get('initial_investment', 0),
                    'type': get_text('initial_investment', lang)
                })

            for tranche in user_tranches:
                investment_date = datetime.strptime(tranche['date'], '%Y-%m-%d')
                amount_invested = tranche['amount']
                total_invested += amount_invested

                days_invested = (today - investment_date).days
                years_invested = days_invested / 365.25

                portfolio_value_at_date = self._get_portfolio_value_at_date(investment_date, stocks_with_prices)
                percentage_bought = amount_invested / portfolio_value_at_date if portfolio_value_at_date > 0 else 0
                tranche_current_value = percentage_bought * total_portfolio_value
                total_current_value += tranche_current_value

                return_amount = tranche_current_value - amount_invested
                return_pct = (return_amount / amount_invested * 100) if amount_invested > 0 else 0
                annualized_return = (((tranche_current_value / amount_invested) ** (1 / years_invested)) - 1) * 100 if years_invested > 0 and amount_invested > 0 else 0

                tranche_rows.append({
                    get_text('username', lang): format_user_display_name(user_config['username']),
                    get_text('investment_date', lang): tranche['date'],
                    get_text('amount_invested', lang): amount_invested,
                    get_text('current_value', lang): tranche_current_value,
                    get_text('return_amount', lang): return_amount,
                    get_text('return_pct', lang): return_pct,
                    get_text('annualized_return', lang): annualized_return,
                    get_text('years_invested', lang): years_invested,
                    'Type': tranche['type'],
                    '_sort_key': (user_config['username'], investment_date)
                })

        if not tranche_rows:
            st.info("No payment information available")
            return

        # Sort by user then date
        tranche_rows.sort(key=lambda x: x['_sort_key'])
        for row in tranche_rows:
            del row['_sort_key']

        df = pd.DataFrame(tranche_rows)

        # Format for display
        formatted_df = df.copy()
        username_col = get_text('username', lang)
        amount_col = get_text('amount_invested', lang)
        current_val_col = get_text('current_value', lang)
        return_amt_col = get_text('return_amount', lang)
        return_pct_col = get_text('return_pct', lang)
        ann_return_col = get_text('annualized_return', lang)
        years_col = get_text('years_invested', lang)

        formatted_df[username_col] = formatted_df[username_col].apply(lambda x: x.title())
        formatted_df[amount_col] = formatted_df[amount_col].apply(lambda x: format_currency(x, lang))
        formatted_df[current_val_col] = formatted_df[current_val_col].apply(lambda x: format_currency(x, lang))
        formatted_df[return_amt_col] = formatted_df[return_amt_col].apply(lambda x: format_currency_change(x, lang))
        formatted_df[return_pct_col] = formatted_df[return_pct_col].apply(lambda x: f"{x:+.2f}%")
        formatted_df[ann_return_col] = formatted_df[ann_return_col].apply(lambda x: f"{x:+.2f}%")
        formatted_df[years_col] = formatted_df[years_col].apply(lambda x: f"{x:.2f}")

        display_df = formatted_df

        def color_returns(val):
            if '+' in str(val):
                return 'color: green'
            elif '-' in str(val):
                return 'color: red'
            else:
                return 'color: gray'

        styled_df = display_df.style.map(
            color_returns,
            subset=[return_amt_col, return_pct_col, ann_return_col]
        )

        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # Verification section - only show if verification fails
        actual_current_value = total_portfolio_value
        difference = total_current_value - actual_current_value

        tolerance = actual_current_value * 0.001
        is_verified = abs(difference) <= tolerance

        if not is_verified:
            st.markdown("---")
            st.subheader(get_text('total_verification', lang))

            verification_cols = st.columns(4)

            with verification_cols[0]:
                st.metric(
                    get_text('sum_of_tranches', lang),
                    format_currency(total_current_value, lang)
                )

            with verification_cols[1]:
                st.metric(
                    get_text('actual_portfolio_value', lang),
                    format_currency(actual_current_value, lang)
                )

            with verification_cols[2]:
                st.metric(
                    get_text('difference', lang),
                    format_currency(difference, lang),
                    delta=None
                )

            with verification_cols[3]:
                st.error(get_text('verification_failed', lang))

        # Show total returns breakdown across all users
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                get_text('amount_invested', lang),
                format_currency(total_invested, lang)
            )

        with col2:
            total_profit = total_current_value - total_invested
            st.metric(
                get_text('return_amount', lang) + " (Total)",
                format_currency_change(total_profit, lang),
                delta=f"{(total_profit / total_invested * 100):+.2f}%" if total_invested > 0 else None
            )

        with col3:
            if total_invested > 0:
                weighted_return = sum([
                    (row[get_text('amount_invested', lang)] / total_invested) * row[get_text('annualized_return', lang)]
                    for row in tranche_rows
                ])
                st.metric(
                    get_text('annualized_return', lang) + " (Avg)",
                    f"{weighted_return:+.2f}%"
                )
    
    def show_holdings_table(self, stocks: List[Dict], user: Dict, lang: str):
        """Show detailed holdings table"""
        
        st.subheader(get_text('detailed_holdings', lang))
        
        # Prepare table data
        table_data = []
        for stock in stocks:
            current_price = stock.get('current_price', stock['price'])
            your_quantity = stock['quantity'] * _user_percentage(user)
            your_value = your_quantity * current_price
            daily_change_pct = self.price_fetcher.get_daily_change_percentage(stock)
            
            industry = stock.get('industry', 'N/A')
            # Translate industry names
            if industry:
                industry = get_text(industry, lang)
            
            table_data.append({
                get_text('symbol', lang): _display_symbol(stock),
                get_text('name', lang): stock['name'],
                get_text('industry', lang): industry,
                get_text('your_quantity', lang): your_quantity,
                get_text('current_price', lang): current_price,
                get_text('your_value', lang): your_value,
                get_text('daily_change', lang): f"{daily_change_pct:+.2f}%",
                get_text('price_source', lang): stock.get('price_source', 'default').title()
            })
        
        df = pd.DataFrame(table_data)
        
        # Sort by value descending
        df = df.sort_values(get_text('your_value', lang), ascending=False)
        
        # Format the dataframe for display
        formatted_df = df.copy()
        your_quantity_col = get_text('your_quantity', lang)
        current_price_col = get_text('current_price', lang)
        your_value_col = get_text('your_value', lang)
        daily_change_col = get_text('daily_change', lang)
        
        formatted_df[your_quantity_col] = formatted_df[your_quantity_col].apply(lambda x: f"{x:.2f}" if x < 1000 else f"{x:,.0f}")
        formatted_df[current_price_col] = formatted_df[current_price_col].apply(lambda x: format_currency(x, lang))
        formatted_df[your_value_col] = formatted_df[your_value_col].apply(lambda x: format_currency(x, lang))
        # Daily change is already formatted
        
        # Style the dataframe
        def color_daily_change(val):
            if '0.00%' in str(val) or 'N/A' in str(val):
                return 'color: gray'
            elif '+' in str(val):
                return 'color: green'
            else:
                return 'color: red'
        
        styled_df = formatted_df.style.map(color_daily_change, subset=[daily_change_col])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_positions = len([s for s in stocks if s['symbol'] != 'CASH'])
            st.metric(get_text('total_positions', lang), total_positions)
        
        with col2:
            cash_value = next((self.price_fetcher.get_stock_value(s) * _user_percentage(user)
                             for s in stocks if s['symbol'] == 'CASH'), 0)
            st.metric(get_text('cash_position', lang), format_currency(cash_value, lang))
        
        with col3:
            live_prices = len([s for s in stocks if s.get('price_source') == 'live'])
            total_non_cash = len([s for s in stocks if s['symbol'] != 'CASH'])
            st.metric(get_text('live_price_coverage', lang), f"{live_prices}/{total_non_cash}")

    def show_investment_tranches(self, user: Dict, stocks_with_prices: List[Dict], lang: str):
        """Show performance breakdown by investment tranche with annualized returns"""
        from datetime import datetime
        from config import USERS

        # Only show tranche details for the aggregate user and foehr and annika
        if user.get('username') not in ('user', 'foehr', 'annika'):
            return

        st.subheader(get_text('investment_tranches', lang))

        # In the aggregated "user" account, show every user's tranches instead of a single total
        if user['username'] == 'user':
            self._show_all_users_tranches(stocks_with_prices, lang)
            return

        # Get current portfolio value
        total_portfolio_value = self.price_fetcher.get_portfolio_value(stocks_with_prices)

        # Get user config to access payment data
        user_config = next((u for u in USERS if u['username'] == user['username']), None)
        if not user_config:
            st.warning("User configuration not found")
            return

        # Prepare tranches list
        tranches = []

        # Check if user has multiple payments or single paid_date
        if 'payments' in user_config:
            # Multiple payments
            for payment in user_config['payments']:
                tranches.append({
                    'date': payment['date'],
                    'amount': payment['amount'],
                    'type': get_text('additional_payment', lang)
                })
        elif 'paid_date' in user_config:
            # Single payment
            tranches.append({
                'date': user_config['paid_date'],
                'amount': user_config.get('initial_investment', 0),
                'type': get_text('initial_investment', lang)
            })

        if not tranches:
            st.info("No payment information available")
            return

        # Calculate current date
        today = datetime.now()

        # Calculate value for each tranche
        tranche_data = []
        total_invested = 0
        total_current_value = 0

        for idx, tranche in enumerate(tranches):
            investment_date = datetime.strptime(tranche['date'], '%Y-%m-%d')
            amount_invested = tranche['amount']
            total_invested += amount_invested

            # Calculate days invested
            days_invested = (today - investment_date).days
            years_invested = days_invested / 365.25

            # Get portfolio value at investment date
            portfolio_value_at_date = self._get_portfolio_value_at_date(investment_date, stocks_with_prices)

            # Calculate the portfolio percentage this investment would have bought
            if portfolio_value_at_date > 0:
                percentage_bought = amount_invested / portfolio_value_at_date
            else:
                percentage_bought = 0

            # Calculate current value of this tranche
            tranche_current_value = percentage_bought * total_portfolio_value
            total_current_value += tranche_current_value

            # Calculate returns
            return_amount = tranche_current_value - amount_invested
            return_pct = (return_amount / amount_invested * 100) if amount_invested > 0 else 0

            # Calculate annualized return
            if years_invested > 0 and amount_invested > 0:
                annualized_return = (((tranche_current_value / amount_invested) ** (1 / years_invested)) - 1) * 100
            else:
                annualized_return = 0

            tranche_data.append({
                get_text('investment_date', lang): tranche['date'],
                get_text('amount_invested', lang): amount_invested,
                get_text('current_value', lang): tranche_current_value,
                get_text('return_amount', lang): return_amount,
                get_text('return_pct', lang): return_pct,
                get_text('annualized_return', lang): annualized_return,
                get_text('days_invested', lang): days_invested,
                get_text('years_invested', lang): years_invested,
                'Type': tranche['type'],
                '_sort_date': investment_date  # For sorting
            })

        # Sort by date
        tranche_data.sort(key=lambda x: x['_sort_date'])

        # Remove sort key before display
        for td in tranche_data:
            del td['_sort_date']

        # Create DataFrame
        df = pd.DataFrame(tranche_data)

        # Format for display
        formatted_df = df.copy()
        amount_col = get_text('amount_invested', lang)
        current_val_col = get_text('current_value', lang)
        return_amt_col = get_text('return_amount', lang)
        return_pct_col = get_text('return_pct', lang)
        ann_return_col = get_text('annualized_return', lang)
        years_col = get_text('years_invested', lang)

        formatted_df[amount_col] = formatted_df[amount_col].apply(lambda x: format_currency(x, lang))
        formatted_df[current_val_col] = formatted_df[current_val_col].apply(lambda x: format_currency(x, lang))
        formatted_df[return_amt_col] = formatted_df[return_amt_col].apply(lambda x: format_currency_change(x, lang))
        formatted_df[return_pct_col] = formatted_df[return_pct_col].apply(lambda x: f"{x:+.2f}%")
        formatted_df[ann_return_col] = formatted_df[ann_return_col].apply(lambda x: f"{x:+.2f}%")
        formatted_df[years_col] = formatted_df[years_col].apply(lambda x: f"{x:.2f}")

        # Hide days_invested column for cleaner display
        display_df = formatted_df.drop(columns=[get_text('days_invested', lang)])

        # Style the dataframe
        def color_returns(val):
            if '+' in str(val):
                return 'color: green'
            elif '-' in str(val):
                return 'color: red'
            else:
                return 'color: gray'

        styled_df = display_df.style.map(
            color_returns,
            subset=[return_amt_col, return_pct_col, ann_return_col]
        )

        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # Verification section - only show if verification fails
        # Calculate actual current value based on current portfolio percentage
        actual_current_value = get_user_portfolio_value(user['username'], total_portfolio_value)
        difference = total_current_value - actual_current_value

        # Check if difference is within acceptable range (0.1%)
        tolerance = actual_current_value * 0.001
        is_verified = abs(difference) <= tolerance

        # Only display verification section if it fails and the user is allowed to see it
        if not is_verified and user.get('username') == 'user':
            st.markdown("---")
            st.subheader(get_text('total_verification', lang))

            verification_cols = st.columns(4)

            with verification_cols[0]:
                st.metric(
                    get_text('sum_of_tranches', lang),
                    format_currency(total_current_value, lang)
                )

            with verification_cols[1]:
                st.metric(
                    get_text('actual_portfolio_value', lang),
                    format_currency(actual_current_value, lang)
                )

            with verification_cols[2]:
                st.metric(
                    get_text('difference', lang),
                    format_currency(difference, lang),
                    delta=None
                )

            with verification_cols[3]:
                st.error(get_text('verification_failed', lang))

        # Show total returns breakdown
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                get_text('amount_invested', lang),
                format_currency(total_invested, lang)
            )

        with col2:
            total_profit = total_current_value - total_invested
            st.metric(
                get_text('return_amount', lang) + " (Total)",
                format_currency_change(total_profit, lang),
                delta=f"{(total_profit / total_invested * 100):+.2f}%" if total_invested > 0 else None
            )

        with col3:
            # Calculate weighted average annualized return
            if total_invested > 0:
                weighted_return = sum([
                    (td[get_text('amount_invested', lang)] / total_invested) * td[get_text('annualized_return', lang)]
                    for td in tranche_data
                ])
                st.metric(
                    get_text('annualized_return', lang) + " (Avg)",
                    f"{weighted_return:+.2f}%"
                )

        # Visualization: Pie chart of tranche contributions
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            # Pie chart by value
            chart_data = []
            for i, tranche in enumerate(tranches):
                investment_date = datetime.strptime(tranche['date'], '%Y-%m-%d')
                amount = tranche_data[i][get_text('current_value', lang)]

                chart_data.append({
                    'Date': tranche['date'],
                    'Value': amount,
                    'Label': f"{tranche['date']}\n{format_currency(tranche['amount'], lang)}"
                })

            chart_df = pd.DataFrame(chart_data)

            if not chart_df.empty:
                fig = px.pie(
                    chart_df,
                    values='Value',
                    names='Date',
                    title=f"{get_text('current_value', lang)} by Tranche"
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                self._plotly_chart(fig)

        with col2:
            # Bar chart of returns
            bar_data = []
            for i, td in enumerate(tranche_data):
                bar_data.append({
                    'Date': tranches[i]['date'],
                    'Return %': td[get_text('return_pct', lang)],
                    'Annualized %': td[get_text('annualized_return', lang)]
                })

            bar_df = pd.DataFrame(bar_data)

            if not bar_df.empty:
                fig = go.Figure()

                fig.add_trace(go.Bar(
                    x=bar_df['Date'],
                    y=bar_df['Return %'],
                    name='Total Return %',
                    marker_color='lightblue',
                    hovertemplate="%{x}<br>%{y:.2f}%<extra></extra>",
                ))

                fig.add_trace(go.Bar(
                    x=bar_df['Date'],
                    y=bar_df['Annualized %'],
                    name='Annualized Return %',
                    marker_color='darkblue',
                    hovertemplate="%{x}<br>%{y:.2f}%<extra></extra>",
                ))

                fig.update_layout(
                    title=f"{get_text('return_pct', lang)} vs {get_text('annualized_return', lang)}",
                    xaxis_title=get_text('investment_date', lang),
                    yaxis_title="Return %",
                    yaxis_tickformat=".2f",
                    barmode='group',
                    height=400
                )

                self._plotly_chart(fig)

    def _get_portfolio_value_at_date(self, date, current_stocks):
        """Get total portfolio value at a specific historical date"""
        from datetime import timedelta

        total_value = 0

        for stock in STOCKS:
            if stock.get('symbol') == 'CASH':
                total_value += stock['quantity'] * 1.0
                continue

            try:
                # Get data around this date (±5 days for buffer)
                start_date = date - timedelta(days=5)
                end_date = date + timedelta(days=5)
                hist = fetch_stock_history_eur(stock, start=start_date, end=end_date)
                price = self._get_price_from_history_window(hist, start_date, end_date)
                if price is None:
                    price = stock['price']

                total_value += stock['quantity'] * price

            except:
                # Use default price if error
                total_value += stock['quantity'] * stock['price']

        return total_value

    def _calculate_tranche_returns(self, user, total_portfolio_value):
        """Calculate returns based on payment tranches"""
        from datetime import datetime
        from config import USERS

        # Get user config to access payment data
        user_config = next((u for u in USERS if u['username'] == user['username']), None)
        if not user_config:
            return 0, 0, 0

        # Prepare tranches list
        tranches = []

        # Check if user has multiple payments or single paid_date
        if 'payments' in user_config:
            # Multiple payments
            for payment in user_config['payments']:
                tranches.append({
                    'date': payment['date'],
                    'amount': payment['amount']
                })
        elif 'paid_date' in user_config:
            # Single payment
            tranches.append({
                'date': user_config['paid_date'],
                'amount': user_config.get('initial_investment', 0)
            })

        if not tranches:
            return 0, 0, 0

        # Sum up total amount invested from all tranches
        total_invested = sum(t['amount'] for t in tranches)

        # Current value is based on the user's actual portfolio percentage
        current_value = get_user_portfolio_value(user['username'], total_portfolio_value)

        # Calculate returns: current value minus what was invested
        total_return_amount = current_value - total_invested
        total_return_percentage = (total_return_amount / total_invested * 100) if total_invested > 0 else 0

        return total_invested, total_return_amount, total_return_percentage

    def show_login_statistics(self, lang: str):
        """Show login statistics (admin only)"""
        from login_tracker import login_tracker
        from datetime import datetime
        import pandas as pd

        st.subheader(get_text('admin_login_stats', lang))

        # Check if tracking is enabled
        if not login_tracker.enabled:
            st.info(get_text('tracking_not_enabled', lang))
            return

        # Get login data
        records = login_tracker.get_login_stats()

        if not records:
            st.info(get_text('no_login_data', lang))
            return

        # Convert to DataFrame
        df = pd.DataFrame(records)

        # Summary metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            total_logins = len(df)
            st.metric(get_text('total_logins', lang), total_logins)

        with col2:
            unique_users = df['Username'].nunique()
            st.metric(get_text('unique_users', lang), unique_users)

        with col3:
            if not df.empty:
                most_active = df['Username'].value_counts().index[0]
                login_count = df['Username'].value_counts().iloc[0]
                st.metric(
                    get_text('most_active_user', lang),
                    most_active.title(),
                    f"{login_count} logins"
                )

        st.markdown("---")

        # Recent logins table
        st.markdown(f"### {get_text('recent_logins', lang)}")

        # Sort by timestamp descending and show last 10
        df_sorted = df.sort_values('Timestamp', ascending=False).head(10)

        # Format for display
        display_df = df_sorted[['Timestamp', 'Username']].copy()
        display_df['Username'] = display_df['Username'].str.title()

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Visualizations
        col1, col2 = st.columns(2)

        with col1:
            # Bar chart: Logins by user
            st.markdown(f"### {get_text('logins_by_user', lang)}")

            user_counts = df['Username'].value_counts().reset_index()
            user_counts.columns = ['Username', 'Count']
            user_counts['Username'] = user_counts['Username'].str.title()

            fig = px.bar(
                user_counts,
                x='Username',
                y='Count',
                title=get_text('logins_by_user', lang)
            )
            fig.update_layout(xaxis_tickangle=-45, height=400)
            self._plotly_chart(fig)

        with col2:
            # Line chart: Logins over time
            st.markdown(f"### {get_text('logins_over_time', lang)}")

            # Parse timestamps and group by date
            df['Date'] = pd.to_datetime(df['Timestamp'], format='%Y-%m-%d %H:%M:%S').dt.date
            daily_logins = df.groupby('Date').size().reset_index(name='Logins')

            fig = px.line(
                daily_logins,
                x='Date',
                y='Logins',
                title=get_text('logins_over_time', lang),
                markers=True
            )
            fig.update_layout(height=400)
            self._plotly_chart(fig)
