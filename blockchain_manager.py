"""
Blockchain Manager for Polymarket Trading Bot
Handles real Web3 interactions with Polygon network
"""

from web3 import Web3
from eth_account import Account
import secrets
from typing import Dict, Optional
from decimal import Decimal

# Polygon Network Configuration
POLYGON_RPC_URL = "https://polygon-rpc.com"  # Free public RPC
POLYGON_CHAIN_ID = 137

# Token Addresses on Polygon
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # USDC on Polygon
MATIC_ADDRESS = "0x0000000000000000000000000000000000001010"  # Native MATIC

# Minimal ERC20 ABI (for balance checking and transfers)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]


class BlockchainManager:
    """
    Manages real blockchain interactions with Polygon network
    """
    
    def __init__(self):
        """Initialize Web3 connection to Polygon"""
        self.w3 = Web3(Web3.HTTPProvider(POLYGON_RPC_URL))
        self.chain_id = POLYGON_CHAIN_ID
        
        # Check connection
        if self.w3.is_connected():
            print(f"✅ Connected to Polygon Network (Chain ID: {self.chain_id})")
            print(f"📊 Latest Block: {self.w3.eth.block_number}")
        else:
            print("❌ Failed to connect to Polygon network")
        
        # Initialize USDC contract
        self.usdc_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(USDC_ADDRESS),
            abi=ERC20_ABI
        )
    
    # ==================== WALLET CREATION ====================
    
    def create_wallet(self) -> Dict:
        """
        Create a new Ethereum/Polygon wallet with real private key
        
        Returns:
            Dictionary with address and private key
        """
        try:
            # Generate random private key (secure)
            private_key = "0x" + secrets.token_hex(32)
            
            # Create account from private key
            account = Account.from_key(private_key)
            
            print(f"🔐 Created new wallet: {account.address}")
            
            return {
                "success": True,
                "address": account.address,
                "private_key": private_key
            }
            
        except Exception as e:
            print(f"❌ Error creating wallet: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def import_wallet(self, private_key: str) -> Dict:
        """
        Import existing wallet from private key
        
        Args:
            private_key: Wallet private key (with or without 0x prefix)
            
        Returns:
            Dictionary with wallet info
        """
        try:
            # Ensure 0x prefix
            if not private_key.startswith('0x'):
                private_key = '0x' + private_key
            
            # Create account from private key
            account = Account.from_key(private_key)
            
            print(f"🔐 Imported wallet: {account.address}")
            
            return {
                "success": True,
                "address": account.address
            }
            
        except Exception as e:
            print(f"❌ Error importing wallet: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== BALANCE CHECKING ====================
    
    def get_matic_balance(self, address: str) -> float:
        """
        Get MATIC balance for an address
        
        Args:
            address: Wallet address
            
        Returns:
            MATIC balance as float
        """
        try:
            # Get balance in Wei
            balance_wei = self.w3.eth.get_balance(Web3.to_checksum_address(address))
            
            # Convert to MATIC (1 MATIC = 10^18 Wei)
            balance_matic = self.w3.from_wei(balance_wei, 'ether')
            
            return float(balance_matic)
            
        except Exception as e:
            print(f"❌ Error getting MATIC balance: {e}")
            return 0.0
    
    def get_usdc_balance(self, address: str) -> float:
        """
        Get USDC balance for an address
        
        Args:
            address: Wallet address
            
        Returns:
            USDC balance as float
        """
        try:
            # Get USDC balance (USDC has 6 decimals on Polygon)
            balance_raw = self.usdc_contract.functions.balanceOf(
                Web3.to_checksum_address(address)
            ).call()
            
            # Convert to human-readable (divide by 10^6)
            balance_usdc = balance_raw / (10 ** 6)
            
            return float(balance_usdc)
            
        except Exception as e:
            print(f"❌ Error getting USDC balance: {e}")
            return 0.0
    
    def get_all_balances(self, address: str) -> Dict:
        """
        Get all token balances for an address
        
        Args:
            address: Wallet address
            
        Returns:
            Dictionary with all balances
        """
        matic_balance = self.get_matic_balance(address)
        usdc_balance = self.get_usdc_balance(address)
        
        return {
            "address": address,
            "matic": matic_balance,
            "usdc": usdc_balance,
            "matic_usd": matic_balance * 0.5,  # Approximate USD value (update with real price)
            "total_usd": (matic_balance * 0.5) + usdc_balance
        }
    
    # ==================== TRANSACTIONS ====================
    
    def send_matic(self, from_private_key: str, to_address: str, amount: float) -> Dict:
        """
        Send MATIC to another address
        
        Args:
            from_private_key: Sender's private key
            to_address: Recipient address
            amount: Amount of MATIC to send
            
        Returns:
            Transaction result
        """
        try:
            # Create account from private key
            account = Account.from_key(from_private_key)
            from_address = account.address
            
            # Get current gas price
            gas_price = self.w3.eth.gas_price
            
            # Build transaction
            transaction = {
                'from': from_address,
                'to': Web3.to_checksum_address(to_address),
                'value': self.w3.to_wei(amount, 'ether'),
                'gas': 21000,  # Standard gas limit for ETH transfer
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(from_address),
                'chainId': self.chain_id
            }
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, from_private_key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"✅ Transaction sent! Hash: {tx_hash.hex()}")
            
            # Wait for confirmation (optional)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "status": receipt['status'],
                "block_number": receipt['blockNumber']
            }
            
        except Exception as e:
            print(f"❌ Error sending MATIC: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_usdc(self, from_private_key: str, to_address: str, amount: float) -> Dict:
        """
        Send USDC to another address
        
        Args:
            from_private_key: Sender's private key
            to_address: Recipient address
            amount: Amount of USDC to send
            
        Returns:
            Transaction result
        """
        try:
            # Create account from private key
            account = Account.from_key(from_private_key)
            from_address = account.address
            
            # Convert USDC amount to raw value (6 decimals)
            amount_raw = int(amount * (10 ** 6))
            
            # Build transaction
            transaction = self.usdc_contract.functions.transfer(
                Web3.to_checksum_address(to_address),
                amount_raw
            ).build_transaction({
                'from': from_address,
                'gas': 100000,  # Gas limit for ERC20 transfer
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(from_address),
                'chainId': self.chain_id
            })
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, from_private_key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"✅ USDC transaction sent! Hash: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "status": receipt['status'],
                "block_number": receipt['blockNumber']
            }
            
        except Exception as e:
            print(f"❌ Error sending USDC: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== UTILITIES ====================
    
    def is_valid_address(self, address: str) -> bool:
        """Check if address is valid Ethereum address"""
        return self.w3.is_address(address)
    
    def get_transaction(self, tx_hash: str) -> Optional[Dict]:
        """Get transaction details by hash"""
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            return dict(tx)
        except Exception as e:
            print(f"❌ Error getting transaction: {e}")
            return None
    
    def get_gas_price(self) -> Dict:
        """Get current gas price"""
        try:
            gas_price_wei = self.w3.eth.gas_price
            gas_price_gwei = self.w3.from_wei(gas_price_wei, 'gwei')
            
            return {
                "gas_price_wei": gas_price_wei,
                "gas_price_gwei": float(gas_price_gwei)
            }
        except Exception as e:
            print(f"❌ Error getting gas price: {e}")
            return {"gas_price_gwei": 0}


def test_blockchain_manager():
    """Test blockchain manager functionality"""
    print("🧪 Testing Blockchain Manager...\n")
    
    # Initialize
    blockchain = BlockchainManager()
    
    # Test 1: Create wallet
    print("\n📝 Test 1: Creating new wallet...")
    wallet = blockchain.create_wallet()
    if wallet['success']:
        print(f"✅ Wallet Address: {wallet['address']}")
        print(f"   Private Key: {wallet['private_key'][:20]}...{wallet['private_key'][-10:]}")
        
        # Test 2: Check balances
        print("\n📝 Test 2: Checking balances...")
        balances = blockchain.get_all_balances(wallet['address'])
        print(f"✅ MATIC Balance: {balances['matic']}")
        print(f"✅ USDC Balance: {balances['usdc']}")
        print(f"✅ Total USD Value: ${balances['total_usd']:.2f}")
    
    # Test 3: Check a known address with balance (Vitalik's address for example)
    print("\n📝 Test 3: Checking real address...")
    vitalik = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    balances = blockchain.get_all_balances(vitalik)
    print(f"✅ Address: {vitalik}")
    print(f"   MATIC Balance: {balances['matic']}")
    print(f"   USDC Balance: {balances['usdc']}")
    
    # Test 4: Get gas price
    print("\n📝 Test 4: Getting gas price...")
    gas = blockchain.get_gas_price()
    print(f"✅ Current Gas Price: {gas['gas_price_gwei']:.2f} Gwei")
    
    print("\n✅ Blockchain Manager test complete!")


if __name__ == "__main__":
    test_blockchain_manager()