import pandas as pd
import pytest

import price_fetcher
from config import (
    ASSET_RECONCILIATION,
    EXECUTED_TRADES,
    PORTFOLIO_ACCOUNTS,
    STOCKS,
    USERS,
)
from price_fetcher import (
    PriceFetcher,
    convert_history_to_eur,
    get_return_base_price_eur,
)


def _position(isin):
    return next(stock for stock in STOCKS if stock["isin"] == isin)


def test_account_and_portfolio_snapshot_totals_reconcile():
    account_totals = {
        account["account_id"]: round(
            account["cash_balance_eur"]
            + sum(
                holding.get("broker_value_eur", holding["value_eur"])
                for holding in account["holdings"]
            ),
            2,
        )
        for account in PORTFOLIO_ACCOUNTS
    }

    assert account_totals == {
        "1182076586": 347300.06,
        "1183194735": 143153.70,
    }
    assert ASSET_RECONCILIATION == {
        "as_of": "2026-08-26",
        "broker_reported_assets_eur": 490453.76,
        "confirmed_cash_withdrawal_eur": 4000.0,
        "valuation_adjustments_eur": -94.0,
        "total_assets_eur": 486359.76,
        "attributed_assets_eur": 486359.76,
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
    assert _position("IE00BLS09N40")["quantity"] == pytest.approx(434.0)
    assert _position("LU0256839274")["quantity"] == pytest.approx(6.301)

    assert _position("IE00B4L5Y983")["account_quantities"] == {
        "1182076586": 734.876,
        "1183194735": 117.299,
    }
    assert _position("IE00BLS09N40")["account_quantities"] == {
        "1182076586": 364.0,
        "1183194735": 70.0,
    }


def test_executed_3bal_sale_is_auditable_and_uses_fifo_remaining_basis():
    assert EXECUTED_TRADES == [
        {
            "date": "2026-08-26",
            "account_id": "1182076586",
            "isin": "IE00BLS09N40",
            "symbol": "3BAL.L",
            "side": "sale",
            "quantity": 214.0,
            "execution_price_eur": 100.02,
            "gross_proceeds_eur": 21404.28,
            "net_cash_proceeds_eur": 15699.17,
            "basis_method": "FIFO",
            "source_note": "User-confirmed executed order and post-trade cash balance",
        }
    ]

    account = next(
        account
        for account in PORTFOLIO_ACCOUNTS
        if account["account_id"] == "1182076586"
    )
    holding = next(
        holding for holding in account["holdings"] if holding["isin"] == "IE00BLS09N40"
    )
    assert account["cash_balance_eur"] == pytest.approx(48180.73 + 15699.17)
    assert holding["quantity"] == pytest.approx(364.0)
    assert holding["cost_basis_eur"] == pytest.approx(3161.55)
    assert holding["value_eur"] == pytest.approx(364 * 100.02)


def test_fallback_prices_are_eur_per_legal_unit():
    for stock in STOCKS:
        assert stock["quantity"] * stock["price"] == pytest.approx(
            stock["value_eur"], abs=0.005
        )

    assert _position("US84615Q1031")["symbol"] == "SPCX"
    assert _position("US84615Q1031")["return_reference_price_eur"] == pytest.approx(
        3275.00 / 28.0
    )
    assert _position("DE0006062144")["price"] == pytest.approx(59.46)
    assert _position("DE0006062144")["price_mode"] == "fixed"
    assert not any(stock["isin"] == "US3682872078" for stock in STOCKS)


def test_fixed_corporate_action_is_not_reported_as_failed_live_price():
    covestro = _position("DE0006062144")
    updated, failed = PriceFetcher().fetch_stock_prices(
        [covestro],
        show_progress=False,
    )

    assert failed == []
    assert updated[0]["price_source"] == "fixed"
    assert updated[0]["current_price"] == pytest.approx(59.46)


def test_current_prices_skip_nan_latest_close(monkeypatch):
    history = pd.DataFrame(
        {"Close": [100.0, 105.0, float("nan")]},
        index=pd.DatetimeIndex(["2026-08-10", "2026-08-11", "2026-08-12"]),
    )
    stock = {
        "symbol": "TEST",
        "quantity": 2.0,
        "price": 90.0,
        "quote_currency": "EUR",
    }
    monkeypatch.setattr(price_fetcher, "fetch_stock_history_eur", lambda *args, **kwargs: history)

    updated, failed = PriceFetcher().fetch_stock_prices([stock], show_progress=False)

    assert failed == []
    assert updated[0]["current_price"] == pytest.approx(105.0)
    assert updated[0]["previous_close"] == pytest.approx(100.0)


def test_portfolio_calculations_fall_back_from_non_finite_prices():
    stock = {
        "symbol": "TEST",
        "quantity": 2.0,
        "price": 90.0,
        "current_price": float("nan"),
        "previous_close": float("nan"),
    }
    fetcher = PriceFetcher()

    assert fetcher.get_portfolio_value([stock]) == pytest.approx(180.0)
    assert fetcher.get_stock_value(stock) == pytest.approx(180.0)
    assert fetcher.get_daily_change_percentage(stock) == 0.0
    assert fetcher.get_user_daily_change_value(stock, 0.5) == 0.0


def test_cached_non_finite_quote_is_sanitized_before_dashboard_use():
    stock = {
        "symbol": "TEST",
        "name": "Test Security",
        "quantity": 2.0,
        "price": 90.0,
        "current_price": float("nan"),
        "previous_close": float("nan"),
        "price_source": "live",
    }

    sanitized, repaired = PriceFetcher().sanitize_stock_prices([stock])

    assert repaired == ["TEST"]
    assert sanitized[0]["current_price"] == 90.0
    assert sanitized[0]["previous_close"] == 90.0
    assert sanitized[0]["price_source"] == "default"


def test_spacex_uses_ipo_price_when_history_contains_listing_date():
    spacex = _position("US84615Q1031")
    history = pd.DataFrame(
        {"Close": [120.0, 125.0]},
        index=pd.DatetimeIndex(["2026-06-12", "2026-06-15"]),
    )
    assert get_return_base_price_eur(spacex, history) == pytest.approx(3275 / 28)


def test_spacex_uses_period_start_after_ipo_date():
    spacex = _position("US84615Q1031")
    history = pd.DataFrame(
        {"Close": [130.0, 125.0]},
        index=pd.DatetimeIndex(["2026-07-01", "2026-07-02"]),
    )
    assert get_return_base_price_eur(spacex, history) == pytest.approx(130.0)


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
