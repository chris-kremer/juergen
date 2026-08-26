"""Ownership-unit ledger for the shared portfolio.

The 2026-08-11 checkpoint is authoritative. Earlier cash movements are not used
to synthesize unit prices because the available cash histories do not contain a
complete historical depot composition. New events can be added after the
checkpoint with an explicit pre-flow unit price.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Dict, Iterable, Optional


OWNERSHIP_CHECKPOINT = {
    "as_of": "2026-08-11",
    "unit_price_eur": Decimal("1.00"),
    "balances": {
        "foehr": Decimal("45359.85"),
        "kremer": Decimal("259037.80"),
        "annika": Decimal("2270.44"),
        "juergen": Decimal("117539.77"),
        "christian": Decimal("68128.67"),
    },
}

# Add only events after the checkpoint. Supported event types:
# - contribution/withdrawal: owner, cash_eur, unit_price_eur
# - transfer: from_owner, to_owner, units
OWNERSHIP_EVENTS = [
    {
        "date": "2026-08-26",
        "type": "transfer",
        "from_owner": "christian",
        "to_owner": "annika",
        "units": Decimal("50.695022"),
        "unit_price_eur": Decimal("0.9862901359026294"),
        "cash_reference_eur": Decimal("50.00"),
        "note": "Ownership transfer valued at the live portfolio NAV",
    },
]

# Audit findings from the two supplied cash-history exports. These items explain
# what can and cannot safely be reconstructed before the opening checkpoint.
HISTORICAL_RECONCILIATION = {
    "confirmed_external_contributions": [
        {"owner": "juergen", "date": "2025-07-03", "cash_eur": 50000.00},
        {"owner": "juergen", "date": "2026-01-05", "cash_eur": 35000.00},
        {"owner": "juergen", "date": "2026-01-06", "cash_eur": 15000.00},
    ],
    "confirmed_internal_transfers": [
        {"from_owner": "christian", "to_owner": "foehr", "cash_reference_eur": 6000.00},
        {"from_owner": "christian", "to_owner": "annika", "cash_reference_eur": 464.26},
    ],
    "unresolved_bank_flows": [
        {"owner_hint": "kremer", "direction": "in", "cash_eur": 35000.00},
        {"owner_hint": "christian", "direction": "in", "cash_eur": 35000.00},
        {"owner_hint": "christian", "direction": "out", "cash_eur": 38800.00},
    ],
    "reason_not_backfilled": (
        "Cash histories do not provide complete historical depot quantities or "
        "portfolio NAVs, so pre-checkpoint unit prices cannot be established reliably."
    ),
}


def _decimal(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def get_unit_balances(
    as_of: Optional[str] = None,
    events: Optional[Iterable[Dict]] = None,
) -> Dict[str, Decimal]:
    """Return owner unit balances after applying eligible post-checkpoint events."""
    balances = dict(OWNERSHIP_CHECKPOINT["balances"])
    effective_events = OWNERSHIP_EVENTS if events is None else list(events)

    for event in sorted(effective_events, key=lambda item: item["date"]):
        if event["date"] <= OWNERSHIP_CHECKPOINT["as_of"]:
            raise ValueError("Ownership events must be after the opening checkpoint")
        if as_of is not None and event["date"] > as_of:
            continue

        event_type = event["type"]
        if event_type in {"contribution", "withdrawal"}:
            owner = event["owner"]
            unit_price = _decimal(event["unit_price_eur"])
            cash_eur = _decimal(event["cash_eur"])
            if unit_price <= 0 or cash_eur <= 0:
                raise ValueError("Cash and unit price must be positive")
            units = cash_eur / unit_price
            balances[owner] += units if event_type == "contribution" else -units
        elif event_type == "transfer":
            units = _decimal(event["units"])
            if units <= 0:
                raise ValueError("Transferred units must be positive")
            balances[event["from_owner"]] -= units
            balances[event["to_owner"]] += units
        else:
            raise ValueError(f"Unsupported ownership event type: {event_type}")

        if any(balance < 0 for balance in balances.values()):
            raise ValueError("Ownership event would create a negative unit balance")

    return balances


def get_total_units(as_of: Optional[str] = None) -> Decimal:
    return sum(get_unit_balances(as_of=as_of).values(), Decimal("0"))


def get_ownership_percentage(username: str, as_of: Optional[str] = None) -> float:
    """Return a unit-derived ownership fraction; the admin overview owns 100%."""
    if username == "user":
        return 1.0
    balances = get_unit_balances(as_of=as_of)
    total_units = sum(balances.values(), Decimal("0"))
    if username not in balances or total_units <= 0:
        return 0.0
    return float(balances[username] / total_units)


def get_unit_price(total_portfolio_value_eur, as_of: Optional[str] = None) -> Decimal:
    total_units = get_total_units(as_of=as_of)
    if total_units <= 0:
        return Decimal("0")
    return _decimal(total_portfolio_value_eur) / total_units


def get_user_portfolio_value(
    username: str,
    total_portfolio_value_eur,
    as_of: Optional[str] = None,
) -> float:
    """Value a user's units at the portfolio's current unit price."""
    if username == "user":
        return float(total_portfolio_value_eur)
    balances = get_unit_balances(as_of=as_of)
    if username not in balances:
        return 0.0
    return float(balances[username] * get_unit_price(total_portfolio_value_eur, as_of))


def get_ownership_snapshot(total_portfolio_value_eur, as_of: Optional[str] = None):
    balances = get_unit_balances(as_of=as_of)
    unit_price = get_unit_price(total_portfolio_value_eur, as_of=as_of)
    total_units = sum(balances.values(), Decimal("0"))
    return {
        username: {
            "units": float(units),
            "percentage": float(units / total_units),
            "value_eur": float(units * unit_price),
        }
        for username, units in balances.items()
    }
