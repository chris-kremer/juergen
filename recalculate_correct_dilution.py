"""
Recalculate dilution based on actual values
User says Juergen's total value should be €108,487.75
"""

# Given information
old_portfolio_value = 273482.36
new_cash = 131358.0
new_portfolio_value = old_portfolio_value + 50000  # Adding 50k
print(f"New portfolio value: €{new_portfolio_value:,.2f}")

# Juergen's target value (from user)
juergen_target_value = 108487.75
juergen_new_percentage = juergen_target_value / new_portfolio_value

print(f"\nJuergen:")
print(f"  Target value: €{juergen_target_value:,.2f}")
print(f"  New percentage: {juergen_new_percentage:.8f} ({juergen_new_percentage*100:.6f}%)")

# Work backwards to find what his old value was
juergen_value_before = juergen_target_value - 50000
juergen_old_percentage = juergen_value_before / old_portfolio_value

print(f"  Value before today: €{juergen_value_before:,.2f}")
print(f"  Old percentage (calculated): {juergen_old_percentage:.8f} ({juergen_old_percentage*100:.6f}%)")
print(f"  Old percentage (in config): 0.14746305 (14.7463%)")
print(f"  Return before today: €{juergen_value_before - 50000:,.2f}")

# Now calculate what everyone else's percentages should be
# Everyone else's absolute value stays the same, but percentages decrease

print(f"\n{'='*70}")
print("OTHER USERS - Maintaining their absolute values")
print('='*70)

# From the old config, let's calculate their old values
old_percentages = {
    'foehr': 0.0644741,
    'kremer': 0.60447851,
    'annika': 0.00363834,
    'christian': 0.17582904
}

# Calculate old values
old_values = {}
for user, old_pct in old_percentages.items():
    old_value = old_portfolio_value * old_pct
    old_values[user] = old_value
    print(f"\n{user}:")
    print(f"  Old value: €{old_value:,.2f}")
    print(f"  New value: €{old_value:,.2f} (unchanged)")

    new_pct = old_value / new_portfolio_value
    print(f"  Old percentage: {old_pct:.8f}")
    print(f"  New percentage: {new_pct:.8f}")

# Verify the sum
print(f"\n{'='*70}")
print("VERIFICATION")
print('='*70)

total_value = juergen_target_value + sum(old_values.values())
print(f"\nSum of all user values: €{total_value:,.2f}")
print(f"Total portfolio value: €{new_portfolio_value:,.2f}")
print(f"Difference: €{total_value - new_portfolio_value:,.2f}")

# Calculate new percentages
new_percentages = {
    'juergen': juergen_new_percentage
}

for user, old_value in old_values.items():
    new_percentages[user] = old_value / new_portfolio_value

print(f"\nSum of new percentages: {sum(new_percentages.values()):.10f}")

print(f"\n{'='*70}")
print("NEW PERCENTAGES FOR config.py")
print('='*70)

for user in ['foehr', 'kremer', 'annika', 'juergen', 'christian']:
    print(f"{user}: {new_percentages[user]:.8f}")
