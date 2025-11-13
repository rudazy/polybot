"""
Fix wallet address mismatch - use the wallet we have the key for
"""

from mongodb_database import MongoDatabase
from bson.objectid import ObjectId

db = MongoDatabase()

user_id = "69143b58947a61414d26119e"
correct_wallet = "0x1987c31825C5002966F1E265B771868F486DB93A"  # The one with private key

print("\n=== FIXING WALLET MISMATCH ===\n")

print(f"Updating user {user_id}")
print(f"New wallet address: {correct_wallet}")
print(f"This wallet has: $1.89 USDC + 0.071 POL")
print(f"And we HAVE the private key for it")

# Update user record
result = db.users.update_one(
    {"_id": ObjectId(user_id)},
    {
        "$set": {
            "wallet_address": correct_wallet,
            "wallet_type": "imported"
        }
    }
)

if result.modified_count > 0:
    print("\nOK User record updated successfully!")

    # Verify
    user = db.users.find_one({"_id": ObjectId(user_id)})
    print(f"\nVerification:")
    print(f"   Email: {user.get('email')}")
    print(f"   Wallet Address: {user.get('wallet_address')}")
    print(f"   Wallet Type: {user.get('wallet_type')}")

    print("\nYou can now test trading with this wallet!")
else:
    print("\nERROR: Failed to update user record")
