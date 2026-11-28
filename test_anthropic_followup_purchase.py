from decimal import Decimal
import copy
import config
from shared_portfolio_adjustments import SHARED_USD_LOTS, apply_shared_usd_purchases


def test_additional_confirmed_ant_lot_is_applied_once():
    lots = [lot for lot in SHARED_USD_LOTS if lot['id'] == 'ant-screenshot-37.56056232']
    assert len(lots) == 1
    assert Decimal(str(lots[0]['quantity'])) == Decimal('37.56056232')
    assert Decimal(str(lots[0]['gross_cost_usd'])) == Decimal('2999.93')
    assert lots[0]['execution_date'] is None
    positions = {s['symbol']: s for s in config.STOCKS}
    assert Decimal(str(positions['ANT']['quantity'])) == Decimal('94.02677910')
    assert Decimal(str(positions['ANT']['cost_basis_usd'])) == Decimal('7825.86')
    assert sum(Decimal(str(a['amount'])) for a in positions['CASH']['native_cash_adjustments']) == Decimal('-10825.79')
    assert apply_shared_usd_purchases(copy.deepcopy(config.STOCKS)) == config.STOCKS
