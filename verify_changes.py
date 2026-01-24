"""
Verify that the changes are correct and total portfolio value is as expected
"""
from config import STOCKS, USERS

# Calculate total portfolio value
total_portfolio_value = sum(stock['quantity'] * stock['price'] for stock in STOCKS)

print("=" * 70)
print("VERIFICATION OF CHANGES")
print("=" * 70)

print(f"\nTotal Portfolio Value: €{total_portfolio_value:,.2f}")
print(f"Expected: €323,482.36")
print(f"Match: {'✓' if abs(total_portfolio_value - 323482.36) < 0.01 else '✗'}")

# Get cash position
cash = next(s['quantity'] for s in STOCKS if s['symbol'] == 'CASH')
print(f"\nCash Position: €{cash:,.2f}")
print(f"Expected: €131,358.00")
print(f"Match: {'✓' if abs(cash - 131358.0) < 0.01 else '✗'}")

# Check user percentages
print("\n" + "=" * 70)
print("USER PERCENTAGES AND VALUES")
print("=" * 70)

expected_percentages = {
    'foehr': 0.05473381,
    'kremer': 0.51315817,
    'annika': 0.00308869,
    'juergen': 0.27975331,
    'christian': 0.14926603
}

total_percentage = 0
print("\nUser | Percentage | Expected | Match | Portfolio Value")
print("-" * 70)

for user in USERS:
    if user['username'] == 'user':
        continue

    username = user['username']
    actual_pct = user['portfolio_percentage']
    expected_pct = expected_percentages.get(username, 0)
    match = '✓' if abs(actual_pct - expected_pct) < 0.00000001 else '✗'
    value = total_portfolio_value * actual_pct

    total_percentage += actual_pct

    print(f"{username:10} | {actual_pct:.8f} | {expected_pct:.8f} | {match:5} | €{value:,.2f}")

print("-" * 70)
print(f"{'TOTAL':10} | {total_percentage:.8f} | 1.00000000 | {'✓' if abs(total_percentage - 1.0) < 0.00000001 else '✗':5} | €{total_portfolio_value:,.2f}")

# Check juergen's payment record
print("\n" + "=" * 70)
print("JUERGEN'S PAYMENT RECORD")
print("=" * 70)

juergen = next(u for u in USERS if u['username'] == 'juergen')
print(f"\nInitial Investment: €{juergen['initial_investment']:,.2f}")

if 'payments' in juergen:
    print("\nPayments:")
    total_payments = 0
    for payment in juergen['payments']:
        print(f"  {payment['date']}: €{payment['amount']:,.2f}")
        total_payments += payment['amount']
    print(f"\nTotal Payments: €{total_payments:,.2f}")
    print(f"Total Investment: €{juergen['initial_investment'] + total_payments:,.2f}")
    print(f"Expected: €100,000.00")
    print(f"Match: {'✓' if abs(juergen['initial_investment'] + total_payments - 100000) < 0.01 else '✗'}")
else:
    print("\n⚠ WARNING: No payments array found for juergen!")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

all_checks_passed = (
    abs(total_portfolio_value - 323482.36) < 0.01 and
    abs(cash - 131358.0) < 0.01 and
    abs(total_percentage - 1.0) < 0.00000001 and
    all(abs(user['portfolio_percentage'] - expected_percentages.get(user['username'], 0)) < 0.00000001
        for user in USERS if user['username'] != 'user')
)

if all_checks_passed:
    print("\n✓ All checks passed! The changes are correct.")
else:
    print("\n✗ Some checks failed. Please review the changes.")

print("\nKey changes:")
print("  • Cash increased from €81,358 to €131,358 (+€50,000)")
print("  • Juergen's percentage increased from 14.75% to 27.98% (+13.23%)")
print("  • All other users were diluted proportionally")
print("  • Total portfolio value: €323,482.36")
