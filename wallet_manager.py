"""
Wallet Manager for Polymarket Trading Bot
Supports both in-app wallets and MetaMask connection
WITH PRIVATE KEY EXPORT FEATURE
"""

import secrets
import json
import base64
from typing import Dict, Optional
from mongodb_database import MongoDatabase

class WalletManager:
    """
    Manages both in-app wallets and external wallet connections
    """
    
    def __init__(self, db: MongoDatabase):
        """Initialize wallet manager"""
        self.db = db
        print("✅ Wallet Manager initialized (offline mode)")
    
    # ==================== IN-APP WALLET CREATION ====================
    
    def create_in_app_wallet(self, user_id: str) -> Dict:
        """
        Create a new in-app wallet for the user
        
        Args:
            user_id: User's database ID
            
        Returns:
            Dictionary with wallet address and encrypted private key
        """
        try:
            # Generate new wallet
            private_key = "0x" + secrets.token_hex(32)
            wallet_address = "0x" + secrets.token_hex(20)
            
            print(f"🔐 Created new wallet: {wallet_address}")
            
            # Encrypt private key before storing
            encrypted_key = self._encrypt_key(private_key)
            
            # Store wallet in database
            from bson.objectid import ObjectId
            self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "wallet_address": wallet_address,
                        "wallet_type": "in-app"
                    }
                }
            )
            
            # Store encrypted private key separately (more secure)
            wallets_collection = self.db.db['wallets']
            
            # Remove old wallet if exists
            wallets_collection.delete_many({"user_id": user_id})
            
            # Insert new wallet
            wallets_collection.insert_one({
                "user_id": user_id,
                "wallet_address": wallet_address,
                "private_key_encrypted": encrypted_key
            })
            
            return {
                "success": True,
                "wallet_address": wallet_address,
                "wallet_type": "in-app",
                "message": "In-app wallet created successfully!"
            }
            
        except Exception as e:
            print(f"❌ Error creating wallet: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== ENCRYPTION/DECRYPTION ====================
    
    def _encrypt_key(self, private_key: str) -> str:
        """
        Encrypt private key before storing
        Using base64 encoding for demo (in production, use AES-256 encryption!)
        
        Args:
            private_key: Raw private key
            
        Returns:
            Encrypted/encoded private key
        """
        # Simple base64 encoding (NOT secure for production!)
        # In production, use proper encryption like Fernet or AES-256
        encoded = base64.b64encode(private_key.encode()).decode()
        return encoded
    
    def _decrypt_key(self, encrypted_key: str) -> str:
        """
        Decrypt private key when needed
        
        Args:
            encrypted_key: Encrypted private key
            
        Returns:
            Decrypted private key
        """
        # Decode from base64
        decoded = base64.b64decode(encrypted_key.encode()).decode()
        return decoded
    
    # ==================== PRIVATE KEY EXPORT ====================
    
    def export_private_key(self, user_id: str) -> Optional[str]:
        """
        Export private key for in-app wallet (DANGEROUS - warn user!)
        
        Args:
            user_id: User's database ID
            
        Returns:
            Private key or None
        """
        try:
            # Get user wallet type
            from bson.objectid import ObjectId
            user = self.db.users.find_one({"_id": ObjectId(user_id)})
            
            if not user:
                print("❌ User not found")
                return None
            
            if user.get('wallet_type') != 'in-app':
                print("❌ Not an in-app wallet (cannot export external wallet keys)")
                return None
            
            # Get encrypted private key
            wallets_collection = self.db.db['wallets']
            wallet = wallets_collection.find_one({"user_id": user_id})
            
            if not wallet:
                print("❌ Wallet not found in database")
                return None
            
            # Decrypt and return
            private_key = self._decrypt_key(wallet['private_key_encrypted'])
            
            print(f"⚠️ WARNING: Private key exported for user {user_id}")
            
            return private_key
            
        except Exception as e:
            print(f"❌ Error exporting private key: {e}")
            return None
    
    # ==================== EXTERNAL WALLET CONNECTION ====================
    
    def connect_external_wallet(self, user_id: str, wallet_address: str) -> Dict:
        """
        Connect user's external wallet (MetaMask, WalletConnect, etc.)
        
        Args:
            user_id: User's database ID
            wallet_address: External wallet address
            
        Returns:
            Success status
        """
        try:
            # Basic validation
            if not wallet_address.startswith('0x') or len(wallet_address) != 42:
                return {
                    "success": False,
                    "error": "Invalid wallet address format"
                }
            
            # Store wallet connection
            from bson.objectid import ObjectId
            self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "wallet_address": wallet_address,
                        "wallet_type": "external"
                    }
                }
            )
            
            print(f"🦊 Connected external wallet: {wallet_address}")
            
            return {
                "success": True,
                "wallet_address": wallet_address,
                "wallet_type": "external",
                "message": "External wallet connected successfully!"
            }
            
        except Exception as e:
            print(f"❌ Error connecting wallet: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== WALLET BALANCE (SIMULATED) ====================
    
    def get_wallet_balance(self, wallet_address: str) -> Dict:
        """
        Get wallet balances (simulated for now)
        
        Args:
            wallet_address: Wallet address to check
            
        Returns:
            Dictionary with balances
        """
        try:
            # Simulate some balance
            return {
                "success": True,
                "wallet_address": wallet_address,
                "matic_balance": 0.5,  # Simulated
                "usdc_balance": 100.0  # Simulated
            }
            
        except Exception as e:
            print(f"❌ Error getting balance: {e}")
            return {
                "success": False,
                "error": str(e),
                "matic_balance": 0.0,
                "usdc_balance": 0.0
            }
    
    # ==================== WALLET INFO ====================
    
    def get_user_wallet(self, user_id: str) -> Optional[Dict]:
        """
        Get user's wallet information
        
        Args:
            user_id: User's database ID
            
        Returns:
            Wallet information or None
        """
        try:
            from bson.objectid import ObjectId
            user = self.db.users.find_one({"_id": ObjectId(user_id)})
            
            if not user or not user.get('wallet_address'):
                return None
            
            wallet_address = user['wallet_address']
            wallet_type = user.get('wallet_type', 'unknown')
            
            # Get balance
            balance_info = self.get_wallet_balance(wallet_address)
            
            return {
                "wallet_address": wallet_address,
                "wallet_type": wallet_type,
                "matic_balance": balance_info.get('matic_balance', 0.0),
                "usdc_balance": balance_info.get('usdc_balance', 0.0)
            }
            
        except Exception as e:
            print(f"❌ Error getting wallet info: {e}")
            return None


def test_wallet_manager():
    """Test wallet manager functionality"""
    print("🧪 Testing Wallet Manager with Private Key Export...\n")
    
    # Initialize
    db = MongoDatabase()
    wallet_manager = WalletManager(db)
    
    # Test 1: Create in-app wallet
    print("Test 1: Creating in-app wallet...")
    
    # Get a real user from database
    user = db.users.find_one({})
    if user:
        user_id = str(user['_id'])
        
        result = wallet_manager.create_in_app_wallet(user_id)
        
        if result['success']:
            print(f"✅ Wallet created: {result['wallet_address']}")
            print(f"   Type: {result['wallet_type']}\n")
            
            # Test 2: Get balance
            print("Test 2: Checking wallet balance...")
            balance = wallet_manager.get_wallet_balance(result['wallet_address'])
            print(f"✅ MATIC Balance: {balance['matic_balance']}")
            print(f"✅ USDC Balance: {balance['usdc_balance']}\n")
            
            # Test 3: Export private key
            print("Test 3: Testing private key export...")
            private_key = wallet_manager.export_private_key(user_id)
            if private_key:
                print(f"✅ Private key exported successfully!")
                print(f"   Key: {private_key[:10]}...{private_key[-10:]}")
                print(f"   ⚠️ WARNING: This is sensitive data!\n")
            
            # Test 4: Get user wallet info
            print("Test 4: Getting user wallet info...")
            wallet_info = wallet_manager.get_user_wallet(user_id)
            if wallet_info:
                print(f"✅ User wallet: {wallet_info['wallet_address']}")
                print(f"   Type: {wallet_info['wallet_type']}")
                print(f"   USDC: ${wallet_info['usdc_balance']}\n")
    else:
        print("⚠️ No users in database. Create a user first!")
    
    db.close()
    print("✅ Wallet Manager test complete!")


if __name__ == "__main__":
    test_wallet_manager()