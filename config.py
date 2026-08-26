"""
Portfolio configuration data
"""

from ownership import get_ownership_percentage

USERS = [
    {
        "username": "user",
        "portfolio_percentage": 1.0,
        "initial_investment": 231158,
        "paid_date": "2022-01-01"
    },
    {
        "username": "foehr",
        "portfolio_percentage": get_ownership_percentage("foehr"),
        "initial_investment": 20000,
        "payments": [
            {"amount": 20000, "date": "2025-07-01"},
            {"amount": 300, "date": "2025-10-01"},
            {"amount": 300, "date": "2025-11-01"},
            {"amount": 200, "date": "2025-11-01"},
            {"amount": 500, "date": "2025-12-01"},
            {"amount": 500, "date": "2026-01-01"},
            {"amount": 500, "date": "2026-02-01"},
            {"amount": 500, "date": "2026-02-02"},
            {"amount": 5000, "date": "2026-03-02"},
            {"amount": 500, "date": "2026-04-01"},
            {"amount": 500, "date": "2026-05-04", "type": "Cash pay-in"},
            {"amount": 9500, "date": "2026-06-01", "type": "Cash pay-in"}
        ]
    },
    {
        "username": "kremer",
        "portfolio_percentage": get_ownership_percentage("kremer"),
        "initial_investment": 130000,
        "paid_date": "2022-01-01"
    },
    {
        "username": "annika",
        "portfolio_percentage": get_ownership_percentage("annika"),
        "initial_investment": 200,
        "payments": [
            {"amount": 100, "date": "2024-09-01"},
            {"amount": 50, "date": "2024-10-01"},
            {"amount": 50, "date": "2024-11-01"},
            {"amount": 50, "date": "2024-12-01"},
            {"amount": 100, "date": "2025-01-01"},
            {"amount": 50, "date": "2025-02-01"},
            {"amount": 50, "date": "2025-03-01"},
            {"amount": 50, "date": "2025-04-01"},
            {"amount": 50, "date": "2025-05-01"},
            {"amount": 50, "date": "2025-06-01"},
            {"amount": 50, "date": "2025-07-01"},
            {"amount": 70, "date": "2025-08-01"},
            {"amount": 50, "date": "2025-09-01"},
            {"amount": 50, "date": "2025-10-01"},
            {"amount": 50, "date": "2025-11-01"},
            {"amount": 50, "date": "2025-12-01"},
            {"amount": 100, "date": "2026-01-01"},
            {"amount": 20, "date": "2026-01-27"},
            {"amount": 150, "date": "2026-02-05"},
            {"amount": 50, "date": "2026-03-01"},
            {"amount": 100, "date": "2026-04-01"},
            {"amount": 100, "date": "2026-05-01", "type": "Share transfer from Christian"},
            {"amount": 150, "date": "2026-05-27", "type": "Share transfer from Christian"},
            {"amount": 64.26, "date": "2026-05-27", "type": "Share transfer from Christian"},
            {"amount": 50, "date": "2026-06-26", "type": "Share transfer from Christian"},
            {"amount": 100, "date": "2026-07-01", "type": "Share transfer from Christian"},
            {"amount": 50, "date": "2026-08-26", "type": "Share transfer from Christian"}
        ]
    },
    {
        "username": "juergen",
        "portfolio_percentage": get_ownership_percentage("juergen"),
        "initial_investment": 50000,
        "payments": [
            {"amount": 50000, "date": "2025-07-03", "type": "Confirmed cash pay-in"},
            {"amount": 35000, "date": "2026-01-05", "type": "Confirmed cash pay-in"},
            {"amount": 15000, "date": "2026-01-06", "type": "Confirmed cash pay-in"}
        ]
    },
    {
        "username": "christian",
        "portfolio_percentage": get_ownership_percentage("christian"),
        "initial_investment": 30000,
        "payments": [
            {"amount": 30000, "date": "2022-01-01", "type": "Initial investment"},
            {"amount": -500, "date": "2026-02-02", "type": "Share sale to Foehr"},
            {"amount": -5000, "date": "2026-03-02", "type": "Share sale to Foehr"},
            {"amount": -500, "date": "2026-04-01", "type": "Share sale to Foehr"},
            {"amount": -100, "date": "2026-05-01", "type": "Share transfer to Annika"},
            {"amount": -150, "date": "2026-05-27", "type": "Share transfer to Annika"},
            {"amount": -64.26, "date": "2026-05-27", "type": "Share transfer to Annika"},
            {"amount": -50, "date": "2026-06-26", "type": "Share transfer to Annika"},
            {"amount": -100, "date": "2026-07-01", "type": "Share transfer to Annika"},
            {"amount": -50, "date": "2026-08-26", "type": "Share transfer to Annika"}
        ]
    }
]

