"""
Wallet Manager for Polymarket Trading Bot
Supports both in-app wallets and MetaMask connection
WITH REAL BLOCKCHAIN INTEGRATION & PRIVATE KEY EXPORT
"""

import secrets
import json
import base64
from typing import Dict, Optional
from mongodb_database import MongoDatabase
from blockchain_manager import BlockchainManager

class WalletManager:
    """
    Manages both in-app wallets and external wallet connections
    Now with REAL blockchain integration!
    """
    
    def __init__(self, db: MongoDatabase):
        """
        Initialize wallet manager with blockchain connection
        ⚠️ ENHANCED: Graceful handling if blockchain connection fails
        """
        self.db = db

        try:
            print("[WALLET] Initializing BlockchainManager...")
            self.blockchain = BlockchainManager()
            print("[WALLET] ✅ BlockchainManager initialized successfully")
        except Exception as e:
            print(f"[WALLET WARNING] ⚠️  BlockchainManager initialization failed: {e}")
            print(f"[WALLET WARNING] Wallet creation will work but without balance checking")
            self.blockchain = None

        print("[WALLET] ✅ Wallet Manager initialized")
    
    # ==================== IN-APP WALLET CREATION ====================
    
    def create_in_app_wallet(self, user_id: str) -> Dict:
        """
        Create a new in-app wallet with REAL blockchain private key
        ⚠️ FIXED: Now checks if wallet already exists to prevent address mismatch!
        ⚠️ ENHANCED: Works even if blockchain RPC is down

        Args:
            user_id: User's database ID

        Returns:
            Dictionary with wallet address and encrypted private key
        """
        try:
            from bson.objectid import ObjectId
            from eth_account import Account
            import secrets

            print(f"[WALLET] Creating in-app wallet for user: {user_id}")

            # CRITICAL FIX: Check if wallet already exists for this user
            wallets_collection = self.db.db['wallets']
            existing_wallet = wallets_collection.find_one({"user_id": user_id})

            if existing_wallet:
                print(f"[WALLET] Wallet already exists for user {user_id}")
                # Return existing wallet instead of creating a new one
                existing_address = existing_wallet.get('wallet_address')
                return {
                    "success": True,
                    "wallet_address": existing_address,
                    "wallet_type": "in-app",
                    "message": "Wallet already exists",
                    "existing": True
                }

            # Generate REAL wallet - try blockchain manager first, fallback to direct creation
            wallet_address = None
            private_key = None

            if self.blockchain:
                print(f"[WALLET] Using BlockchainManager to create wallet...")
                try:
                    wallet_result = self.blockchain.create_wallet()

                    if wallet_result.get('success'):
                        wallet_address = wallet_result['address']
                        private_key = wallet_result['private_key']
                        print(f"[WALLET] ✅ Wallet created via BlockchainManager")
                    else:
                        print(f"[WALLET WARNING] BlockchainManager failed, using fallback")
                except Exception as e:
                    print(f"[WALLET WARNING] BlockchainManager error: {e}, using fallback")

            # Fallback: Create wallet directly if blockchain manager failed
            if not wallet_address:
                print(f"[WALLET] Creating wallet directly (fallback)...")
                private_key = "0x" + secrets.token_hex(32)
                account = Account.from_key(private_key)
                wallet_address = account.address
                print(f"[WALLET] ✅ Wallet created via fallback method")

            print(f"[WALLET] Created wallet: {wallet_address}")

            # Encrypt private key before storing
            encrypted_key = self._encrypt_key(private_key)

            # Store wallet in database
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
            wallets_collection.insert_one({
                "user_id": user_id,
                "wallet_address": wallet_address,
                "private_key_encrypted": encrypted_key
            })

            print(f"[WALLET] ✅ Wallet saved to database for user {user_id}")

            return {
                "success": True,
                "wallet_address": wallet_address,
                "wallet_type": "in-app",
                "message": "Real blockchain wallet created successfully!"
            }

        except Exception as e:
            print(f"[WALLET ERROR] ❌ Error creating wallet for user {user_id}")
            print(f"[WALLET ERROR] Error type: {type(e).__name__}")
            print(f"[WALLET ERROR] Error message: {str(e)}")

            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
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
        ⚠️ ENHANCED: Better error messages for external wallets

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
                print(f"[EXPORT] ❌ User not found: {user_id}")
                return None

            wallet_type = user.get('wallet_type', 'unknown')
            wallet_address = user.get('wallet_address', 'unknown')

            print(f"[EXPORT] Export request for user {user_id}")
            print(f"[EXPORT] Wallet type: {wallet_type}")
            print(f"[EXPORT] Wallet address: {wallet_address}")

            if wallet_type != 'in-app':
                print(f"[EXPORT] ❌ Cannot export {wallet_type} wallet keys!")
                print(f"[EXPORT] External wallet keys are stored in your browser/wallet app (Rabby, MetaMask, etc.)")
                return None

            # Get encrypted private key
            wallets_collection = self.db.db['wallets']
            wallet = wallets_collection.find_one({"user_id": user_id})

            if not wallet:
                print(f"[EXPORT] ❌ Wallet private key not found in database")
                print(f"[EXPORT] This might be an external wallet or key was never stored")
                return None

            # Decrypt and return
            private_key = self._decrypt_key(wallet['private_key_encrypted'])

            print(f"[EXPORT] ⚠️  WARNING: Private key exported for user {user_id}")
            print(f"[EXPORT] Address: {wallet_address}")

            return private_key

        except Exception as e:
            print(f"[EXPORT ERROR] ❌ Error exporting private key: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    # ==================== EXTERNAL WALLET CONNECTION ====================
    
    def connect_external_wallet(self, user_id: str, wallet_address: str) -> Dict:
        """
        Connect user's external wallet (Rabby, MetaMask, WalletConnect, etc.)
        ⚠️ ENHANCED: Better validation and logging

        Args:
            user_id: User's database ID
            wallet_address: External wallet address

        Returns:
            Success status
        """
        try:
            from bson.objectid import ObjectId
            from web3 import Web3

            print(f"[CONNECT] Connecting external wallet for user {user_id}")
            print(f"[CONNECT] Wallet address provided: {wallet_address}")

            # Validate address format (works without RPC)
            if not Web3.is_address(wallet_address):
                print(f"[CONNECT] ❌ Invalid wallet address format: {wallet_address}")
                return {
                    "success": False,
                    "error": "Invalid wallet address format. Must be a valid Ethereum address (0x...)"
                }

            # Checksum the address
            wallet_address = Web3.to_checksum_address(wallet_address)
            print(f"[CONNECT] Checksummed address: {wallet_address}")

            # Check if user exists
            user = self.db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                print(f"[CONNECT] ❌ User not found: {user_id}")
                return {
                    "success": False,
                    "error": "User not found"
                }

            # Store wallet connection
            self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "wallet_address": wallet_address,
                        "wallet_type": "external"
                    }
                }
            )

            print(f"[CONNECT] ✅ Connected external wallet: {wallet_address}")
            print(f"[CONNECT] Wallet type: external (Rabby/MetaMask/etc.)")

            return {
                "success": True,
                "wallet_address": wallet_address,
                "wallet_type": "external",
                "message": "External wallet connected successfully!",
                "note": "Private keys for external wallets are stored in your browser wallet extension, not on our servers."
            }

        except Exception as e:
            print(f"[CONNECT ERROR] ❌ Error connecting wallet: {e}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    # ==================== WALLET BALANCE (REAL BLOCKCHAIN) ====================
    
    def get_wallet_balance(self, wallet_address: str) -> Dict:
        """
        Get REAL wallet balances from blockchain
        
        Args:
            wallet_address: Wallet address to check
            
        Returns:
            Dictionary with real balances from blockchain
        """
        try:
            # Get REAL balances from blockchain
            balances = self.blockchain.get_all_balances(wallet_address)
            
            return {
                "success": True,
                "wallet_address": wallet_address,
                "matic_balance": balances['matic'],
                "usdc_balance": balances['usdc'],
                "total_usd": balances['total_usd']
            }
            
        except Exception as e:
            print(f"[ERROR] Error getting balance: {e}")
            return {
                "success": False,
                "error": str(e),
                "matic_balance": 0.0,
                "usdc_balance": 0.0
            }
    
    # ==================== WALLET INFO ====================
    
    def get_user_wallet(self, user_id: str) -> Optional[Dict]:
        """
        Get user's wallet information with REAL blockchain balances
        
        Args:
            user_id: User's database ID
            
        Returns:
            Wallet information with real balances or None
        """
        try:
            from bson.objectid import ObjectId
            user = self.db.users.find_one({"_id": ObjectId(user_id)})
            
            if not user or not user.get('wallet_address'):
                return None
            
            wallet_address = user['wallet_address']
            wallet_type = user.get('wallet_type', 'unknown')
            
            # Get REAL balance from blockchain
            balance_info = self.get_wallet_balance(wallet_address)
            
            return {
                "wallet_address": wallet_address,
                "wallet_type": wallet_type,
                "matic_balance": balance_info.get('matic_balance', 0.0),
                "usdc_balance": balance_info.get('usdc_balance', 0.0),
                "total_usd": balance_info.get('total_usd', 0.0)
            }
            
        except Exception as e:
            print(f"[ERROR] Error getting wallet info: {e}")
            return None
    
    # ==================== TRANSACTIONS ====================
    
    def send_matic(self, user_id: str, to_address: str, amount: float) -> Dict:
        """
        Send MATIC from user's wallet
        
        Args:
            user_id: User's database ID
            to_address: Recipient address
            amount: Amount of MATIC to send
            
        Returns:
            Transaction result
        """
        try:
            # Get user's private key
            private_key = self.export_private_key(user_id)
            
            if not private_key:
                return {
                    "success": False,
                    "error": "Cannot access wallet private key"
                }
            
            # Send MATIC using blockchain manager
            result = self.blockchain.send_matic(private_key, to_address, amount)
            
            return result
            
        except Exception as e:
            print(f"[ERROR] Error sending MATIC: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_usdc(self, user_id: str, to_address: str, amount: float) -> Dict:
        """
        Send USDC from user's wallet
        
        Args:
            user_id: User's database ID
            to_address: Recipient address
            amount: Amount of USDC to send
            
        Returns:
            Transaction result
        """
        try:
            # Get user's private key
            private_key = self.export_private_key(user_id)
            
            if not private_key:
                return {
                    "success": False,
                    "error": "Cannot access wallet private key"
                }
            
            # Send USDC using blockchain manager
            result = self.blockchain.send_usdc(private_key, to_address, amount)
            
            return result
            
        except Exception as e:
            print(f"[ERROR] Error sending USDC: {e}")
            return {
                "success": False,
                "error": str(e)
            }


def test_wallet_manager():
    """Test wallet manager functionality with REAL blockchain"""
    print("🧪 Testing Wallet Manager with REAL BLOCKCHAIN...\n")
    
    # Initialize
    db = MongoDatabase()
    wallet_manager = WalletManager(db)
    
    # Test 1: Create in-app wallet with REAL blockchain
    print("Test 1: Creating REAL blockchain wallet...")
    
    # Get a real user from database
    user = db.users.find_one({})
    if user:
        user_id = str(user['_id'])
        
        result = wallet_manager.create_in_app_wallet(user_id)
        
        if result['success']:
            print(f"[OK] REAL Wallet created: {result['wallet_address']}")
            print(f"   Type: {result['wallet_type']}\n")
            
            # Test 2: Get REAL balance from blockchain
            print("Test 2: Checking REAL blockchain balance...")
            balance = wallet_manager.get_wallet_balance(result['wallet_address'])
            print(f"[OK] MATIC Balance: {balance['matic_balance']}")
            print(f"[OK] USDC Balance: {balance['usdc_balance']}")
            print(f"[OK] Total USD: ${balance['total_usd']:.2f}\n")
            
            # Test 3: Export private key
            print("Test 3: Testing private key export...")
            private_key = wallet_manager.export_private_key(user_id)
            if private_key:
                print(f"[OK] Private key exported successfully!")
                print(f"   Key: {private_key[:10]}...{private_key[-10:]}")
                print(f"   [WARNING] WARNING: This is a REAL private key!\n")
            
            # Test 4: Get user wallet info with REAL balances
            print("Test 4: Getting user wallet info with REAL balances...")
            wallet_info = wallet_manager.get_user_wallet(user_id)
            if wallet_info:
                print(f"[OK] User wallet: {wallet_info['wallet_address']}")
                print(f"   Type: {wallet_info['wallet_type']}")
                print(f"   REAL MATIC: {wallet_info['matic_balance']}")
                print(f"   REAL USDC: ${wallet_info['usdc_balance']:.2f}\n")
    else:
        print("[WARNING] No users in database. Create a user first!")
    
    db.close()
    print("[OK] Wallet Manager with REAL blockchain test complete!")


if __name__ == "__main__":
    test_wallet_manager()