"""
Test trade for drzobara@gmail.com account
"""

from wallet_manager import WalletManager
from mongodb_database import MongoDatabase
from polymarket_api import PolymarketAPI
from polymarket_trading import PolymarketTrading

# Initialize
db = MongoDatabase()
wallet_manager = WalletManager(db)
polymarket = PolymarketAPI()
trading = PolymarketTrading()

wallet_address = "0x2A64e04D2447f95e28aF4f54630567188f4a4042"
email = "Drzobara@gmail.com"

print("\n=== TESTING DRZOBARA ACCOUNT ===\n")

# Find user
user = db.users.find_one({"email": email})
if not user:
    print(f"ERROR: User {email} not found")
    exit(1)

user_id = str(user['_id'])
wallet_type = user.get('wallet_type')

print(f"User ID: {user_id}")
print(f"Wallet Type: {wallet_type}")
print(f"Wallet Address: {wallet_address}")

# Check balance
print("\n1. Checking balance...")
balance_info = wallet_manager.get_wallet_balance(wallet_address)

if balance_info.get('success'):
    usdc = balance_info.get('usdc_balance', 0)
    pol = balance_info.get('pol_balance', 0)
    print(f"   POL: {pol} POL")
    print(f"   USDC: ${usdc} USDC")

    if usdc < 1:
        print(f"\n   ERROR: Not enough USDC!")
        print(f"   Current: ${usdc}")
        print(f"   Required: $1")
        exit(1)
else:
    print(f"   ERROR: Failed to get balance")
    print(f"   {balance_info}")
    exit(1)

# Get a market with token IDs - Try to find one with volume
print("\n2. Finding tradeable market...")
markets = polymarket.get_trending_markets(limit=100)

if not markets:
    print("   ERROR: No markets available")
    exit(1)

test_market = None
for market in markets:
    formatted = polymarket.format_market_data(market)
    token_ids = formatted.get('token_ids', [])
    condition_id = formatted.get('condition_id')
    liquidity = formatted.get('liquidity', 0)

    # For testing: Just need token IDs and condition ID
    # Check liquidity > 0 to ensure there's an orderbook
    if token_ids and len(token_ids) >= 2 and condition_id and liquidity > 0:
        test_market = formatted
        print(f"   Found market with ${liquidity:,.2f} liquidity")
        break

# If no liquid market, just take any market with token IDs for testing
if not test_market:
    print("   No liquid markets found, trying any market with token IDs...")
    for market in markets:
        formatted = polymarket.format_market_data(market)
        token_ids = formatted.get('token_ids', [])
        condition_id = formatted.get('condition_id')

        if token_ids and len(token_ids) >= 2 and condition_id:
            test_market = formatted
            print(f"   Using market (may have no orderbook yet)")
            break

if not test_market:
    print("   ERROR: No markets with token IDs found")
    exit(1)

print(f"   Market: {test_market['question'][:70]}...")
print(f"   Token IDs: {test_market.get('token_ids')}")
print(f"   Condition ID: {test_market.get('condition_id')}")

# Get private key
print("\n3. Exporting private key...")
private_key = wallet_manager.export_private_key(user_id)

if not private_key:
    print(f"   ERROR: Failed to export key")
    print(f"   Function returned None")
    exit(1)

print(f"   Key: {private_key[:10]}...")

# Try to execute trade
print("\n4. Executing trade...")
print(f"   Amount: $1 USDC")
print(f"   Side: YES")
print(f"   Token: {test_market['token_ids'][0]}")

try:
    order_result = trading.create_market_order(
        private_key=private_key,
        token_id=test_market['token_ids'][0],
        side='YES',
        amount=1.0,
        condition_id=test_market['condition_id']
    )

    print(f"\n=== RESULT ===")
    print(f"Success: {order_result.get('success')}")

    if order_result.get('success'):
        print(f"Order ID: {order_result.get('order_id')}")
        print(f"Price: ${order_result.get('price'):.4f}")
        print(f"Shares: {order_result.get('size'):.2f}")
        print(f"\nTRADE EXECUTED SUCCESSFULLY!")
    else:
        print(f"\nTRADE FAILED!")
        print(f"Error: {order_result.get('error')}")
        print(f"Error Type: {order_result.get('error_type')}")
        print(f"\nFull response:")
        import json
        print(json.dumps(order_result, indent=2))

except Exception as e:
    print(f"\nEXCEPTION:")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
