from decimal import Decimal

import pytest

from ownership import (
    HISTORICAL_RECONCILIATION,
    OWNERSHIP_CHECKPOINT,
    get_ownership_percentage,
    get_ownership_snapshot,
    get_total_units,
    get_unit_balances,
    get_unit_price,
)


def test_checkpoint_units_reconcile_exactly_to_attributed_assets():
    assert get_total_units() == Decimal("492336.53")
    assert sum(get_unit_balances().values()) == Decimal("492336.53")
    assert OWNERSHIP_CHECKPOINT["unit_price_eur"] == Decimal("1.00")


def test_unit_derived_percentages_sum_to_exactly_one():
    owners = list(OWNERSHIP_CHECKPOINT["balances"])
    assert sum(get_ownership_percentage(owner) for owner in owners) == pytest.approx(
        1.0,
        abs=1e-15,
    )


def test_checkpoint_values_equal_unit_balances_at_one_euro_nav():
    snapshot = get_ownership_snapshot(492336.53)
    for username, expected_units in OWNERSHIP_CHECKPOINT["balances"].items():
        assert snapshot[username]["units"] == pytest.approx(float(expected_units))
        assert snapshot[username]["value_eur"] == pytest.approx(float(expected_units))


def test_current_values_revalue_without_changing_ownership_percentages():
    total_value = Decimal("510000.00")
    snapshot = get_ownership_snapshot(total_value)
    assert get_unit_price(total_value) == total_value / Decimal("492336.53")
    assert sum(owner["value_eur"] for owner in snapshot.values()) == pytest.approx(
        float(total_value)
    )


def test_post_checkpoint_transfer_moves_units_without_changing_total():
    events = [{
        "date": "2026-08-12",
        "type": "transfer",
        "from_owner": "christian",
        "to_owner": "annika",
        "units": "100.00",
    }]
    balances = get_unit_balances(events=events)
    assert balances["christian"] == Decimal("68028.67")
    assert balances["annika"] == Decimal("2370.44")
    assert sum(balances.values()) == Decimal("492336.53")


def test_post_checkpoint_contribution_issues_units_at_explicit_nav():
    events = [{
        "date": "2026-08-12",
        "type": "contribution",
        "owner": "foehr",
        "cash_eur": "500.00",
        "unit_price_eur": "1.25",
    }]
    balances = get_unit_balances(events=events)
    assert balances["foehr"] == Decimal("45759.85")
    assert sum(balances.values()) == Decimal("492736.53")


def test_historical_reconciliation_keeps_unresolved_flows_out_of_units():
    confirmed_juergen = sum(
        Decimal(str(item["cash_eur"]))
        for item in HISTORICAL_RECONCILIATION["confirmed_external_contributions"]
        if item["owner"] == "juergen"
    )
    assert confirmed_juergen == Decimal("100000.0")
    assert HISTORICAL_RECONCILIATION["unresolved_bank_flows"]
