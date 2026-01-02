"""
Portfolio configuration data
"""

USERS = [
    {
        "username": "user",
        "password": "password",
        "portfolio_percentage": 1.0,
        "initial_investment": 231158,
        "paid_date": "2022-01-01"
    },
    {
        "username": "foehr",
        "password": "foehr1",
        "portfolio_percentage": 0.0644741,
        "initial_investment": 20000,
        "payments": [
            {"amount": 20000, "date": "2025-07-01"},
            {"amount": 300, "date": "2025-10-01"},
            {"amount": 300, "date": "2025-11-01"},
            {"amount": 200, "date": "2025-11-01"},
            {"amount": 500, "date": "2025-12-01"},
            {"amount": 500, "date": "2026-01-01"}
        ]
    },
    {
        "username": "kremer",
        "password": "kremer1",
        "portfolio_percentage": 0.60447851,
        "initial_investment": 130000,
        "paid_date": "2022-01-01"
    },
    {
        "username": "annika",
        "password": "anakin",
        "portfolio_percentage": 0.00363834,
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
            {"amount": 100, "date": "2026-01-01"}
        ]
    },
    {
        "username": "juergen",
        "password": "juergen1",
        "portfolio_percentage": 0.14746305,
        "initial_investment": 50000,
        "paid_date": "2025-06-01"
    },
    {
        "username": "christian",
        "password": "chris1",
        "portfolio_percentage": 0.17582904,
        "initial_investment": 30000,
        "paid_date": "2022-01-01"
    }
]

STOCKS = [
    {"symbol": "UQ2B.F", "quantity": 5.4, "price": 365.00, "name": "Index Fund", "industry": "Index"},
    {"symbol": "BP", "quantity": 143.0, "price": 4.41, "name": "BP", "industry": "Oil & Gas"},
    {"symbol": "C", "quantity": 282.0, "price": 73.64, "name": "Citigroup", "industry": "Bank"},
    {"symbol": "1COV.DE", "quantity": 100.0, "price": 60.54, "name": "Covestro", "industry": "Chemicals"},
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
    {"symbol": "CASH", "quantity": 81358.0, "price": 1.00, "name": "Cash", "industry": None}
]
