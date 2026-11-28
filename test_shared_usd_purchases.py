"""USD-funded incremental correction, not a synthetic negative broker balance."""
import copy
from decimal import Decimal
import pandas as pd
import pytest
import config
import price_fetcher
from price_fetcher import PriceFetcher, fetch_stock_history_eur


def added():
    return [s for s in config.STOCKS if s.get('symbol') in ('ANT', 'SKHY', 'CASH')]


def test_confirmed_shared_positions_and_exact_native_cash():
    positions = {s['symbol']: s for s in added()}
    assert set(positions) == {'ANT', 'SKHY', 'CASH'}
    assert positions['ANT']['quantity'] == 94.02677910
    assert positions['SKHY']['quantity'] == 26.57988951
    assert positions['ANT']['cost_basis_usd'] == 7825.86
    assert positions['SKHY']['cost_basis_usd'] == 2999.93
    adjustments = positions['CASH']['native_cash_adjustments']
    assert sum(Decimal(str(a['amount'])) for a in adjustments) == Decimal('-10825.79')
    assert all(a['currency'] == 'USD' and a['account_id'] is None for a in adjustments)
    assert all(a['opening_balance'] is None for a in adjustments)
    assert all(s['acquisition_date'] is None for s in positions.values() if s['symbol'] != 'CASH')
    assert [a['cash_balance_eur'] for a in config.PORTFOLIO_ACCOUNTS] == [70178.26, 27298.92]
    assert positions['CASH']['quantity'] == 93477.18
    assert sum(s['value_eur'] for s in config.STOCKS) == pytest.approx(481045.10)


def test_ipo_counted_once_and_reapplying_is_idempotent():
    from shared_portfolio_adjustments import apply_shared_usd_purchases, SHARED_USD_LOTS
    lots = [lot for lot in SHARED_USD_LOTS if lot['id'] == 'ant-ipo-22-at-83']
    assert len(lots) == 1
    assert lots[0]['quantity'] == 22
    assert lots[0]['execution_price_usd'] == 83
    assert all(lot['execution_date'] is None and lot['fees_usd'] is None for lot in SHARED_USD_LOTS)
    assert apply_shared_usd_purchases(copy.deepcopy(config.STOCKS)) == config.STOCKS
    assert len({lot['id'] for lot in SHARED_USD_LOTS}) == 4


@pytest.mark.parametrize('eurusd', [1.10, 1.25])
@pytest.mark.parametrize('missing_quotes', [False, True])
def test_live_common_fx_and_gross_cost_fallback(monkeypatch, eurusd, missing_quotes):
    idx = pd.DatetimeIndex(['2026-11-20', '2026-11-23'])
    positions = {s['symbol']: s for s in added()}
    def history(symbol, **kwargs):
        if symbol == 'EURUSD=X':
            return pd.DataFrame({'Close': [1.2, eurusd]}, index=idx)
        if missing_quotes:
            return pd.DataFrame()
        # Price observation is older than latest FX: current valuation still uses common latest FX.
        return pd.DataFrame({'Close': [100.0]}, index=idx[:1])
    monkeypatch.setattr(price_fetcher, 'fetch_yfinance_history', history)
    result, failed = PriceFetcher().fetch_stock_prices(added(), show_progress=False)
    by_symbol = {s['symbol']: s for s in result}
    cash = PriceFetcher().get_stock_value(by_symbol['CASH'])
    assert cash == pytest.approx(93477.18 - 10825.79 / eurusd)
    assert by_symbol['CASH']['valuation_fx_rate'] == pytest.approx(1 / eurusd)
    total = PriceFetcher().get_portfolio_value(result)
    gain_usd = 0 if missing_quotes else sum(s['quantity'] * 100 - s['cost_basis_usd'] for s in positions.values() if s['symbol'] != 'CASH')
    assert total == pytest.approx(93477.18 + gain_usd / eurusd)
    assert set(failed) == ({'ANT', 'SKHY'} if missing_quotes else set())
    for symbol in ('ANT', 'SKHY'):
        assert by_symbol[symbol]['valuation_fx_rate'] == pytest.approx(1 / eurusd)
        assert by_symbol[symbol]['price_source'] == ('acquisition_cost' if missing_quotes else 'live')


def test_missing_fx_uses_one_disclosed_reference_for_entire_correction(monkeypatch):
    monkeypatch.setattr(price_fetcher, 'fetch_yfinance_history', lambda *a, **kw: pd.DataFrame())
    result, failed = PriceFetcher().fetch_stock_prices(added(), show_progress=False)
    assert PriceFetcher().get_portfolio_value(result) == pytest.approx(93477.18)
    assert 'EURUSD=X' in failed
    assert all(s['fx_source'] == 'reference_fallback' for s in result)


def test_new_stakes_have_no_fabricated_acquisition_history(monkeypatch):
    def unexpected(*a, **kw):
        pytest.fail('Unknown execution dates must not request historical security prices')
    monkeypatch.setattr(price_fetcher, 'fetch_yfinance_history', unexpected)
    for stock in added():
        if stock['symbol'] != 'CASH':
            assert fetch_stock_history_eur(stock, period='1y').empty


def test_pending_evidence_points_to_canonical_lot_not_another_purchase():
    import json
    from pathlib import Path
    root = Path(__file__).parent
    ipo = json.loads((root / 'pending-trades/anthropic-2026-11-19.json').read_text())
    shared = json.loads((root / 'pending-trades/shared-ant-skhy-reconciliation.json').read_text())
    assert ipo['status'] == 'reconciled_into_shared_portfolio'
    assert ipo['canonical_lot_id'] == 'ant-ipo-22-at-83'
    assert ipo['execution_date'] is None
    assert shared['status'] == 'applied_incremental_usd_cash_correction'
    assert shared['cash_adjustment_usd'] == -10825.79
    assert shared['account_id'] is None


def test_ownership_configuration_unchanged():
    # Config correction must be an internal asset swap, never an ownership event.
    import ast
    import subprocess
    old = ast.parse(subprocess.check_output(['git', 'show', 'HEAD:config.py'], text=True))
    new = ast.parse(open('config.py').read())
    def users(tree):
        return ast.dump(next(n.value for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'USERS' for t in n.targets)))
    assert users(old) == users(new)
