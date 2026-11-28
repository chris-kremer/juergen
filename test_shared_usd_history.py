"""Keep unknown-date USD additions outside historical return/tax claims."""
from datetime import datetime
import pandas as pd
import pytest
import config
import portfolio_dashboard as dashboard
import report_generator
from price_fetcher import PriceFetcher


def test_historical_dates_preserve_pre_correction_scope(monkeypatch):
    legacy = config._aggregate_stocks(config.PORTFOLIO_ACCOUNTS)
    baseline = sum(s['value_eur'] for s in legacy)
    monkeypatch.setattr(dashboard, 'fetch_stock_history_eur', lambda *a, **kw: pd.DataFrame())
    view = dashboard.PortfolioDashboard(PriceFetcher())
    date = datetime(2026, 1, 2)
    assert view._get_portfolio_value_at_date(date, config.STOCKS) == pytest.approx(baseline)
    value, _ = view._get_single_date_data(date, {'username': 'user'})
    assert value == pytest.approx(baseline)


def test_report_does_not_backfill_unknown_acquisitions(monkeypatch):
    generator = report_generator.AnnualReportGenerator(PriceFetcher())
    position = next(s for s in config.STOCKS if s['symbol'] == 'ANT')
    monkeypatch.setattr(report_generator, 'fetch_stock_history_eur', lambda *a, **kw: pd.DataFrame())
    series = generator._get_price_series(position, datetime(2025, 1, 1), datetime(2025, 1, 3), position['price'])
    assert series.eq(0).all()


def test_report_context_preserves_legacy_cash_and_excludes_new_positions(monkeypatch):
    generator = report_generator.AnnualReportGenerator(PriceFetcher())
    monkeypatch.setattr(report_generator, 'fetch_stock_history_eur', lambda *a, **kw: pd.DataFrame())
    monkeypatch.setattr(generator, '_build_monthly_returns', lambda *a, **kw: pd.DataFrame())
    legacy = config._aggregate_stocks(config.PORTFOLIO_ACCOUNTS)
    monkeypatch.setattr(report_generator, 'STOCKS', legacy)
    before = generator._build_report_context({'username': 'user'}, legacy, 2025)
    monkeypatch.setattr(report_generator, 'STOCKS', config.STOCKS)
    after = generator._build_report_context({'username': 'user'}, config.STOCKS, 2025)
    pd.testing.assert_series_equal(before['user_series'], after['user_series'])
    assert not {'ANT', 'SKHY'} & set(after['breakdown']['Symbol'])
    assert 'unknown execution dates' in after['history_scope_note']


def test_unknown_eur_basis_is_not_silently_taxed_as_zero_or_fabricated():
    position = next(s for s in config.STOCKS if s['symbol'] == 'ANT')
    assert position['cost_basis_eur'] is None
    with pytest.raises(ValueError, match='EUR acquisition basis'):
        dashboard.calculate_tax_simulation([position])


def test_heatmap_uses_disclosed_usd_return_at_valuation_fx():
    position = next(s.copy() for s in config.STOCKS if s['symbol'] == 'ANT')
    position.update(current_price=100 / 1.25, valuation_fx_rate=1/1.25)
    row = dashboard.build_portfolio_heatmap_rows([position], color_mode='since_purchase')[0]
    assert row['performance_pct'] == pytest.approx((94.02677910 * 100 / 7825.86 - 1) * 100)
    assert row['performance_basis'] == 'USD cost at valuation FX, not historical EUR return'


def test_tax_view_discloses_unknown_basis_instead_of_crashing(monkeypatch):
    messages = []
    monkeypatch.setattr(dashboard.st, 'subheader', lambda *a, **kw: None)
    monkeypatch.setattr(dashboard.st, 'caption', lambda *a, **kw: None)
    monkeypatch.setattr(dashboard.st, 'info', lambda message: messages.append(message))
    monkeypatch.setattr(dashboard.st, 'radio', lambda *a, **kw: pytest.fail('Must stop before tax controls'))
    dashboard.PortfolioDashboard(PriceFetcher()).show_tax_overview(config.STOCKS, {'username': 'user'}, 'en')
    assert messages and 'EUR acquisition basis' in messages[0]
