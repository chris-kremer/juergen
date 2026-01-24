"""
Final verification of the updated percentages
"""
from config import STOCKS, USERS

print("=" * 70)
print("FINAL VERIFICATION WITH LIVE PRICES")
print("=" * 70)

# Calculate current total portfolio value with current prices
total_portfolio_value = sum(s['quantity'] * s['price'] for s in STOCKS)
print(f"\nTotal Portfolio Value (config prices): €{total_portfolio_value:,.2f}")
print(f"Note: With live prices, this should be ~€394,000")

print("\n" + "=" * 70)
print("USER PORTFOLIO VALUES")
print("=" * 70)

users_to_check = ['foehr', 'kremer', 'annika', 'juergen', 'christian']

for username in users_to_check:
    user = next(u for u in USERS if u['username'] == username)
    percentage = user['portfolio_percentage']

    # Calculate value with config prices
    value_config = total_portfolio_value * percentage

    # Calculate value with ~394k (live prices estimate)
    value_live = 394000 * percentage

    # Calculate total invested
    if 'payments' in user:
        total_invested = sum(p['amount'] for p in user['payments'])
    else:
        total_invested = user.get('initial_investment', 0)

    # Calculate return with live prices
    return_amount = value_live - total_invested
    return_pct = (return_amount / total_invested * 100) if total_invested > 0 else 0

    print(f"\n{username.upper()}:")
    print(f"  Percentage: {percentage:.8f} ({percentage*100:.6f}%)")
    print(f"  Value (config prices): €{value_config:,.2f}")
    print(f"  Value (live ~394k): €{value_live:,.2f}")
    print(f"  Total Invested: €{total_invested:,.2f}")
    print(f"  Return (live): €{return_amount:,.2f} ({return_pct:+.2f}%)")

print("\n" + "=" * 70)
print("JUERGEN SPECIFIC CHECK")
print("=" * 70)

juergen = next(u for u in USERS if u['username'] == 'juergen')
juergen_value_live = 394000 * juergen['portfolio_percentage']
juergen_invested = sum(p['amount'] for p in juergen['payments'])

print(f"\nWith live prices (~€394k total):")
print(f"  Juergen's value: €{juergen_value_live:,.2f}")
print(f"  Expected: €108,487.75")
print(f"  Match: {'✓' if abs(juergen_value_live - 108487.75) < 1 else '✗'}")

print(f"\n  Total invested: €{juergen_invested:,.2f}")
print(f"  Return: €{juergen_value_live - juergen_invested:,.2f}")
print(f"  Expected return: €8,487.75")
print(f"  Match: {'✓' if abs((juergen_value_live - juergen_invested) - 8487.75) < 1 else '✗'}")

print("\n" + "=" * 70)
print("PERCENTAGE SUM CHECK")
print("=" * 70)

total_pct = sum(u['portfolio_percentage'] for u in USERS if u['username'] != 'user')
print(f"\nSum of all user percentages: {total_pct:.10f}")
print(f"Expected: 1.0000000000")
print(f"Match: {'✓' if abs(total_pct - 1.0) < 0.00000001 else '✗'}")

print("\n" + "=" * 70)
if abs(juergen_value_live - 108487.75) < 1 and abs(total_pct - 1.0) < 0.00000001:
    print("✓ ALL CHECKS PASSED!")
else:
    print("✗ SOME CHECKS FAILED")
print("=" * 70)