ASSET_SNAPSHOT_DATE = "2026-08-26"

# The EUR 4,000 transfer is already reflected in the current broker cash balance
# below. Keeping a separate deduction would remove it from portfolio assets twice.
CONFIRMED_CASH_WITHDRAWAL_EUR = 0.00

EXECUTED_TRADES = [
    {
        "date": "2026-08-26",
        "account_id": "1182076586",
        "isin": "IE00BLS09N40",
        "symbol": "3BAL.L",
        "side": "sale",
        "quantity": 214.0,
        "execution_price_eur": 100.02,
        "gross_proceeds_eur": 21404.28,
        "post_trade_cash_balance_eur": 15699.17,
        "basis_method": "FIFO",
        "source_note": "User-confirmed executed order and post-trade cash balance",
    },
]

# Legal positions exactly as reported by the two custody accounts. Quantities are
# never adjusted for exchange rates, ADR ratios, or quote units. `value_eur` is the
# broker-reported snapshot value and is used as the fallback when a live quote is
# unavailable.
PORTFOLIO_ACCOUNTS = [
    {
        "account_id": "1182076586",
        "cash_balance_eur": 15699.17,
        "holdings": [
            {"isin": "IE00B4L5Y983", "wkn": "A0RPWH", "symbol": "EUNL.DE", "quantity": 734.876, "value_eur": 94773.28, "cost_basis_eur": 44941.80, "name": "iShares Core MSCI World", "industry": "Index", "quote_currency": "EUR"},
            {"isin": "US9497461015", "wkn": "857949", "symbol": "WFC", "quantity": 400.0, "value_eur": 30359.70, "cost_basis_eur": 10337.70, "name": "Wells Fargo", "industry": "Bank", "quote_currency": "USD"},
            {"isin": "DE0006047004", "wkn": "604700", "symbol": "HEI.DE", "quantity": 185.0, "value_eur": 30201.25, "cost_basis_eur": 9400.20, "name": "Heidelberg Materials", "industry": "Materials", "quote_currency": "EUR"},
            {"isin": "US1729674242", "wkn": "A1H92V", "symbol": "C", "quantity": 200.0, "value_eur": 23524.00, "cost_basis_eur": 9248.00, "name": "Citigroup", "industry": "Bank", "quote_currency": "USD"},
            {"isin": "LU0411078552", "wkn": "DBX0B5", "symbol": "DBPG.DE", "quantity": 45.0, "value_eur": 14418.00, "cost_basis_eur": 6510.60, "name": "Xtrackers S&P 500 2x Leveraged", "industry": "Index", "quote_currency": "EUR"},
            {"isin": "IE00BLS09N40", "wkn": "A14JCP", "symbol": "3BAL.L", "quantity": 364.0, "value_eur": 36407.28, "cost_basis_eur": 3161.55, "name": "WisdomTree EURO STOXX Banks 3x", "industry": "European Banks", "quote_currency": "GBP", "quote_multiplier": 0.01},
            {"isin": "DE000A0F5UJ7", "wkn": "A0F5UJ", "symbol": "EXV1.DE", "quantity": 284.0, "value_eur": 12126.80, "cost_basis_eur": 3998.72, "name": "iShares STOXX Europe 600 Banks", "industry": "European Banks", "quote_currency": "EUR"},
            {"isin": "DE0006062144", "wkn": "606214", "symbol": None, "quantity": 100.0, "value_eur": 5946.00, "broker_value_eur": 6040.00, "cost_basis_eur": 3840.50, "name": "Covestro (pending squeeze-out)", "industry": "Chemicals", "quote_currency": "EUR", "price_mode": "fixed", "fixed_price_reason": "Pending cash compensation at EUR 59.46 per share"},
            {"isin": "GB0007980591", "wkn": "850517", "symbol": "BP.L", "quantity": 1000.0, "value_eur": 6225.00, "cost_basis_eur": 3779.00, "name": "BP", "industry": "Oil & Gas", "quote_currency": "GBP", "quote_multiplier": 0.01},
            {"isin": "US84615Q1031", "wkn": "A42D4F", "symbol": "SPCX", "quantity": 28.0, "value_eur": 3321.21, "cost_basis_eur": 3275.00, "name": "SpaceX Class A", "industry": "Aerospace", "quote_currency": "USD", "return_reference_date": "2026-06-12", "return_reference_price_eur": 116.9642857143, "return_reference_label": "IPO price ($135.00)"},
            {"isin": "GB00BP6MXD84", "wkn": "A3C99G", "symbol": "SHEL.L", "quantity": 150.0, "value_eur": 5883.00, "cost_basis_eur": 2768.58, "name": "Shell", "industry": "Oil & Gas", "quote_currency": "GBP", "quote_multiplier": 0.01},
            {"isin": "LU0252633754", "wkn": "LYX0AC", "symbol": "LYY7.DE", "quantity": 15.543, "value_eur": 3738.09, "cost_basis_eur": 2581.49, "name": "Amundi DAX III", "industry": "DAX", "quote_currency": "EUR"},
            {"isin": "US69608A1088", "wkn": "A2QA4J", "symbol": "PLTR", "quantity": 100.0, "value_eur": 15290.00, "cost_basis_eur": 895.33, "name": "Palantir", "industry": "Software", "quote_currency": "USD"},
            {"isin": "LU0256839274", "wkn": "A0KDMU", "symbol": "UQ2B.F", "quantity": 2.897, "value_eur": 1079.35, "cost_basis_eur": 845.22, "name": "AGIF Europe Equity Growth", "industry": "European Equity", "quote_currency": "EUR"},
            {"isin": "DE0005140008", "wkn": "514000", "symbol": "DBK.DE", "quantity": 1.0, "value_eur": 33.20, "cost_basis_eur": 10.76, "name": "Deutsche Bank", "industry": "Bank", "quote_currency": "EUR"},
        ],
    },
    {
        "account_id": "1183194735",
        "cash_balance_eur": 34693.63,
        "holdings": [
            {"isin": "US9100471096", "wkn": "A1C6TV", "symbol": "UAL", "quantity": 60.0, "value_eur": 6570.00, "cost_basis_eur": 3088.20, "name": "United Airlines", "industry": "Airlines", "quote_currency": "USD"},
            {"isin": "LU0256839274", "wkn": "A0KDMU", "symbol": "UQ2B.F", "quantity": 3.404, "value_eur": 1268.25, "cost_basis_eur": 1241.57, "name": "AGIF Europe Equity Growth", "industry": "European Equity", "quote_currency": "EUR"},
            {"isin": "US1729674242", "wkn": "A1H92V", "symbol": "C", "quantity": 140.0, "value_eur": 16466.80, "cost_basis_eur": 6421.20, "name": "Citigroup", "industry": "Bank", "quote_currency": "USD"},
            {"isin": "IE00B4L5Y983", "wkn": "A0RPWH", "symbol": "EUNL.DE", "quantity": 117.299, "value_eur": 15126.88, "cost_basis_eur": 10427.78, "name": "iShares Core MSCI World", "industry": "Index", "quote_currency": "EUR"},
            {"isin": "LU0290358497", "wkn": "DBX0AN", "symbol": "XEON.DE", "quantity": 334.0, "value_eur": 50054.24, "cost_basis_eur": 49878.89, "name": "Xtrackers EUR Overnight Rate", "industry": "Money Market", "quote_currency": "EUR"},
            {"isin": "US38141G1040", "wkn": "920332", "symbol": "GS", "quantity": 9.0, "value_eur": 8049.60, "cost_basis_eur": 2418.75, "name": "Goldman Sachs", "industry": "Bank", "quote_currency": "USD"},
            {"isin": "IE00BLS09N40", "wkn": "A14JCP", "symbol": "3BAL.L", "quantity": 70.0, "value_eur": 7034.30, "cost_basis_eur": 1148.14, "name": "WisdomTree EURO STOXX Banks 3x", "industry": "European Banks", "quote_currency": "GBP", "quote_multiplier": 0.01},
            {"isin": "US8447411088", "wkn": "862837", "symbol": "LUV", "quantity": 100.0, "value_eur": 3890.00, "cost_basis_eur": 2405.00, "name": "Southwest Airlines", "industry": "Airlines", "quote_currency": "USD"},
        ],
    },
]


