"""
Recalculate dilution with CORRECT totals:
- Old total: €394k (before adding 50k)
- New total: €444k (after adding 50k)
"""

# Correct values
old_total_portfolio = 394000  # BEFORE adding 50k
new_total_portfolio = 444000  # AFTER adding 50k

# Juergen's values
juergen_old_value = 58487.75  # His value before adding 50k (had +8,487.75 return on 50k investment)
juergen_new_value = 108487.75  # His value after adding 50k

print("=" * 70)
print("DILUTION CALCULATION WITH CORRECT PORTFOLIO VALUES")
print("=" * 70)

print(f"\nOld Total Portfolio: €{old_total_portfolio:,.2f}")
print(f"New Total Portfolio: €{new_total_portfolio:,.2f}")
print(f"Cash Added: €{new_total_portfolio - old_total_portfolio:,.2f}")

# Juergen's percentages
juergen_old_pct = juergen_old_value / old_total_portfolio
juergen_new_pct = juergen_new_value / new_total_portfolio

print(f"\nJuergen:")
print(f"  Old value: €{juergen_old_value:,.2f}")
print(f"  Old percentage: {juergen_old_pct:.8f} ({juergen_old_pct*100:.6f}%)")
print(f"  New value: €{juergen_new_value:,.2f}")
print(f"  New percentage: {juergen_new_pct:.8f} ({juergen_new_pct*100:.6f}%)")
print(f"  Return: €{juergen_old_value - 50000:,.2f} (+{(juergen_old_value - 50000)/50000*100:.2f}%)")

# Other users - their values stay the same, just percentages change
# Old percentages from original config
old_config_percentages = {
    'foehr': 0.0644741,
    'kremer': 0.60447851,
    'annika': 0.00363834,
    'christian': 0.17582904
}

print(f"\n{'='*70}")
print("OTHER USERS")
print('='*70)

# Calculate their values based on their share of the remaining portfolio
remaining_old_value = old_total_portfolio - juergen_old_value
print(f"\nRemaining portfolio value (other users): €{remaining_old_value:,.2f}")

# Calculate each user's share
other_users_sum = sum(old_config_percentages.values())
print(f"Sum of other users' old percentages: {other_users_sum:.8f}")

new_percentages = {}
for user, old_pct in old_config_percentages.items():
    # Calculate their share of the remaining portfolio
    user_share_of_others = old_pct / other_users_sum
    user_old_value = user_share_of_others * remaining_old_value
    user_new_value = user_old_value  # Stays the same (no dilution in absolute terms)
    user_new_pct = user_new_value / new_total_portfolio

    new_percentages[user] = user_new_pct

    print(f"\n{user}:")
    print(f"  Share of 'others': {user_share_of_others:.6f}")
    print(f"  Old value: €{user_old_value:,.2f}")
    print(f"  New value: €{user_new_value:,.2f}")
    print(f"  New percentage: {user_new_pct:.8f} ({user_new_pct*100:.6f}%)")

# Add juergen
new_percentages['juergen'] = juergen_new_pct

print(f"\n{'='*70}")
print("VERIFICATION")
print('='*70)

total_pct = sum(new_percentages.values())
print(f"\nSum of new percentages: {total_pct:.10f}")

# Verify values sum correctly
total_value = juergen_new_value + remaining_old_value
print(f"\nSum of all user values: €{total_value:,.2f}")
print(f"Expected portfolio value: €{new_total_portfolio:,.2f}")
print(f"Difference: €{total_value - new_total_portfolio:,.2f}")

print(f"\n{'='*70}")
print("NEW PERCENTAGES FOR config.py")
print('='*70)

for user in ['foehr', 'kremer', 'annika', 'juergen', 'christian']:
    print(f"{user}: {new_percentages[user]:.8f}")

# Verify by calculating back
print(f"\n{'='*70}")
print("VERIFICATION - Calculate values from new percentages")
print('='*70)

for user in ['foehr', 'kremer', 'annika', 'juergen', 'christian']:
    value = new_percentages[user] * new_total_portfolio
    print(f"{user}: {new_percentages[user]:.8f} × €{new_total_portfolio:,.2f} = €{value:,.2f}")

print(f"\nJuergen's return check:")
print(f"  Value: €{juergen_new_pct * new_total_portfolio:,.2f}")
print(f"  Invested: €100,000.00")
print(f"  Return: €{(juergen_new_pct * new_total_portfolio) - 100000:,.2f}")
print(f"  Expected: €8,487.75")
