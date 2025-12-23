"""
Annual PDF report generator for user portfolios.
Creates 2025 performance reports with benchmark comparisons,
monthly position returns, and inflation-adjusted views.
"""

from __future__ import annotations

import io
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import yfinance as yf

from config import STOCKS


# Conservative monthly inflation assumptions for 2025 (approx. 3% annualized)
DEFAULT_2025_INFLATION = {
    1: 0.0025,
    2: 0.0025,
    3: 0.0025,
    4: 0.0025,
    5: 0.0025,
    6: 0.0025,
    7: 0.0025,
    8: 0.0025,
    9: 0.0025,
    10: 0.0025,
    11: 0.0025,
    12: 0.0025,
}


class AnnualReportGenerator:
    """Builds yearly analytics and renders them as a downloadable PDF."""

    def __init__(self, price_fetcher):
        self.price_fetcher = price_fetcher
        self.index_candidates = ["URTH", "UQ2B.F", "DBPG.DE", "EXV1.DE"]
        self.dax_candidates = ["DAX", "^GDAXI"]

    # Public API -----------------------------------------------------
    def generate_user_report(
        self, user: Dict, stocks_with_prices: List[Dict], year: int = 2025
    ) -> Tuple[bytes, Dict]:
        """Create the PDF and return its raw bytes alongside the context used."""
        context = self._build_report_context(user, stocks_with_prices, year)
        pdf_bytes = self._render_pdf(user, context, year)
        return pdf_bytes, context

    # Data preparation ----------------------------------------------
    def _build_report_context(
        self, user: Dict, stocks_with_prices: List[Dict], year: int
    ) -> Dict:
        start_date = datetime(year, 1, 1)
        end_date = min(datetime(year, 12, 31), datetime.now())
        if end_date < start_date:
            end_date = start_date

        date_index = pd.date_range(start=start_date, end=end_date, freq="B")

        # Build portfolio value series (total, then apply user share)
        price_series_map = {}
        portfolio_series = pd.Series(0.0, index=date_index)

        for stock in STOCKS:
            symbol = stock["symbol"]
            default_price = stock.get("current_price", stock["price"])

            if symbol == "CASH":
                cash_series = pd.Series(default_price * stock["quantity"], index=date_index)
                portfolio_series += cash_series
                price_series_map[symbol] = cash_series / stock["quantity"]
                continue

            series = self._get_price_series(
                symbol,
                start_date,
                end_date,
                default_price,
            )
            price_series_map[symbol] = series
            portfolio_series += series * stock["quantity"]

        user_series = portfolio_series * user["portfolio_percentage"]

        # Benchmarks
        index_symbol = self._pick_symbol(self.index_candidates)
        dax_symbol = self._pick_symbol(self.dax_candidates)

        index_series = self._get_price_series(
            index_symbol,
            start_date,
            end_date,
            self._default_price_for_symbol(index_symbol),
        )
        dax_series = self._get_price_series(
            dax_symbol,
            start_date,
            end_date,
            self._default_price_for_symbol(dax_symbol),
        )

        # Inflation adjusted performance
        inflation_multiplier = self._build_inflation_index(date_index)
        real_series = user_series / inflation_multiplier

        # Payment markers for the selected year
        payment_events = self._collect_payment_events(user, start_date, end_date)

        # Position-level stats
        breakdown = self._build_position_breakdown(
            stocks_with_prices, price_series_map, end_date
        )

        monthly_returns = self._build_monthly_returns(price_series_map, start_date, end_date)

        summary = self._build_summary(user_series, index_series, dax_series, real_series)

        return {
            "date_index": date_index,
            "user_series": user_series,
            "index_series": index_series,
            "dax_series": dax_series,
            "inflation_index": inflation_multiplier,
            "real_series": real_series,
            "payments": payment_events,
            "breakdown": breakdown,
            "monthly_returns": monthly_returns,
            "summary": summary,
            "index_symbol": index_symbol,
            "dax_symbol": dax_symbol,
            "end_date": end_date,
        }

    def _get_price_series(
        self, symbol: str, start: datetime, end: datetime, default_price: float
    ) -> pd.Series:
        """Fetch close prices and align to business days with graceful fallback."""
        full_index = pd.date_range(start=start, end=end, freq="B")
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start, end=end + timedelta(days=2))

            if hist.empty:
                return pd.Series(default_price, index=full_index)

            closes = hist["Close"]
            closes.index = pd.to_datetime(closes.index).tz_localize(None)
            closes = closes.groupby(closes.index.date).last()
            closes.index = pd.to_datetime(closes.index)
            aligned = closes.reindex(full_index).ffill().bfill()
            if aligned.isna().all():
                aligned = pd.Series(default_price, index=full_index)
            return aligned
        except Exception:
            return pd.Series(default_price, index=full_index)

    def _build_inflation_index(self, index: pd.DatetimeIndex) -> pd.Series:
        """Create a cumulative inflation index from monthly assumptions."""
        factors = []
        cumulative = 1.0
        for dt in index:
            monthly_rate = DEFAULT_2025_INFLATION.get(dt.month, 0.0025)
            cumulative *= 1 + monthly_rate
            factors.append(cumulative)
        return pd.Series(factors, index=index)

    def _collect_payment_events(
        self, user: Dict, start: datetime, end: datetime
    ) -> List[Dict]:
        events = []
        if "payments" in user:
            for payment in user["payments"]:
                pay_date = datetime.strptime(payment["date"], "%Y-%m-%d")
                if start <= pay_date <= end:
                    events.append({"date": pay_date, "amount": payment["amount"]})
        elif "paid_date" in user:
            pay_date = datetime.strptime(user["paid_date"], "%Y-%m-%d")
            if start <= pay_date <= end:
                events.append({"date": pay_date, "amount": user.get("initial_investment", 0)})
        return events

    def _build_position_breakdown(
        self, stocks: List[Dict], price_series_map: Dict[str, pd.Series], end_date: datetime
    ) -> pd.DataFrame:
        rows = []
        total_portfolio_value = sum(
            self.price_fetcher.get_stock_value(stock) for stock in stocks
        )

        for stock in stocks:
            if stock["symbol"] == "CASH":
                continue

            series = price_series_map.get(stock["symbol"])
            start_price = series.iloc[0] if series is not None else stock.get("price", 0)
            end_price = series.iloc[-1] if series is not None else stock.get("price", 0)
            change_pct = ((end_price - start_price) / start_price * 100) if start_price else 0

            position_value = stock["quantity"] * end_price
            weight = (position_value / total_portfolio_value * 100) if total_portfolio_value else 0

            rows.append(
                {
                    "Symbol": stock["symbol"],
                    "Name": stock["name"],
                    "Weight %": weight,
                    "2025 Return %": change_pct,
                }
            )

        return pd.DataFrame(rows).sort_values("Weight %", ascending=False)

    def _build_monthly_returns(
        self, price_series_map: Dict[str, pd.Series], start: datetime, end: datetime
    ) -> pd.DataFrame:
        months = pd.period_range(start=start, end=end, freq="M")
        table = pd.DataFrame(index=months)

        for symbol, series in price_series_map.items():
            if series is None or symbol == "CASH":
                continue
            monthly_prices = series.resample("M").last()
            monthly_returns = monthly_prices.pct_change() * 100
            # Reindex to full month list to keep future months as NaN
            monthly_returns = monthly_returns.reindex(months, fill_value=float("nan"))
            table[symbol] = monthly_returns.values

        return table

    def _build_summary(
        self,
        user_series: pd.Series,
        index_series: pd.Series,
        dax_series: pd.Series,
        real_series: pd.Series,
    ) -> Dict:
        def _pct(series: pd.Series) -> float:
            if series.empty:
                return 0
            start_val = series.iloc[0]
            end_val = series.iloc[-1]
            return ((end_val - start_val) / start_val * 100) if start_val else 0

        return {
            "portfolio_return_pct": _pct(user_series),
            "index_return_pct": _pct(index_series),
            "dax_return_pct": _pct(dax_series),
            "real_return_pct": _pct(real_series),
        }

    def _pick_symbol(self, candidates: List[str]) -> str:
        available_symbols = {stock["symbol"] for stock in STOCKS}
        for candidate in candidates:
            if candidate in available_symbols:
                return candidate
        return candidates[0]

    def _default_price_for_symbol(self, symbol: str) -> float:
        found = next((s for s in STOCKS if s["symbol"] == symbol), None)
        if found:
            return found.get("current_price", found.get("price", 100))
        return 100

    # PDF rendering --------------------------------------------------
    def _render_pdf(self, user: Dict, context: Dict, year: int) -> bytes:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Header
        pdf.set_fill_color(32, 60, 116)
        pdf.rect(0, 0, 210, 25, "F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 18)
        pdf.ln(10)
        pdf.cell(0, 10, f"{year} Portfolio Report - {user['username'].title()}", ln=1, align="C")

        # Summary metrics
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 8, "Performance Highlights", ln=1)
        pdf.set_font("Helvetica", "", 11)
        summary = context["summary"]
        pdf.cell(
            0,
            6,
            f"Portfolio: {summary['portfolio_return_pct']:+.2f}%   "
            f"Real (inflation-adjusted): {summary['real_return_pct']:+.2f}%   "
            f"{context['index_symbol']} Benchmark: {summary['index_return_pct']:+.2f}%   "
            f"{context['dax_symbol']} Benchmark: {summary['dax_return_pct']:+.2f}%",
            ln=1,
        )
        pdf.ln(2)

        # Portfolio vs benchmarks chart
        perf_fig = self._build_performance_chart(context, year)
        pdf = self._embed_chart(pdf, perf_fig, "Portfolio vs Benchmarks", y_padding=2)

        # Inflation chart
        inflation_fig = self._build_inflation_chart(context, year)
        pdf = self._embed_chart(pdf, inflation_fig, "Inflation-Adjusted Performance", y_padding=4)

        # Payment markers
        if context["payments"]:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "2025 Contributions", ln=1)
            pdf.set_font("Helvetica", "", 11)
            for payment in context["payments"]:
                pdf.cell(
                    0,
                    6,
                    f"{payment['date'].strftime('%Y-%m-%d')}: +{payment['amount']:,.2f} EUR",
                    ln=1,
                )
            pdf.ln(2)

        # Position breakdown
        if not context["breakdown"].empty:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Positions & Performance", ln=1)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(40, 8, "Symbol", border=1)
            pdf.cell(70, 8, "Name", border=1)
            pdf.cell(30, 8, "Weight %", border=1, align="R")
            pdf.cell(40, 8, "2025 Return %", border=1, ln=1, align="R")
            for _, row in context["breakdown"].iterrows():
                pdf.cell(40, 8, str(row["Symbol"]), border=1)
                pdf.cell(70, 8, str(row["Name"])[:30], border=1)
                pdf.cell(30, 8, f"{row['Weight %']:.2f}", border=1, align="R")
                pdf.cell(40, 8, f"{row['2025 Return %']:+.2f}", border=1, ln=1, align="R")
            pdf.ln(2)

        # Monthly returns table
        if not context["monthly_returns"].empty:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Monthly Returns by Position (%)", ln=1)
            pdf.set_font("Helvetica", "", 7)
            month_labels = [p.strftime("%b") for p in context["monthly_returns"].index]
            symbols = list(context["monthly_returns"].columns)

            symbol_col_width = 20
            month_col_width = max(10, (190 - symbol_col_width) / max(1, len(month_labels)))

            # Header
            pdf.cell(symbol_col_width, 7, "Symbol", border=1, align="C")
            for month in month_labels:
                pdf.cell(month_col_width, 7, month, border=1, align="C")
            pdf.ln()

            # Rows
            for symbol in symbols:
                pdf.cell(symbol_col_width, 7, symbol, border=1)
                for val in context["monthly_returns"][symbol]:
                    cell_text = "-" if pd.isna(val) else f"{val:+.1f}"
                    pdf.cell(month_col_width, 7, cell_text, border=1, align="R")
                pdf.ln()

        raw = pdf.output(dest="S")
        if isinstance(raw, (bytes, bytearray)):
            return bytes(raw)
        return str(raw).encode("latin1")

    def _embed_chart(self, pdf: FPDF, fig, title: str, y_padding: int = 0) -> FPDF:
        """Render a matplotlib figure to PNG and embed it in the PDF."""
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, title, ln=1)

        buffer = io.BytesIO()
        try:
            fig.savefig(buffer, format="png", bbox_inches="tight", dpi=200)
            buffer.seek(0)
            pdf.image(buffer, x=10, w=190, type="PNG")
        except Exception as err:
            safe_err = str(err).encode("ascii", errors="replace").decode("ascii")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, f"[Chart unavailable: {safe_err}]")
        finally:
            plt.close(fig)

        pdf.ln(y_padding)
        return pdf

    # Charts ---------------------------------------------------------
    def _build_performance_chart(self, context: Dict, year: int):
        dates = context["date_index"]
        user_base = context["user_series"].iloc[0] or 1
        index_base = context["index_series"].iloc[0] or 1
        dax_base = context["dax_series"].iloc[0] or 1

        user_norm = (context["user_series"] / user_base) * 100
        index_norm = (context["index_series"] / index_base) * 100
        dax_norm = (context["dax_series"] / dax_base) * 100

        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(dates, user_norm, label="Portfolio", linewidth=2.5, color="#1f77b4")
        ax.plot(dates, index_norm, label=context["index_symbol"], linewidth=1.8, linestyle="--", color="#2ca02c")
        ax.plot(dates, dax_norm, label=context["dax_symbol"], linewidth=1.8, linestyle=":", color="#ff7f0e")

        for payment in context["payments"]:
            payment_date = payment["date"]
            # Align to nearest available date to avoid missing index keys on weekends
            aligned_date = user_norm.index[user_norm.index.get_indexer([payment_date], method="nearest")[0]]
            ax.scatter(aligned_date, user_norm.loc[aligned_date], color="#d62728", zorder=5)
            ax.text(
                aligned_date,
                user_norm.loc[aligned_date],
                f" +{payment['amount']:,.0f}",
                color="#d62728",
                fontsize=8,
                va="bottom",
            )

        ax.set_title(f"{year} Performance vs Benchmarks")
        ax.set_ylabel("Index (100 = period start)")
        ax.grid(alpha=0.2)
        ax.legend()
        fig.autofmt_xdate()
        return fig

    def _build_inflation_chart(self, context: Dict, year: int):
        dates = context["date_index"]
        nominal_base = context["user_series"].iloc[0] or 1
        real_base = context["real_series"].iloc[0] or 1
        nominal = (context["user_series"] / nominal_base) * 100
        real = (context["real_series"] / real_base) * 100

        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(dates, nominal, label="Nominal", linewidth=2.5, color="#1f77b4")
        ax.plot(dates, real, label="Inflation-adjusted", linewidth=2, linestyle="--", color="#d62728")
        ax.set_title(f"{year} Inflation Adjustment")
        ax.set_ylabel("Index (100 = period start)")
        ax.grid(alpha=0.2)
        ax.legend()
        fig.autofmt_xdate()
        return fig
