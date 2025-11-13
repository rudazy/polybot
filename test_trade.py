"""
Test real trade execution
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

# Test wallet (first Safe wallet)
user_id = "691357fb50a17a1fd083862c"
wallet_address = "0xD3fe1960CA17a1698d3333Cd99915AF404914949"

print(f"\n=== TESTING TRADE FOR USER {user_id} ===\n")

# Check balance
print("1. Checking wallet balance...")
balance_info = wallet_manager.get_wallet_balance(wallet_address)

if balance_info.get('success'):
    usdc = balance_info.get('usdc_balance', 0)
    pol = balance_info.get('pol_balance', 0)
    print(f"   POL Balance: {pol} POL")
    print(f"   USDC Balance: {usdc} USDC")

    if usdc < 1:
        print(f"\n   ERROR: Need at least $1 USDC to test trade")
        print(f"   Current balance: ${usdc}")
        exit(1)
else:
    print(f"   ERROR: Failed to get balance: {balance_info}")
    exit(1)

# Get a popular market
print("\n2. Getting popular market...")
markets = polymarket.get_trending_markets(limit=10)

if not markets:
    print("   ERROR: No markets available")
    exit(1)

# Find a market with token IDs
test_market = None
for market in markets:
    formatted = polymarket.format_market_data(market)
    if formatted.get('token_ids') and len(formatted.get('token_ids', [])) >= 2:
        test_market = formatted
        break

if not test_market:
    print("   ERROR: No markets with token IDs found")
    exit(1)

print(f"   Market: {test_market['question'][:70]}...")
print(f"   Token IDs: {test_market.get('token_ids')}")
print(f"   Condition ID: {test_market.get('condition_id')}")

# Get private key
print("\n3. Getting private key for signing...")
key_export = wallet_manager.export_private_key(user_id, wallet_address)

if not key_export.get('success'):
    print(f"   ERROR: Failed to export key: {key_export}")
    exit(1)

private_key = key_export.get('private_key')
print(f"   Key exported: {private_key[:10]}...")

# Execute trade
print("\n4. Executing test trade...")
print(f"   Amount: $1 USDC")
print(f"   Side: YES")
print(f"   Token ID: {test_market['token_ids'][0]}")

try:
    order_result = trading.create_market_order(
        private_key=private_key,
        token_id=test_market['token_ids'][0],
        side='YES',
        amount=1.0,
        condition_id=test_market['condition_id']
    )

    print(f"\n=== TRADE RESULT ===")
    print(f"Success: {order_result.get('success')}")

    if order_result.get('success'):
        print(f"Order ID: {order_result.get('order_id')}")
        print(f"Price: ${order_result.get('price')}")
        print(f"Shares: {order_result.get('size')}")
        print(f"Builder Attributed: {order_result.get('builder_attributed')}")
        print(f"\nTRADE EXECUTED SUCCESSFULLY!")
    else:
        print(f"Error: {order_result.get('error')}")
        print(f"Details: {order_result.get('details')}")

except Exception as e:
    print(f"\nEXCEPTION during trade execution:")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
