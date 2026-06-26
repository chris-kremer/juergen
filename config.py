"""
Portfolio configuration data
"""

USERS = [
    {
        "username": "user",
        "portfolio_percentage": 1.0,
        "initial_investment": 231158,
        "paid_date": "2022-01-01"
    },
    {
        "username": "foehr",
        "portfolio_percentage": 0.091309020,
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
            {"amount": 9500, "date": "2026-06-01", "type": "Cash pay-in"}
        ]
    },
    {
        "username": "kremer",
        "portfolio_percentage": 0.527548533,
        "initial_investment": 130000,
        "paid_date": "2022-01-01"
    },
    {
        "username": "annika",
        "portfolio_percentage": 0.004410199,
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
            {"amount": 50, "date": "2026-06-26", "type": "Share transfer from Christian"}
        ]
    },
    {
        "username": "juergen",
        "portfolio_percentage": 0.239377930,
        "initial_investment": 50000,
        "payments": [
            {"amount": 50000, "date": "2025-06-01"},
            {"amount": 50000, "date": "2026-01-24"}
        ]
    },
    {
        "username": "christian",
        "portfolio_percentage": 0.138962484,
        "initial_investment": 30000,
        "payments": [
            {"amount": 30000, "date": "2022-01-01", "type": "Initial investment"},
            {"amount": -500, "date": "2026-02-02", "type": "Share sale to Foehr"},
            {"amount": -5000, "date": "2026-03-02", "type": "Share sale to Foehr"},
            {"amount": -500, "date": "2026-04-01", "type": "Share sale to Foehr"},
            {"amount": -100, "date": "2026-05-01", "type": "Share transfer to Annika"},
            {"amount": -150, "date": "2026-05-27", "type": "Share transfer to Annika"},
            {"amount": -64.26, "date": "2026-05-27", "type": "Share transfer to Annika"},
            {"amount": -50, "date": "2026-06-26", "type": "Share transfer to Annika"}
        ]
    }
]

STOCKS = [
    {"symbol": "UQ2B.F", "quantity": 5.4, "price": 365.00, "name": "Index Fund", "industry": "Index"},
    {"symbol": "BP", "quantity": 143.0, "price": 4.41, "name": "BP", "industry": "Oil & Gas"},
    {"symbol": "C", "quantity": 282.0, "price": 73.64, "name": "Citigroup", "industry": "Bank"},
    {"symbol": "HEI.DE", "quantity": 185.0, "price": 192.25, "name": "Heidelberg Materials", "industry": "Materials"},
    {"symbol": "EXV1.DE", "quantity": 284.0, "price": 27.83, "name": "Index Fund", "industry": "European Banks"},
    {"symbol": "URTH", "quantity": 493.0, "price": 100.48, "name": "Index Fund", "industry": "Index"},
    {"symbol": "DAX", "quantity": 60.0, "price": 217.75, "name": "Index Fund", "industry": "DAX"},
    {"symbol": "PLTR", "quantity": 85.0, "price": 113.08, "name": "Palantir", "industry": "Software"},
    {"symbol": "SHEL", "quantity": 74.0, "price": 30.61, "name": "Shell", "industry": "Oil & Gas"},
    {"symbol": "WFC", "quantity": 340.0, "price": 70.36, "name": "Wells Fargo", "industry": "Bank"},
    {"symbol": "3BAL.L", "quantity": 7.5, "price": 29.70, "name": "Index Fund", "industry": "European Banks"},
    {"symbol": "DBPG.DE", "quantity": 47.0, "price": 212.65, "name": "Index Fund", "industry": "Index"},
    {"symbol": "GS", "quantity": 8.0, "price": 608.10, "name": "Goldman Sachs", "industry": "Bank"},
    {"symbol": "LUV", "quantity": 80.0, "price": 28.79, "name": "Southwest (Airline)", "industry": "Airlines"},
    {"symbol": "UAL", "quantity": 50.0, "price": 68.92, "name": "United (Airline)", "industry": "Airlines"},
    {"symbol": "CASH", "quantity": 146858.0, "price": 1.00, "name": "Cash", "industry": None}
]
