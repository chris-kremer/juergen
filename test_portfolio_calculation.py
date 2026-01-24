"""
Test script to calculate current and future portfolio values
"""
from config import STOCKS, USERS

# Calculate current total portfolio value (stocks at current prices + cash)
def calculate_portfolio_value(stocks):
    total = 0
    for stock in stocks:
        total += stock['quantity'] * stock['price']
    return total

# Calculate each user's investment amount
def calculate_user_investments(users):
    investments = {}
    for user in users:
        if user['username'] == 'user':  # Skip test user
            continue
        total = user.get('initial_investment', 0)
        payments = user.get('payments', [])
        for payment in payments:
            total += payment['amount']
        investments[user['username']] = total
    return investments

# Current state
print("=" * 60)
print("CURRENT STATE")
print("=" * 60)

current_portfolio_value = calculate_portfolio_value(STOCKS)
print(f"\nCurrent Total Portfolio Value: €{current_portfolio_value:,.2f}")

current_cash = next(s['quantity'] for s in STOCKS if s['symbol'] == 'CASH')
print(f"Current Cash Position: €{current_cash:,.2f}")

print("\nCurrent User Percentages:")
for user in USERS:
    if user['username'] == 'user':
        continue
    print(f"  {user['username']}: {user['portfolio_percentage']:.6f} ({user['portfolio_percentage']*100:.4f}%)")
    print(f"    Portfolio value: €{current_portfolio_value * user['portfolio_percentage']:,.2f}")

user_investments = calculate_user_investments(USERS)
print("\nUser Total Investments:")
for username, investment in user_investments.items():
    print(f"  {username}: €{investment:,.2f}")

total_investments = sum(user_investments.values())
print(f"\nTotal User Investments: €{total_investments:,.2f}")

# New state after juergen adds 50,000
print("\n" + "=" * 60)
print("NEW STATE (After Juergen adds €50,000)")
print("=" * 60)

new_cash = current_cash + 50000
print(f"\nNew Cash Position: €{new_cash:,.2f}")

# The new portfolio value should be old value + 50,000
new_portfolio_value = current_portfolio_value + 50000
print(f"New Total Portfolio Value: €{new_portfolio_value:,.2f}")

# Update juergen's investment
user_investments['juergen'] += 50000
print(f"\nJuergen's New Total Investment: €{user_investments['juergen']:,.2f}")

# Calculate new total investments
new_total_investments = sum(user_investments.values())
print(f"New Total User Investments: €{new_total_investments:,.2f}")

# Recalculate percentages based on each user's investment / total investments
print("\nNew User Percentages (based on investment amounts):")
new_percentages = {}
for username, investment in user_investments.items():
    new_percentage = investment / new_total_investments
    new_percentages[username] = new_percentage
    print(f"  {username}: {new_percentage:.8f} ({new_percentage*100:.6f}%)")
    print(f"    Portfolio value: €{new_portfolio_value * new_percentage:,.2f}")

# Verify percentages sum to 1
percentage_sum = sum(new_percentages.values())
print(f"\nSum of new percentages: {percentage_sum:.10f}")

# Test: Calculate portfolio value with new percentages
print("\n" + "=" * 60)
print("VERIFICATION TEST")
print("=" * 60)
print(f"\nOld total portfolio value: €{current_portfolio_value:,.2f}")
print(f"New total portfolio value: €{new_portfolio_value:,.2f}")
print(f"Difference: €{new_portfolio_value - current_portfolio_value:,.2f} (should be €50,000.00)")

print("\nUser portfolio values comparison:")
for username in user_investments.keys():
    old_pct = next(u['portfolio_percentage'] for u in USERS if u['username'] == username)
    old_value = current_portfolio_value * old_pct
    new_value = new_portfolio_value * new_percentages[username]

    print(f"\n  {username}:")
    print(f"    Old: {old_pct:.8f} = €{old_value:,.2f}")
    print(f"    New: {new_percentages[username]:.8f} = €{new_value:,.2f}")
    print(f"    Change: €{new_value - old_value:,.2f}")
