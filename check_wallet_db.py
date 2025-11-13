"""
Check what's in the database for the Drzobara account
"""

from mongodb_database import MongoDatabase
from bson.objectid import ObjectId

db = MongoDatabase()

user_id = "69143b58947a61414d26119e"
wallet_address = "0x2A64e04D2447f95e28aF4f54630567188f4a4042"

print("\n=== CHECKING DATABASE FOR DRZOBARA ACCOUNT ===\n")

# Check user record
print("1. User record:")
user = db.users.find_one({"_id": ObjectId(user_id)})
if user:
    print(f"   Email: {user.get('email')}")
    print(f"   Wallet Address: {user.get('wallet_address')}")
    print(f"   Wallet Type: {user.get('wallet_type')}")
    print(f"   Owner Address: {user.get('owner_address', 'N/A')}")
else:
    print("   User not found!")

# Check wallets collection
print("\n2. Wallets collection:")
wallets_collection = db.db['wallets']

all_user_wallets = list(wallets_collection.find({"user_id": user_id}))
print(f"   Found {len(all_user_wallets)} wallet entries for this user")

for i, wallet in enumerate(all_user_wallets, 1):
    print(f"\n   Wallet {i}:")
    print(f"      User ID: {wallet.get('user_id')}")
    print(f"      Wallet Address: {wallet.get('wallet_address')}")
    print(f"      Owner Address: {wallet.get('owner_address', 'N/A')}")
    print(f"      Wallet Type: {wallet.get('wallet_type', 'N/A')}")
    print(f"      Has Private Key: {'Yes' if wallet.get('private_key_encrypted') else 'No'}")

# Try to find by exact match
print("\n3. Looking for exact match:")
exact_wallet = wallets_collection.find_one({
    "user_id": user_id,
    "wallet_address": wallet_address
})

if exact_wallet:
    print(f"   Found wallet with address {wallet_address}")
    print(f"   Wallet Type: {exact_wallet.get('wallet_type', 'N/A')}")
    print(f"   Has Private Key: {'Yes' if exact_wallet.get('private_key_encrypted') else 'No'}")
else:
    print(f"   No wallet found with address {wallet_address}")

# Try Safe wallet specific search
print("\n4. Looking for Safe wallet:")
safe_wallet = wallets_collection.find_one({
    "user_id": user_id,
    "wallet_type": "safe"
})

if safe_wallet:
    print(f"   Found Safe wallet:")
    print(f"   Safe Address: {safe_wallet.get('wallet_address')}")
    print(f"   Owner Address: {safe_wallet.get('owner_address', 'N/A')}")
    print(f"   Has Private Key: {'Yes' if safe_wallet.get('private_key_encrypted') else 'No'}")
else:
    print(f"   No Safe wallet found")

print("\n=== DIAGNOSIS COMPLETE ===\n")
