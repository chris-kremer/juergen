"""
Recalculate dilution with correct total portfolio value
User says total should be ~394k after adding 50k
So old total was ~344k
"""

# Correct values based on user input
old_total_portfolio = 344000  # approximately
new_total_portfolio = 394000  # approximately (after adding 50k)

# Juergen's values
juergen_old_value = 58487.75  # His value before adding 50k (had +8k return on 50k investment)
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
# We need to work backwards from the old config percentages

print(f"\n{'='*70}")
print("OTHER USERS")
print('='*70)

# Old percentages from config (the ones we had before this change)
old_config_percentages = {
    'foehr': 0.0644741,
    'kremer': 0.60447851,
    'annika': 0.00363834,
    'christian': 0.17582904
}

# Calculate their values based on a normalized share of the remaining portfolio
# Total old portfolio = 344k
# Juergen had 58,487.75
# Others split the remaining: 344k - 58,487.75 = 285,512.25

remaining_old_value = old_total_portfolio - juergen_old_value
print(f"\nRemaining portfolio value (other users): €{remaining_old_value:,.2f}")

# Calculate each user's share of the remaining portfolio
# First normalize the old config percentages (excluding juergen)
other_users_sum = sum(old_config_percentages.values())
print(f"Sum of other users' old percentages: {other_users_sum:.8f}")

new_percentages = {}
for user, old_pct in old_config_percentages.items():
    # Calculate their share of the remaining portfolio
    user_share_of_others = old_pct / other_users_sum
    user_old_value = user_share_of_others * remaining_old_value
    user_new_value = user_old_value  # Stays the same
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
