"""
Find who has the duplicate wallet address
"""

from mongodb_database import MongoDatabase

db = MongoDatabase()

wallet_address = "0x1987c31825C5002966F1E265B771868F486DB93A"

print(f"\n=== FINDING WHO HAS WALLET {wallet_address} ===\n")

# Find all users with this wallet
users = list(db.users.find({"wallet_address": wallet_address}))

print(f"Found {len(users)} user(s) with this wallet:\n")

for user in users:
    print(f"User ID: {user['_id']}")
    print(f"Email: {user.get('email')}")
    print(f"Wallet Type: {user.get('wallet_type')}")
    print()

# Check wallets collection
wallets_collection = db.db['wallets']
wallets = list(wallets_collection.find({"wallet_address": wallet_address}))

print(f"Found {len(wallets)} wallet entry/entries:\n")

for wallet in wallets:
    print(f"User ID: {wallet.get('user_id')}")
    print(f"Wallet Type: {wallet.get('wallet_type')}")
    print(f"Has Private Key: {'Yes' if wallet.get('private_key_encrypted') else 'No'}")
    print()
