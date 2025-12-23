#!/usr/bin/env python3
"""
Plot 2025 YTD performance (rebased to 100 on 2025-01-01) for:
- S&P 500 (grey benchmark)
- MSCI World (URTH)
- A portfolio containing all configured holdings; 3BAL.L is present throughout, UAL/LUV are bought on 2025-04-07 (reducing cash).
Also produce pie charts of portfolio value split by category and YTD earnings share by category.
"""

from __future__ import annotations

import datetime as dt
import sys
from typing import Dict, List

import config

import matplotlib

# Use non-GUI backend so the script can run headless and save to file quickly.
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

# Category grouping
CATEGORY_MAP = {
    "CASH": "Cash/Covestro",
    "1COV.DE": "Cash/Covestro",
    "UQ2B.F": "Index Funds",
    "EXV1.DE": "Index Funds",
    "URTH": "Index Funds",
    "DAX": "Index Funds",
    "DBPG.DE": "Index Funds",
    "3BAL.L": "Levered",
}
DEFAULT_CATEGORY = "Single Stocks"
CATEGORY_ORDER = ["Cash/Covestro", "Index Funds", "Single Stocks", "Levered"]
RISK_LABELS = {
    "Cash/Covestro": "No Risk",
    "Index Funds": "Low Risk",
    "Single Stocks": "Medium Risk",
    "Levered": "High Risk",
}
RISK_ORDER = ["No Risk", "Low Risk", "Medium Risk", "High Risk"]


def get_base_start() -> dt.date:
    """Return Jan 1, 2025 (base year for rebasing)."""
    return dt.date(2025, 1, 1)


def fetch_prices(tickers: List[str], start: dt.date, end: dt.date) -> tuple[pd.DataFrame, List[str]]:
    """Download adjusted close prices for tickers between start and end."""
    data = yf.download(
        tickers,
        start=start,
        end=end + dt.timedelta(days=1),
        progress=False,
        auto_adjust=False,
    )["Adj Close"]
    if isinstance(data, pd.Series):
        data = data.to_frame()
    data = data.sort_index()

    # Keep only columns that returned data; forward-fill across non-trading days.
    available_cols = [c for c in data.columns if c in tickers]
    data = data[available_cols].ffill()
    # Drop any leading rows that remain NaN for all series.
    data = data.dropna(how="all")

    missing = [t for t in tickers if t not in available_cols]
    return data, missing


def rebase_series_to_100(series: pd.Series, base_ts: pd.Timestamp) -> pd.Series:
    """Rebase a series to 100 at base_ts (or next available date)."""
    if base_ts not in series.index:
        idx = series.index.get_indexer([base_ts], method="bfill")[0]
        if idx == -1:
            idx = 0
        base_ts = series.index[idx]
    base_value = series.loc[base_ts]
    return series.divide(base_value).multiply(100)


