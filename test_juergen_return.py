"""
Test Juergen's return calculation after fixing the payments array
"""
from config import STOCKS, USERS

# Get Juergen's config
juergen = next(u for u in USERS if u['username'] == 'juergen')

print("=" * 60)
print("JUERGEN'S CONFIGURATION")
print("=" * 60)

print(f"\nInitial Investment: €{juergen['initial_investment']:,}")
print(f"Portfolio Percentage: {juergen['portfolio_percentage']:.8f} ({juergen['portfolio_percentage']*100:.4f}%)")

if 'payments' in juergen:
    print("\nPayments:")
    total_payments = 0
    for payment in juergen['payments']:
        print(f"  {payment['date']}: €{payment['amount']:,}")
        total_payments += payment['amount']
    print(f"\nTotal from Payments Array: €{total_payments:,}")
else:
    print("\nNo payments array found")

# Calculate total portfolio value
total_portfolio_value = sum(s['quantity'] * s['price'] for s in STOCKS)
print(f"\n{'='*60}")
print("PORTFOLIO CALCULATIONS")
print('='*60)

print(f"\nTotal Portfolio Value: €{total_portfolio_value:,.2f}")

# Juergen's portfolio value
juergen_value = total_portfolio_value * juergen['portfolio_percentage']
print(f"Juergen's Portfolio Value: €{juergen_value:,.2f}")

# Calculate return (should be based on all payments)
if 'payments' in juergen:
    total_invested = sum(p['amount'] for p in juergen['payments'])
else:
    total_invested = juergen['initial_investment']

print(f"\nTotal Amount Invested: €{total_invested:,}")
print(f"Expected: €100,000")
print(f"Match: {'✓' if total_invested == 100000 else '✗ ERROR'}")

# Return calculation
return_amount = juergen_value - total_invested
return_pct = (return_amount / total_invested * 100) if total_invested > 0 else 0

print(f"\n{'='*60}")
print("RETURN CALCULATION")
print('='*60)

print(f"\nCurrent Value: €{juergen_value:,.2f}")
print(f"Total Invested: €{total_invested:,.2f}")
print(f"Return Amount: €{return_amount:,.2f}")
print(f"Return Percentage: {return_pct:+.2f}%")

print(f"\n{'='*60}")
if total_invested == 100000:
    print("✓ SUCCESS: Return calculation now includes all investments!")
else:
    print("✗ ERROR: Return calculation is still wrong!")
print('='*60)
