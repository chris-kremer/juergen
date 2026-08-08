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
from price_fetcher import PriceFetcher, fetch_yfinance_history
from config import STOCKS
from translations import get_language, get_text, format_currency, format_currency_change
from celebration import (
    build_annika_2500_celebration_html,
    build_doubling_celebration_html,
    resolve_doubling_celebration_return,
    should_show_annika_2500_celebration,
)
from ui_theme import build_dashboard_header

pio.templates.default = "plotly_white"
px.defaults.template = "plotly_white"

class PortfolioDashboard:
    def __init__(self, price_fetcher: PriceFetcher):
        self.price_fetcher = price_fetcher

    def _plotly_chart(self, fig, **kwargs):
        """Render Plotly charts with the restrained portfolio theme."""
        fig.update_layout(
            template="plotly_white",
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
            color="#68736b",
            gridcolor="#edf0ec",
            zerolinecolor="#c9d0c8",
            linecolor="#c9d0c8",
        )
        fig.update_yaxes(
            color="#68736b",
            gridcolor="#edf0ec",
            zerolinecolor="#c9d0c8",
            linecolor="#c9d0c8",
        )
        st.plotly_chart(fig, use_container_width=True, theme=None, **kwargs)

    def _show_metric_grid(self, metrics: List[Dict]):
        """Render responsive metric cards without Streamlit column truncation."""
        cards = []
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
                delta_html = f'<div class="metric-delta {delta_class}">{prefix}{escape(delta_text)}</div>'

            cards.append(
                f'<div class="metric-card">'
                f'<div class="metric-label">{label}</div>'
                f'<div class="metric-value">{value}</div>'
                f'{delta_html}'
                f'</div>'
            )

        st.markdown(f'<div class="metric-grid">{"".join(cards)}</div>', unsafe_allow_html=True)
    
    def show_dashboard(self, user: Dict, stocks_with_prices: List[Dict], failed_symbols: List[str]):
        """Display the main portfolio dashboard"""
        
        lang = get_language(user['username'])
        preview_requested = bool(
            st.session_state.pop('kremer_doubling_preview_requested', False)
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
        user_portfolio_value = total_portfolio_value * user['portfolio_percentage']

        # Calculate returns from tranches (not from initial_investment field)
        total_invested, total_return_amount, total_return_percentage = self._calculate_tranche_returns(user, total_portfolio_value)

        # Fallback to initial_investment if no tranches configured
        if total_invested == 0:
            initial_investment = user.get('initial_investment', 0)
            total_return_amount = user_portfolio_value - initial_investment
            total_return_percentage = (total_return_amount / initial_investment * 100) if initial_investment > 0 else 0
        
        # Calculate total daily change
        total_daily_change = sum([
            self.price_fetcher.get_user_daily_change_value(stock, user['portfolio_percentage'])
            for stock in stocks_with_prices
        ])
        
        # Calculate daily percentage change
        daily_percentage = (total_daily_change / user_portfolio_value * 100) if user_portfolio_value > 0 else 0
        
        # Calculate top performers for metrics row
        stock_changes = []
        for stock in stocks_with_prices:
            if stock['symbol'] == 'CASH':
                continue
            daily_change_pct = self.price_fetcher.get_daily_change_percentage(stock)
            daily_change_value = self.price_fetcher.get_user_daily_change_value(stock, user['portfolio_percentage'])
            if stock.get('price_source') == 'live':
                stock_changes.append({
                    'symbol': stock['symbol'],
                    'name': stock['name'],
                    'daily_change_pct': daily_change_pct,
                    'daily_change_value': daily_change_value,
                    'current_price': stock.get('current_price', stock['price'])
                })

        live_count = len([s for s in stocks_with_prices if s.get('price_source') == 'live'])
        top_pct_stock = max(stock_changes, key=lambda x: x['daily_change_pct']) if stock_changes else None
        top_value_stock = max(stock_changes, key=lambda x: x['daily_change_value']) if stock_changes else None

        self._show_metric_grid([
            {
                "label": get_text('your_portfolio_value', lang),
                "value": format_currency(user_portfolio_value, lang),
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

        st.markdown("---")

        # Investment tranche performance (moved up for better visibility)
        self.show_investment_tranches(user, stocks_with_prices, lang)

        st.markdown("---")

        # Show user overview if this is the "user" account
        if user['username'] == 'user':
            self.show_all_users_overview(stocks_with_prices, lang)
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

    def show_all_users_overview(self, stocks_with_prices: List[Dict], lang: str):
        """Show overview of all users' portfolio values (only for 'user' account)"""
        from config import USERS
        
        st.subheader(get_text('all_users_overview', lang))
        

        
        # Calculate total portfolio value
        total_portfolio_value = self.price_fetcher.get_portfolio_value(stocks_with_prices)
        
        # Prepare data for all users
        user_data = []
        for user_info in USERS:
            if user_info['username'] != 'user':  # Skip the overview user itself
                user_value = total_portfolio_value * user_info['portfolio_percentage']
                initial_investment = user_info.get('initial_investment', 0)
                total_return = user_value - initial_investment
                return_percentage = (total_return / initial_investment * 100) if initial_investment > 0 else 0
                
                user_data.append({
                    'User': user_info['username'].title(),
                    'Portfolio Value': user_value,
                    'Initial Investment': initial_investment,
                    'Total Return': total_return,
                    'Return %': return_percentage,
                    'Share %': user_info['portfolio_percentage'] * 100
                })
        
        # Sort by portfolio value descending
        user_data.sort(key=lambda x: x['Portfolio Value'], reverse=True)
        
        # Create DataFrame
        df = pd.DataFrame(user_data)
        
        # Format for display
        formatted_df = df.copy()
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
            st.metric("Current Total", format_currency(current_total, lang))
    
    def show_historical_performance_chart(self, user: Dict, lang: str):
        """Show historical portfolio performance vs URTH benchmark with progressive loading"""
        
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
            line=dict(color='#1f77b4', width=3)
        ))
        
        urth_trace = fig.add_trace(go.Scatter(
            x=sample_dates,
            y=initial_urth_values,
            mode='lines',
            name='URTH Benchmark',
            line=dict(color='#ff7f0e', width=2, dash='dash')
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
                        f"{portfolio_values[-1]:.1f}",
                        f"{portfolio_change:+.1f}"
                    )
                
                with col2:
                    st.metric(
                        "URTH Performance", 
                        f"{urth_values[-1]:.1f}",
                        f"{urth_change:+.1f}"
                    )
                
                with col3:
                    outperformance = portfolio_change - urth_change
                    st.metric(
                        "Outperformance",
                        f"{outperformance:+.1f}",
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
            if stock['symbol'] == 'CASH':
                continue
            histories[stock['symbol']] = fetch_yfinance_history(
                stock['symbol'],
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
        """Get portfolio and URTH values for a single date"""
        try:
            from datetime import timedelta
            
            total_portfolio_value = 0
            urth_price = None
            
            # Get data for each stock on this date
            for stock in STOCKS:
                if stock['symbol'] == 'CASH':
                    total_portfolio_value += stock['quantity'] * 1.0
                    continue
                
                try:
                    start_date = date - timedelta(days=5)
                    end_date = date + timedelta(days=5)

                    if history_by_symbol is not None:
                        hist = history_by_symbol.get(stock['symbol'])
                    else:
                        hist = fetch_yfinance_history(stock['symbol'], start=start_date, end=end_date)

                    price = self._get_price_from_history_window(hist, start_date, end_date)
                    if price is None:
                        price = stock['price']
                    
                    if stock['symbol'] == 'URTH':
                        urth_price = price
                    
                    total_portfolio_value += stock['quantity'] * price
                    
                except:
                    # Use default price if error
                    price = stock['price']
                    if stock['symbol'] == 'URTH':
                        urth_price = price
                    total_portfolio_value += stock['quantity'] * price
            
            # Calculate user's portfolio value
            user_portfolio_value = total_portfolio_value * user['portfolio_percentage']
            
            # If no URTH price found, use default
            if urth_price is None:
                urth_price = next((s['price'] for s in STOCKS if s['symbol'] == 'URTH'), 100)
            
            return user_portfolio_value, urth_price
            
        except Exception as e:
            # Return default values on error
            default_portfolio = sum(s['quantity'] * s['price'] for s in STOCKS) * user['portfolio_percentage']
            default_urth = next((s['price'] for s in STOCKS if s['symbol'] == 'URTH'), 100)
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
        non_cash_stocks = [s for s in STOCKS if s['symbol'] != 'CASH']
        total_stocks = len(non_cash_stocks)

        # Collect data for all stocks
        all_stock_data = []

        for idx, stock in enumerate(non_cash_stocks):
            progress_text.text(f"Loading data for {stock['symbol']}... ({idx + 1}/{total_stocks})")
            progress_bar.progress((idx + 1) / total_stocks)

            try:
                hist = fetch_yfinance_history(stock['symbol'], start=start_date, end=end_date)

                if not hist.empty and len(hist) > 1:
                    # Normalize to percentage change from start
                    base_price = float(hist['Close'].iloc[0])
                    dates = hist.index.tolist()
                    normalized_values = [((float(price) - base_price) / base_price * 100) for price in hist['Close']]

                    all_stock_data.append({
                        'symbol': stock['symbol'],
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
            if stock['symbol'] == 'CASH':  # Skip cash
                continue
                
            change_percentage = stock.get('historical_change', 0)
            
            # Only include positions with meaningful changes or if they have live prices
            if abs(change_percentage) > 0.01 or stock.get('price_source') == 'live':
                # Special color for URTH (benchmark)
                if stock['symbol'] == 'URTH':
                    color = '#1f77b4'  # Blue for benchmark
                else:
                    color = '#00AA00' if change_percentage >= 0 else '#FF4444'  # Green/red for others
                
                returns_data.append({
                    'Symbol': stock['symbol'],
                    'Name': stock['name'],
                    'Return (%)': change_percentage,
                    'Color': color,
                    'Is_Benchmark': stock['symbol'] == 'URTH'
                })
        
        if returns_data:
            # Separate URTH (benchmark) from other stocks
            urth_data = [x for x in returns_data if x['Symbol'] == 'URTH']
            other_data = [x for x in returns_data if x['Symbol'] != 'URTH']
            
            # Sort other stocks by return percentage (highest gain to highest loss)
            other_data.sort(key=lambda x: x['Return (%)'], reverse=True)
            
            # Put URTH first, then other stocks
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
                showlegend=False,
                height=400,
                xaxis_tickangle=-45
            )
            
            # Add zero line
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            # Add URTH benchmark line
            urth_return = next((item['Return (%)'] for item in returns_data if item['Symbol'] == 'URTH'), None)
            if urth_return is not None:
                fig.add_hline(
                    y=urth_return, 
                    line_dash="dot", 
                    line_color="#1f77b4", 
                    opacity=0.7,
                    annotation_text=f"URTH Benchmark: {urth_return:.1f}%",
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
                value = self.price_fetcher.get_stock_value(stock) * user['portfolio_percentage']
                if value > 0:  # Only show non-zero values
                    chart_data.append({
                        'Symbol': stock['symbol'],
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
                    get_text('username', lang): user_config['username'].title(),
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
            your_quantity = stock['quantity'] * user['portfolio_percentage']
            your_value = your_quantity * current_price
            daily_change_pct = self.price_fetcher.get_daily_change_percentage(stock)
            
            industry = stock.get('industry', 'N/A')
            # Translate industry names
            if industry:
                industry = get_text(industry, lang)
            
            table_data.append({
                get_text('symbol', lang): stock['symbol'],
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
            cash_value = next((self.price_fetcher.get_stock_value(s) * user['portfolio_percentage'] 
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
        actual_current_value = total_portfolio_value * user['portfolio_percentage']
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
                    marker_color='lightblue'
                ))

                fig.add_trace(go.Bar(
                    x=bar_df['Date'],
                    y=bar_df['Annualized %'],
                    name='Annualized Return %',
                    marker_color='darkblue'
                ))

                fig.update_layout(
                    title=f"{get_text('return_pct', lang)} vs {get_text('annualized_return', lang)}",
                    xaxis_title=get_text('investment_date', lang),
                    yaxis_title="Return %",
                    barmode='group',
                    height=400
                )

                self._plotly_chart(fig)

    def _get_portfolio_value_at_date(self, date, current_stocks):
        """Get total portfolio value at a specific historical date"""
        from datetime import timedelta

        total_value = 0

        for stock in STOCKS:
            if stock['symbol'] == 'CASH':
                total_value += stock['quantity'] * 1.0
                continue

            try:
                # Get data around this date (±5 days for buffer)
                start_date = date - timedelta(days=5)
                end_date = date + timedelta(days=5)
                hist = fetch_yfinance_history(stock['symbol'], start=start_date, end=end_date)
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
        current_value = total_portfolio_value * user['portfolio_percentage']

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
