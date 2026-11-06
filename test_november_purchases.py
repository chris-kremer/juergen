"""Confirmed broker purchases: legal units, account cash, and pending-order isolation."""
import unittest
from decimal import Decimal as D
import config


class NovemberPurchases(unittest.TestCase):
    def test_executed_holdings_and_cash(self):
        accounts = {a['account_id']: a for a in config.PORTFOLIO_ACCOUNTS}
        expected = [('1182076586', 'US7960502018', 2, 5894.98),
                    ('1183194735', 'US5951121038', 6, 4344.71),
                    ('1182076586', 'US67066G1040', 15, 2496.00)]
        for account, isin, units, basis in expected:
            h = next(h for h in accounts[account]['holdings'] if h['isin'] == isin)
            self.assertEqual(h['quantity'], units)
            self.assertEqual(h['cost_basis_eur'], basis)
            self.assertEqual(h['value_eur'], basis)  # cost fallback, not a claimed current mark
        self.assertEqual(accounts['1182076586']['cash_balance_eur'], 70178.26)
        self.assertEqual(accounts['1183194735']['cash_balance_eur'], 30348.92)
        cash = next(s for s in config.STOCKS if s['symbol'] == 'CASH')
        self.assertEqual(D(str(cash['quantity'])).quantize(D('.01')), D('96527.18'))

    def test_trade_evidence_preserves_known_and_unknown_amounts(self):
        buys = [t for t in config.EXECUTED_TRADES if t['side'] == 'buy']
        self.assertEqual(len(buys), 3)
        samsung, micron, nvidia = sorted(buys, key=lambda t: t['date'])
        self.assertEqual((samsung['quantity'], samsung['cash_debit_eur']), (2, 5894.98))
        self.assertEqual((micron['quantity'], micron['cash_debit_eur']), (6, 4344.71))
        self.assertIsNone(samsung['execution_price_eur'])
        self.assertIsNone(micron['execution_price_eur'])
        self.assertEqual(nvidia['execution_price_eur'], 166.4)
        self.assertEqual(nvidia['gross_cost_eur'], 2496)
        self.assertIsNone(nvidia['fees_eur'])
        self.assertTrue(nvidia['cash_debit_is_provisional'])
        self.assertEqual(sum(D(str(t['cash_debit_eur'])) for t in buys), D('12735.69'))

    def test_gdr_and_pending_order_are_not_underlying_or_executed_units(self):
        samsung = next(s for s in config.STOCKS if s['isin'] == 'US7960502018')
        self.assertEqual((samsung['symbol'], samsung['quote_currency']), ('SSUN.F', 'EUR'))
        self.assertEqual(samsung['underlying_shares_per_receipt'], 25)
        self.assertEqual(samsung.get('quote_multiplier', 1), 1)
        self.assertEqual(len(config.OPEN_ORDERS), 1)
        order = config.OPEN_ORDERS[0]
        self.assertEqual((order['account_id'], order['symbol'], order['quantity'], order['status']),
                         ('1183194735', 'MU', 5, 'open'))
        self.assertEqual(next(s['quantity'] for s in config.STOCKS if s['symbol'] == 'MU'), 6)

    def test_internal_asset_swap_does_not_invent_loss_or_change_ownership(self):
        self.assertEqual(config.ASSET_RECONCILIATION['total_assets_eur'], 481045.10)
        self.assertEqual(config.ASSET_RECONCILIATION['as_of'], '2026-09-22')
        self.assertEqual(config.HOLDINGS_UPDATED_DATE, '2026-11-06')
        self.assertAlmostEqual(sum(u['portfolio_percentage'] for u in config.USERS if u['username'] != 'user'), 1)


if __name__ == '__main__':
    unittest.main()