def _aggregate_stocks(accounts):
    """Aggregate account-level legal holdings by ISIN for dashboard display."""
    aggregated = {}
    for account in accounts:
        account_id = account["account_id"]
        for holding in account["holdings"]:
            isin = holding["isin"]
            if isin not in aggregated:
                aggregated[isin] = {
                    key: value
                    for key, value in holding.items()
                    if key not in {"quantity", "value_eur", "cost_basis_eur"}
                }
                aggregated[isin].update({
                    "quantity": 0.0,
                    "value_eur": 0.0,
                    "cost_basis_eur": 0.0,
                    "account_quantities": {},
                })

            position = aggregated[isin]
            position["quantity"] += holding["quantity"]
            position["value_eur"] += holding["value_eur"]
            position["cost_basis_eur"] += holding["cost_basis_eur"]
            position["account_quantities"][account_id] = holding["quantity"]

    stocks = []
    for position in aggregated.values():
        # `price` is always an EUR-per-legal-unit fallback. Live quote currency
        # conversion is handled by PriceFetcher.
        position["price"] = (
            position["value_eur"] / position["quantity"]
            if position["quantity"]
            else 0.0
        )
        stocks.append(position)

    broker_cash = sum(account["cash_balance_eur"] for account in accounts)
    total_cash = broker_cash - CONFIRMED_CASH_WITHDRAWAL_EUR
    stocks.append({
        "isin": "CASH-EUR",
        "wkn": None,
        "symbol": "CASH",
        "quantity": total_cash,
        "price": 1.0,
        "value_eur": total_cash,
        "cost_basis_eur": total_cash,
        "name": "Cash",
        "industry": None,
        "quote_currency": "EUR",
        "account_quantities": {
            account["account_id"]: account["cash_balance_eur"]
            for account in accounts
        },
        "broker_reported_value_eur": broker_cash,
        "confirmed_withdrawal_eur": CONFIRMED_CASH_WITHDRAWAL_EUR,
    })
    return stocks


STOCKS = _aggregate_stocks(PORTFOLIO_ACCOUNTS)


def get_asset_reconciliation():
    """Reconcile broker assets to the net amount attributed to the owners."""
    broker_reported_assets = round(
        sum(
            account["cash_balance_eur"]
            + sum(
                holding.get("broker_value_eur", holding["value_eur"])
                for holding in account["holdings"]
            )
            for account in PORTFOLIO_ACCOUNTS
        ),
        2,
    )
    total_assets = round(sum(stock["value_eur"] for stock in STOCKS), 2)
    return {
        "as_of": ASSET_SNAPSHOT_DATE,
        "broker_reported_assets_eur": broker_reported_assets,
        "confirmed_cash_withdrawal_eur": CONFIRMED_CASH_WITHDRAWAL_EUR,
        "valuation_adjustments_eur": round(
            total_assets
            - (broker_reported_assets - CONFIRMED_CASH_WITHDRAWAL_EUR),
            2,
        ),
        "total_assets_eur": total_assets,
        "attributed_assets_eur": total_assets,
        "other_overhang_eur": 0.0,
    }


ASSET_RECONCILIATION = get_asset_reconciliation()
