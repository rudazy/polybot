"""
Test trade WITHOUT builder credentials - just private key
"""

from wallet_manager import WalletManager
from mongodb_database import MongoDatabase
from polymarket_api import PolymarketAPI
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY

# Initialize
db = MongoDatabase()
wallet_manager = WalletManager(db)
polymarket = PolymarketAPI()

user_id = "69143b58947a61414d26119e"
email = "Drzobara@gmail.com"

print("\n=== SIMPLE TRADE TEST (NO BUILDER CREDS) ===\n")

# Get private key
print("1. Getting private key...")
private_key = wallet_manager.export_private_key(user_id)

if not private_key:
    print("ERROR: No private key")
    exit(1)

if private_key.startswith('0x'):
    private_key = private_key[2:]

print(f"   Key: {private_key[:10]}...")

# Get a market
print("\n2. Finding market...")
markets = polymarket.get_trending_markets(limit=100)

test_market = None
for market in markets:
    formatted = polymarket.format_market_data(market)
    token_ids = formatted.get('token_ids', [])
    condition_id = formatted.get('condition_id')

    # Just take ANY market with token IDs for testing
    if token_ids and len(token_ids) >= 2 and condition_id:
        test_market = formatted
        print(f"   Using any available market for testing")
        break

if not test_market:
    print("ERROR: No tradeable market found")
    exit(1)

print(f"   Market: {test_market['question'][:60]}...")
print(f"   Liquidity: ${test_market['liquidity']:.2f}")

# Create simple client with ONLY private key
print("\n3. Creating CLOB client (no builder creds)...")
client = ClobClient(
    host="https://clob.polymarket.com",
    chain_id=137,
    key=private_key
)
print("   OK Client created")

# Try to create and post order
print("\n4. Creating order...")
token_id = test_market['token_ids'][0]
price = 0.50  # 50% probability
amount = 1.0  # $1 USDC
size = amount / price  # 2 shares

print(f"   Token: {token_id}")
print(f"   Price: {price}")
print(f"   Size: {size} shares")

try:
    order_args = OrderArgs(
        token_id=token_id,
        price=price,
        size=size,
        side=BUY,
        fee_rate_bps=0
    )

    print("\n5. Signing order...")
    signed_order = client.create_order(order_args)
    print("   OK Order signed")

    print("\n6. Posting order...")
    resp = client.post_order(signed_order, OrderType.FOK)

    print(f"\n=== RESULT ===")
    print(f"Response: {resp}")

    if resp and resp.get('success'):
        print(f"\nTRADE SUCCESSFUL!")
        print(f"Order ID: {resp.get('orderID')}")
    else:
        print(f"\nTrade failed but no exception")
        print(f"Response: {resp}")

except Exception as e:
    print(f"\nTRADE FAILED!")
    print(f"Error: {e}")
    print(f"Error Type: {type(e).__name__}")

    import traceback
    traceback.print_exc()
