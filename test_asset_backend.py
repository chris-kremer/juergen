import pandas as pd
import pytest

import price_fetcher
from config import ASSET_RECONCILIATION, PORTFOLIO_ACCOUNTS, STOCKS, USERS
from price_fetcher import convert_history_to_eur


def _position(isin):
    return next(stock for stock in STOCKS if stock["isin"] == isin)


def test_account_and_portfolio_snapshot_totals_reconcile():
    account_totals = {
        account["account_id"]: round(
            account["cash_balance_eur"]
            + sum(holding["value_eur"] for holding in account["holdings"]),
            2,
        )
        for account in PORTFOLIO_ACCOUNTS
    }

    assert account_totals == {
        "1182076586": 353276.83,
        "1183194735": 143153.70,
    }
    assert ASSET_RECONCILIATION == {
        "as_of": "2026-08-11",
        "broker_reported_assets_eur": 496430.53,
        "pending_cash_withdrawal_eur": 4000.0,
        "total_assets_eur": 492430.53,
        "attributed_assets_eur": 492430.53,
        "other_overhang_eur": 0.0,
    }


def test_owner_percentages_reconcile_to_exactly_one_hundred_percent():
    owner_percentages = [
        user["portfolio_percentage"]
        for user in USERS
        if user["username"] != "user"
    ]
    assert sum(owner_percentages) == pytest.approx(1.0, abs=1e-12)


def test_combined_positions_keep_legal_share_counts_and_account_attribution():
    assert _position("IE00B4L5Y983")["quantity"] == pytest.approx(852.175)
    assert _position("US1729674242")["quantity"] == pytest.approx(340.0)
    assert _position("IE00BLS09N40")["quantity"] == pytest.approx(648.0)
    assert _position("LU0256839274")["quantity"] == pytest.approx(6.301)

    assert _position("IE00B4L5Y983")["account_quantities"] == {
        "1182076586": 734.876,
        "1183194735": 117.299,
    }
    assert _position("IE00BLS09N40")["account_quantities"] == {
        "1182076586": 578.0,
        "1183194735": 70.0,
    }


def test_fallback_prices_are_eur_per_legal_unit():
    for stock in STOCKS:
        assert stock["quantity"] * stock["price"] == pytest.approx(
            stock["value_eur"], abs=0.005
        )

    # SpaceX is a private holding. It must never be priced from the unrelated
    # exchange-traded SPCX ticker.
    assert _position("US84615Q1031")["symbol"] is None


def test_usd_history_is_converted_to_eur(monkeypatch):
    index = pd.DatetimeIndex(["2026-08-10", "2026-08-11"])
    security_history = pd.DataFrame({"Close": [100.0, 110.0]}, index=index)
    fx_history = pd.DataFrame({"Close": [1.25, 1.10]}, index=index)

    monkeypatch.setattr(
        price_fetcher,
        "fetch_yfinance_history",
        lambda symbol, **kwargs: fx_history if symbol == "EURUSD=X" else pd.DataFrame(),
    )

    converted = convert_history_to_eur(
        {"quote_currency": "USD"}, security_history, period="5d"
    )
    assert converted["Close"].tolist() == pytest.approx([80.0, 100.0])


def test_gbp_pence_history_is_converted_to_eur(monkeypatch):
    index = pd.DatetimeIndex(["2026-08-10", "2026-08-11"])
    security_history = pd.DataFrame({"Close": [10000.0, 10100.0]}, index=index)
    fx_history = pd.DataFrame({"Close": [1.15, 1.16]}, index=index)

    monkeypatch.setattr(
        price_fetcher,
        "fetch_yfinance_history",
        lambda symbol, **kwargs: fx_history if symbol == "GBPEUR=X" else pd.DataFrame(),
    )

    converted = convert_history_to_eur(
        {"quote_currency": "GBP", "quote_multiplier": 0.01},
        security_history,
        period="5d",
    )
    assert converted["Close"].tolist() == pytest.approx([115.0, 117.16])
