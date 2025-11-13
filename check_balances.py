"""
Check balances for both wallet addresses
"""

from wallet_manager import WalletManager
from mongodb_database import MongoDatabase

db = MongoDatabase()
wallet_manager = WalletManager(db)

address1 = "0x2A64e04D2447f95e28aF4f54630567188f4a4042"  # Current in user record
address2 = "0x1987c31825C5002966F1E265B771868F486DB93A"  # In wallets collection

print("\n=== CHECKING BALANCES ===\n")

print(f"1. Address in user record: {address1}")
balance1 = wallet_manager.get_wallet_balance(address1)
if balance1.get('success'):
    print(f"   USDC: ${balance1.get('usdc_balance', 0)}")
    print(f"   POL: {balance1.get('pol_balance', 0)}")
else:
    print(f"   Failed to get balance")

print(f"\n2. Address in wallets collection: {address2}")
balance2 = wallet_manager.get_wallet_balance(address2)
if balance2.get('success'):
    print(f"   USDC: ${balance2.get('usdc_balance', 0)}")
    print(f"   POL: {balance2.get('pol_balance', 0)}")
else:
    print(f"   Failed to get balance")

print("\n=== CONCLUSION ===")
if balance1.get('usdc_balance', 0) > 0:
    print(f"Funds are in: {address1} (user record)")
    print(f"But private key is stored for: {address2}")
    print(f"MISMATCH - Need to use the wallet with funds!")
elif balance2.get('usdc_balance', 0) > 0:
    print(f"Funds are in: {address2} (wallets collection)")
    print(f"This address HAS the private key stored")
    print(f"Should update user record to use this address")
