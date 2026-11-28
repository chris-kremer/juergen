# ANT / SKHY: incremental USD-funded correction

`shared_portfolio_adjustments.py` is the canonical lot ledger. It adds:

- SKHY: 26.57988951 legal quoted units, gross USD 2,999.93.
- ANT: 34.46621678 units / USD 2,999.93, 37.56056232 units / USD 2,999.93, plus 22 IPO shares at USD 83 / USD 1,826; combined 94.02677910 units / USD 7,825.86.
- Pooled cash correction: **USD -10,825.79**. The IPO evidence file references the same canonical lot; it is not another purchase.

## What the correction means

The user confirmed dollar-account funding. The dollar account number and opening balance are unknown. This is an **incremental correction against the existing pooled cash checkpoint**, not a new broker account with a negative balance. It does not establish that the original pooled checkpoint's absolute cash is complete or correctly split by currency. The two historical real EUR account balances and their historical reconciliation totals remain unchanged. No contribution, owner units or ownership percentages change.

The existing single `CASH` position carries `native_cash_adjustments`. For compatibility, its `quantity` remains the original EUR checkpoint quantity (93,477.18); its `price` / `current_price` is now a cash aggregation factor, **not a EUR cash unit or FX quote**. All current-value consumers must use `quantity * current_price` (or fallback `price`) / `PriceFetcher.get_stock_value`, not `quantity` alone. Historical consumers deliberately use `historical_price` and the pre-correction scope.

Current cash value = original pooled cash + native USD correction × EUR per USD.
The new stocks' current values and the cash correction use **one identical latest available EURUSD history observation**, even if the latest security observation is from an earlier date. Therefore the correction's NAV effect is `(new security USD value - gross USD cost) / EURUSD`, not a capital inflow or a fabricated investment loss. Daily previous stock prices are converted at the same valuation FX (constant-FX price comparison), not a complete daily FX-return attribution.

## Fallbacks and missing evidence

- Security quote failure: gross USD cost per legal unit at the same valuation FX. `price_source=acquisition_cost` and the failed symbol is returned.
- FX failure: use the disclosed common reference for assets and cash; return `EURUSD=X` as failed and `fx_source=reference_fallback`. This is not a live FX valuation.
- Static reference: Yahoo `EURUSD=X` Close 1.0905125141143799, daily bar labelled 2026-11-23, retrieved during implementation. This is a **valuation reference**, not execution-date FX or an exact FX trade timestamp. At the reference, fallback cash is EUR 83,549.9303262154 and combined new assets EUR 9,927.2496737846: snapshot pooled NAV stays EUR 481,045.10.
- Execution dates and fees remain unknown (`None`); 2026-11-19 is only the IPO report date. The deduction uses confirmed gross totals and does not invent an extra fee.
- `cost_basis_eur=None`: no historical EUR acquisition/tax basis is fabricated. The tax simulation is explicitly unavailable while that basis is missing. Since-purchase heatmap returns use USD cost at valuation FX, not actual historical EUR returns.
- New acquisitions and their cash correction are excluded from backward historical NAV/annual report scope until execution dates are established. They must not be backfilled across the previous year. The old history remains an approximation using its previous composition, not transaction-accurate broker NAV. Historical ATH claims are suppressed because full new-holding history is unavailable.
- SKHY ISIN/custody account are unresolved; no identifier or receipt ratio is guessed. Quote identity/freshness validation and publication remain separate deployment checks.

The supplemental trade-report basket must stop adding ANT/SKHY separately once it reads these canonical holdings, or its duplicate-symbol guard will intentionally reject the report. Do not consume `pending-trades/` as another executable ledger.