def main(purchase_str: str = "2025-04-07") -> None:
    today = dt.date.today()
    purchase_date = dt.datetime.strptime(purchase_str, "%Y-%m-%d").date()

    base_start = get_base_start()
    start_date = min(base_start, purchase_date)

    # Prepare tickers from config; exclude CASH, add S&P 500 benchmark.
    stock_entries = config.STOCKS
    cash_entry = next(s for s in stock_entries if s["symbol"] == "CASH")
    holdings = {s["symbol"]: s["quantity"] for s in stock_entries if s["symbol"] != "CASH"}
    ticker_list = list(holdings.keys())
    all_fetch = ticker_list + ["^GSPC"]

    prices, missing = fetch_prices(all_fetch, start=start_date, end=today)

    # Substitute URTH for UQ2B.F if missing (proxy for MSCI World exposure).
    if "UQ2B.F" in missing and "URTH" in prices.columns:
        prices["UQ2B.F"] = prices["URTH"]
        missing = [m for m in missing if m != "UQ2B.F"]

    if missing:
        print(f"Warning: missing price data for: {', '.join(missing)}")
    if "^GSPC" not in prices.columns:
        raise ValueError("S&P 500 (^GSPC) data not available.")

    # Drop holdings that lack price data.
    holdings = {k: v for k, v in holdings.items() if k in prices.columns}
    ticker_list = list(holdings.keys())

    purchase_ts = pd.Timestamp(purchase_date)
    if purchase_ts not in prices.index:
        purchase_idx = prices.index.get_indexer([purchase_ts], method="pad")[0]
        if purchase_idx == -1:
            purchase_idx = 0
        purchase_ts = prices.index[purchase_idx]

    # Set airline quantities to 0 before purchase.
    before_qty = holdings.copy()
    if "UAL" in before_qty:
        before_qty["UAL"] = 0
    if "LUV" in before_qty:
        before_qty["LUV"] = 0

    after_qty = holdings.copy()

    qty_df = pd.DataFrame(before_qty, index=prices.index)
    for col, val in after_qty.items():
        qty_df.loc[prices.index >= purchase_ts, col] = val

    ticker_prices = prices[list(after_qty.keys())]

    # Adjust cash for airline purchase at purchase_ts (only if both tickers exist).
    purchase_cost = 0.0
    for t in ("UAL", "LUV"):
        if t in after_qty and t in prices.columns:
            purchase_cost += prices.loc[purchase_ts, t] * after_qty[t]
    cash_initial = cash_entry["quantity"]
    cash_after_purchase = cash_initial - purchase_cost
    cash_series = pd.Series(cash_initial, index=prices.index)
    cash_series.loc[cash_series.index >= purchase_ts] = cash_after_purchase

    portfolio_values = (ticker_prices * qty_df).sum(axis=1) + cash_series

    base_ts = pd.Timestamp(base_start)
    portfolio_rebased = rebase_series_to_100(portfolio_values, base_ts)
    sp500_rebased = rebase_series_to_100(prices["^GSPC"], base_ts)
    msci_rebased = rebase_series_to_100(prices["URTH"], base_ts) if "URTH" in prices.columns else None

    # --- Pie chart data ---
    final_prices = ticker_prices.ffill().iloc[-1].fillna(0.0)
    final_qty = {k: float(v) for k, v in after_qty.items()}
    final_values = final_prices * pd.Series(final_qty, dtype=float)
    final_values["CASH"] = float(cash_series.iloc[-1])

    def base_price_for(ticker: str) -> float:
        if ticker not in prices.columns:
            return 0.0
        series = prices[ticker].ffill()
        ref_ts = purchase_ts if ticker in ("UAL", "LUV") else base_ts
        if ref_ts not in series.index:
            idx = series.index.get_indexer([ref_ts], method="bfill")[0]
            if idx == -1:
                idx = 0
            ref_ts_ = series.index[idx]
        else:
            ref_ts_ = ref_ts
        val = float(series.loc[ref_ts_])
        return val if pd.notna(val) else 0.0

    earnings = {}
    for tkr, qty in final_qty.items():
        qty = float(qty)
        base_price = base_price_for(tkr)
        base_val = base_price * qty
        current_price = float(final_prices.get(tkr, 0.0) or 0.0)
        earn = current_price * qty - base_val
        cat = CATEGORY_MAP.get(tkr, DEFAULT_CATEGORY)
        if pd.notna(earn):
            earnings[cat] = earnings.get(cat, 0.0) + earn

    # Cash earnings assumed zero (no yield).
    cash_cat = CATEGORY_MAP.get("CASH", DEFAULT_CATEGORY)
    earnings[cash_cat] = earnings.get(cash_cat, 0.0)

    category_values = {}
    for tkr, val in final_values.items():
        cat = CATEGORY_MAP.get(tkr, DEFAULT_CATEGORY)
        category_values[cat] = category_values.get(cat, 0.0) + float(val if pd.notna(val) else 0.0)

    # Keep consistent order and drop zeros.
    def ordered_nonzero(d: Dict[str, float], order: List[str]) -> Dict[str, float]:
        ordered = {}
        for cat in order:
            if d.get(cat, 0):
                ordered[cat] = d[cat]
        for cat, val in d.items():
            if cat not in ordered and val:
                ordered[cat] = val
        return ordered

    category_values = ordered_nonzero(category_values, CATEGORY_ORDER)
    earnings = ordered_nonzero(earnings, CATEGORY_ORDER)

    # Map to risk labels and aggregate
    def to_risk(d: Dict[str, float]) -> Dict[str, float]:
        risk = {}
        for cat, val in d.items():
            label = RISK_LABELS.get(cat, cat)
            risk[label] = risk.get(label, 0.0) + val
        return ordered_nonzero(risk, RISK_ORDER)

    category_values = to_risk(category_values)
    earnings = to_risk(earnings)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(sp500_rebased.index, sp500_rebased, label="S&P 500", color="grey", linewidth=2)
    if msci_rebased is not None:
        ax.plot(msci_rebased.index, msci_rebased, label="MSCI World (URTH)", linewidth=1.6)
    ax.plot(portfolio_rebased.index, portfolio_rebased, label="Total Portfolio", linewidth=2)

    ax.set_title(f"YTD: Portfolio vs S&P 500 (airlines added {purchase_ts.date()})")
    ax.set_ylabel("Rebased Level (100 = 1 Jan)")
    ax.set_xlabel("Date")
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.6)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()

    plt.tight_layout()
    output_path = "equity_comparison.png"
    plt.savefig(output_path, dpi=150)
    print(f"Saved plot to {output_path}")

    # Pie charts: portfolio value and YTD earnings
    pie_fig, pie_axes = plt.subplots(1, 2, figsize=(12, 6))

    def autopct_fmt(values):
        def _fmt(pct):
            total = sum(values)
            if total == 0:
                return ""
            return f"{pct:.1f}%"

        return _fmt

    # Portfolio value
    if category_values and sum(category_values.values()) > 0:
        pie_axes[0].pie(
            list(category_values.values()),
            labels=list(category_values.keys()),
            autopct=autopct_fmt(category_values.values()),
            startangle=90,
        )
        pie_axes[0].set_title("Portfolio Value by Category")
    else:
        pie_axes[0].text(0.5, 0.5, "No data", ha="center", va="center")
        pie_axes[0].axis("off")

    # Earnings (include magnitudes even if negative; show sign in labels)
    earnings_sizes = {k: abs(v) for k, v in earnings.items()}
    total_earn = sum(earnings_sizes.values())
    if earnings_sizes and total_earn > 0:
        labels = list(earnings_sizes.keys())
        pie_axes[1].pie(
            list(earnings_sizes.values()),
            labels=labels,
            autopct=autopct_fmt(earnings_sizes.values()),
            startangle=90,
        )
        pie_axes[1].set_title("2025 YTD Earnings by Category")
    else:
        # Show textual summary if effectively flat.
        pie_axes[1].text(0.5, 0.5, "Earnings ~0", ha="center", va="center")
        pie_axes[1].axis("off")

    plt.tight_layout()
    pie_output = "portfolio_pies.png"
    pie_fig.savefig(pie_output, dpi=150)
    print(f"Saved pie charts to {pie_output}")


if __name__ == "__main__":
    purchase = sys.argv[1] if len(sys.argv) > 1 else "2025-04-07"
    main(purchase)
