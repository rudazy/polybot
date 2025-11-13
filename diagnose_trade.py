"""
Diagnose trade execution issues
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

print("\n=== DIAGNOSING TRADE EXECUTION ===\n")

# Check all user accounts
print("1. Checking all user wallets...")
users = list(db.users.find())

for user in users:
    user_id = str(user['_id'])
    email = user.get('email')
    wallet_address = user.get('wallet_address')
    wallet_type = user.get('wallet_type')

    if wallet_address and wallet_address != 'None':
        balance_info = wallet_manager.get_wallet_balance(wallet_address)
        usdc = balance_info.get('usdc_balance', 0)

        print(f"\n  User: {email}")
        print(f"    Wallet: {wallet_address[:12]}...")
        print(f"    Type: {wallet_type}")
        print(f"    USDC: ${usdc}")

        if usdc >= 1:
            print(f"    ✅ Has enough USDC to test!")

# Check if CLOB client is working
print("\n2. Checking CLOB client...")
if trading.client:
    print("   ✅ CLOB client initialized")
    print(f"   Host: {trading.host}")
    print(f"   Builder enabled: {trading.builder_enabled}")
else:
    print("   ❌ CLOB client NOT initialized")

# Check if we can get market data with token IDs
print("\n3. Checking market data...")
markets = polymarket.get_trending_markets(limit=5)

if markets:
    print(f"   ✅ Retrieved {len(markets)} markets")

    market_with_tokens = None
    for market in markets:
        formatted = polymarket.format_market_data(market)
        token_ids = formatted.get('token_ids', [])

        if token_ids and len(token_ids) >= 2:
            market_with_tokens = formatted
            print(f"\n   ✅ Found market with token IDs:")
            print(f"      Question: {formatted['question'][:60]}...")
            print(f"      Token IDs: {token_ids}")
            print(f"      Condition ID: {formatted.get('condition_id')}")
            break

    if not market_with_tokens:
        print("\n   ❌ No markets found with token IDs!")
        print("   This could be why trades are failing")
else:
    print("   ❌ No markets retrieved")

print("\n=== DIAGNOSIS COMPLETE ===\n")
print("ISSUES TO FIX:")
print("1. If no USDC in any wallet → Need to fund a wallet")
print("2. If CLOB client not initialized → Check builder credentials")
print("3. If no markets with token IDs → Markets may not be tradeable yet")
