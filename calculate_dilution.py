"""
Calculate proper dilution when juergen adds €50,000
Using value-based dilution method
"""
from config import STOCKS, USERS

# Current state
print("=" * 60)
print("CALCULATING DILUTION - VALUE-BASED METHOD")
print("=" * 60)

# Get current total portfolio value
current_portfolio_value = sum(stock['quantity'] * stock['price'] for stock in STOCKS)
print(f"\nCurrent Total Portfolio Value: €{current_portfolio_value:,.2f}")

# Get current percentages (excluding 'user')
current_percentages = {}
for u in USERS:
    if u['username'] != 'user':
        current_percentages[u['username']] = u['portfolio_percentage']

# First, normalize current percentages to sum to exactly 1.0
current_sum = sum(current_percentages.values())
print(f"\nCurrent sum of percentages: {current_sum:.10f}")

print("\nNormalizing percentages to sum to 1.0:")
normalized_percentages = {}
for username, pct in current_percentages.items():
    normalized_percentages[username] = pct / current_sum
    print(f"  {username}: {pct:.8f} -> {normalized_percentages[username]:.8f}")

# Calculate each user's current portfolio value
print("\nCurrent portfolio values:")
current_values = {}
for username, pct in normalized_percentages.items():
    value = pct * current_portfolio_value
    current_values[username] = value
    print(f"  {username}: €{value:,.2f}")

# Juergen adds €50,000
print(f"\n{'='*60}")
print("AFTER JUERGEN ADDS €50,000")
print('='*60)

new_cash = 81358 + 50000
print(f"\nNew Cash Position: €{new_cash:,.2f}")

# Add to juergen's value
current_values['juergen'] += 50000
print(f"\nJuergen's new portfolio value: €{current_values['juergen']:,.2f}")

# New total portfolio value
new_portfolio_value = current_portfolio_value + 50000
print(f"New Total Portfolio Value: €{new_portfolio_value:,.2f}")

# Calculate new percentages
print("\nNew percentages (with dilution):")
new_percentages = {}
for username, value in current_values.items():
    new_pct = value / new_portfolio_value
    new_percentages[username] = new_pct
    old_pct = normalized_percentages[username]
    print(f"  {username}: {old_pct:.8f} -> {new_pct:.8f} ({new_pct*100:.6f}%)")
    print(f"    Value: €{value:,.2f}")
    if username == 'juergen':
        print(f"    Change: +{(new_pct - old_pct)*100:.6f}% (added money)")
    else:
        print(f"    Change: {(new_pct - old_pct)*100:.6f}% (diluted)")

# Verify sum
new_sum = sum(new_percentages.values())
print(f"\nSum of new percentages: {new_sum:.10f}")

# Output final values for config.py
print(f"\n{'='*60}")
print("FINAL VALUES FOR config.py")
print('='*60)
print("\nCash quantity to update:")
print(f"  {new_cash:.2f}")

print("\nUser percentages to update:")
for username in ['foehr', 'kremer', 'annika', 'juergen', 'christian']:
    print(f'  {username}: {new_percentages[username]:.8f}')

# Add payment to juergen's record
print("\nAdd this payment to juergen's payments array:")
print('  {"amount": 50000, "date": "2026-01-24"}')
