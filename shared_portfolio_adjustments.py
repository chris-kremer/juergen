"""Confirmed USD purchases outside the historical EUR custody checkpoint.

This is an incremental pooled-cash correction, NOT a dollar-account balance.
No execution dates, account numbers, purchase-date EUR basis or fees are inferred.
"""
import copy
from decimal import Decimal

# Observed Yahoo EURUSD=X daily bar, retrieved 2026-11-23. Valuation reference
# only (bar timestamp is not a transaction timestamp or exact FX trade time).
REFERENCE_EURUSD = 1.0905125141143799
REFERENCE_FX_DATE = '2026-11-23'
ADJUSTMENT_ID = 'shared-ant-skhy-usd-funded-v1'
SHARED_USD_LOTS = [
    {'id': 'skhy-screenshot-26.57988951', 'symbol': 'SKHY', 'quantity': 26.57988951,
     'gross_cost_usd': 2999.93, 'execution_price_usd': None, 'execution_date': None, 'fees_usd': None},
    {'id': 'ant-screenshot-34.46621678', 'symbol': 'ANT', 'quantity': 34.46621678,
     'gross_cost_usd': 2999.93, 'execution_price_usd': None, 'execution_date': None, 'fees_usd': None},
    {'id': 'ant-screenshot-37.56056232', 'symbol': 'ANT', 'quantity': 37.56056232,
     'gross_cost_usd': 2999.93, 'execution_price_usd': None, 'execution_date': None, 'fees_usd': None},
    {'id': 'ant-ipo-22-at-83', 'symbol': 'ANT', 'quantity': 22,
     'gross_cost_usd': 1826.0, 'execution_price_usd': 83.0, 'execution_date': None,
     'reported_date': '2026-11-19', 'fees_usd': None},
]


def apply_shared_usd_purchases(stocks):
    """Return a copy with one idempotent gross-cost internal swap applied.

    CASH.quantity remains the legacy EUR checkpoint amount for compatibility;
    CASH.price/current_price is an aggregation factor, not an FX quote or a
    broker cash unit. Consumers must use quantity * price, never quantity alone.
    History ignores this correction until execution dates can be established.
    """
    result = copy.deepcopy(stocks)
    cash = next(s for s in result if s.get('symbol') == 'CASH')
    if cash.get('shared_adjustment_id') == ADJUSTMENT_ID:
        return result
    if any(s.get('symbol') in ('ANT', 'SKHY') for s in result):
        raise ValueError('ANT/SKHY already present without the matching cash correction')
    total = sum(Decimal(str(lot['gross_cost_usd'])) for lot in SHARED_USD_LOTS)
    cash['native_cash_adjustments'] = [{
        'id': ADJUSTMENT_ID, 'currency': 'USD', 'amount': float(-total),
        'account_id': None, 'opening_balance': None, 'execution_date': None,
        'type': 'incremental_correction_not_broker_balance',
    }]
    cash['shared_adjustment_id'] = ADJUSTMENT_ID
    cash['historical_price'] = cash['price']
    cash['unadjusted_value_eur'] = cash['value_eur']
    cash['value_eur'] -= float(total) / REFERENCE_EURUSD
    cash['price'] = cash['value_eur'] / cash['quantity']
    cash['cost_basis_eur'] = cash['value_eur']
    cash['valuation_note'] = 'Pooled cash less native USD incremental correction; dollar opening balance unknown, not negative broker cash'
    for symbol, name, isin, industry in [
        ('SKHY', 'SK hynix', None, 'Semiconductors'),
        ('ANT', 'Anthropic Class A', 'US03703U1079', 'Software'),
    ]:
        lots = [lot for lot in SHARED_USD_LOTS if lot['symbol'] == symbol]
        quantity = float(sum(Decimal(str(lot['quantity'])) for lot in lots))
        cost = float(sum(Decimal(str(lot['gross_cost_usd'])) for lot in lots))
        value = cost / REFERENCE_EURUSD
        result.append({
            'isin': isin, 'wkn': None, 'symbol': symbol, 'name': name,
            'industry': industry, 'quantity': quantity, 'quote_currency': 'USD',
            'quote_multiplier': 1.0, 'cost_basis_usd': cost,
            'cost_basis_eur': None, 'value_eur': value, 'price': value / quantity,
            'account_quantities': {}, 'acquisition_date': None, 'fees_usd': None,
            'history_policy': 'exclude_unknown_execution_date',
            'shared_adjustment_id': ADJUSTMENT_ID, 'lots': copy.deepcopy(lots),
            'valuation_note': 'Gross USD acquisition-cost fallback at common valuation FX; not historical EUR basis',
        })
    return result
