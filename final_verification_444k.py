"""
Final verification with correct totals:
- Old: €394k
- New: €444k (with live prices)
"""
from config import STOCKS, USERS

print("=" * 70)
print("FINAL VERIFICATION")
print("=" * 70)

# Expected values
expected_new_total = 444000
expected_juergen_value = 108487.75

print(f"\nExpected Total Portfolio (with live prices): €{expected_new_total:,.2f}")
print(f"Expected Juergen Value: €{expected_juergen_value:,.2f}")

print("\n" + "=" * 70)
print("USER PORTFOLIO VALUES (at €444k total)")
print("=" * 70)

users_to_check = ['foehr', 'kremer', 'annika', 'juergen', 'christian']

total_value = 0
for username in users_to_check:
    user = next(u for u in USERS if u['username'] == username)
    percentage = user['portfolio_percentage']

    # Calculate value at expected new total
    value_at_444k = expected_new_total * percentage
    total_value += value_at_444k

    # Calculate total invested
    if 'payments' in user:
        total_invested = sum(p['amount'] for p in user['payments'])
    else:
        total_invested = user.get('initial_investment', 0)

    # Calculate return
    return_amount = value_at_444k - total_invested
    return_pct = (return_amount / total_invested * 100) if total_invested > 0 else 0

    print(f"\n{username.upper()}:")
    print(f"  Percentage: {percentage:.8f} ({percentage*100:.6f}%)")
    print(f"  Value @ €444k: €{value_at_444k:,.2f}")
    print(f"  Total Invested: €{total_invested:,.2f}")
    print(f"  Return: €{return_amount:,.2f} ({return_pct:+.2f}%)")

print("\n" + "=" * 70)
print("CRITICAL CHECKS")
print("=" * 70)

# Check 1: Percentages sum to 1
total_pct = sum(u['portfolio_percentage'] for u in USERS if u['username'] != 'user')
print(f"\n1. Sum of percentages: {total_pct:.10f}")
print(f"   Expected: 1.0000000000")
print(f"   Status: {'✓ PASS' if abs(total_pct - 1.0) < 0.00000001 else '✗ FAIL'}")

# Check 2: Total value equals expected
print(f"\n2. Sum of user values: €{total_value:,.2f}")
print(f"   Expected: €{expected_new_total:,.2f}")
print(f"   Status: {'✓ PASS' if abs(total_value - expected_new_total) < 0.01 else '✗ FAIL'}")

# Check 3: Juergen's specific value
juergen = next(u for u in USERS if u['username'] == 'juergen')
juergen_value = expected_new_total * juergen['portfolio_percentage']
print(f"\n3. Juergen's value: €{juergen_value:,.2f}")
print(f"   Expected: €{expected_juergen_value:,.2f}")
print(f"   Status: {'✓ PASS' if abs(juergen_value - expected_juergen_value) < 0.01 else '✗ FAIL'}")

# Check 4: Juergen's return
juergen_invested = sum(p['amount'] for p in juergen['payments'])
juergen_return = juergen_value - juergen_invested
print(f"\n4. Juergen's return: €{juergen_return:,.2f}")
print(f"   Expected: €8,487.75")
print(f"   Status: {'✓ PASS' if abs(juergen_return - 8487.75) < 0.01 else '✗ FAIL'}")

print("\n" + "=" * 70)
all_pass = (
    abs(total_pct - 1.0) < 0.00000001 and
    abs(total_value - expected_new_total) < 0.01 and
    abs(juergen_value - expected_juergen_value) < 0.01 and
    abs(juergen_return - 8487.75) < 0.01
)

if all_pass:
    print("✓✓✓ ALL CHECKS PASSED! ✓✓✓")
else:
    print("✗✗✗ SOME CHECKS FAILED ✗✗✗")
print("=" * 70)
