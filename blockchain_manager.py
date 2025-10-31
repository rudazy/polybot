"""
Blockchain Manager for Polymarket Trading Bot
Handles real Web3 interactions with Polygon network
NOW WITH TESTNET/MAINNET SWITCHING!
"""

from web3 import Web3
from eth_account import Account
import secrets
from typing import Dict, Optional
from decimal import Decimal

# Network Configurations
NETWORKS = {
    "mainnet": {
        "name": "Polygon Mainnet",
        "rpc_url": "https://polygon-rpc.com",
        "chain_id": 137,
        "usdc_address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "explorer": "https://polygonscan.com",
        "currency_symbol": "MATIC"
    },
    "testnet": {
        "name": "Mumbai Testnet", 
        "rpc_url": "https://rpc-mumbai.maticvigil.com",
        "chain_id": 80001,
        "usdc_address": "0x0FA8781a83E46826621b3BC094Ea2A0212e71B23",  # Test USDC
        "explorer": "https://mumbai.polygonscan.com",
        "currency_symbol": "MATIC (Test)"
    }
}

# Default network - START WITH TESTNET FOR SAFETY!
DEFAULT_NETWORK = "testnet"

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
    Supports both TESTNET (Mumbai) and MAINNET (Polygon)
    """
    
    def __init__(self, network: str = DEFAULT_NETWORK):
        """
        Initialize Web3 connection to Polygon
        
        Args:
            network: "testnet" for Mumbai or "mainnet" for Polygon
        """
        if network not in NETWORKS:
            raise ValueError(f"Invalid network: {network}. Use 'testnet' or 'mainnet'")
        
        self.network = network
        self.network_config = NETWORKS[network]
        self.w3 = Web3(Web3.HTTPProvider(self.network_config["rpc_url"]))
        self.chain_id = self.network_config["chain_id"]
        
        # Check connection
        if self.w3.is_connected():
            print(f"[OK] Connected to {self.network_config['name']} (Chain ID: {self.chain_id})")
            print(f"[INFO] Latest Block: {self.w3.eth.block_number}")
            if network == "testnet":
                print(f"[TEST] TESTNET MODE - Using test tokens (no real money)")
            else:
                print(f"[MAINNET] MAINNET MODE - Using REAL tokens!")
        else:
            print(f"[ERROR] Failed to connect to {self.network_config['name']}")
        
        # Initialize USDC contract
        self.usdc_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.network_config["usdc_address"]),
            abi=ERC20_ABI
        )
    
    # ==================== NETWORK SWITCHING ====================
    
    def switch_network(self, network: str) -> bool:
        """
        Switch between testnet and mainnet
        
        Args:
            network: "testnet" or "mainnet"
            
        Returns:
            Success status
        """
        try:
            if network not in NETWORKS:
                print(f"[ERROR] Invalid network: {network}")
                return False
            
            print(f"[SWITCH] Switching to {NETWORKS[network]['name']}...")
            self.__init__(network)
            return True
            
        except Exception as e:
            print(f"[ERROR] Error switching network: {e}")
            return False
    
    def get_network_info(self) -> Dict:
        """Get current network information"""
        return {
            "network": self.network,
            "name": self.network_config["name"],
            "chain_id": self.chain_id,
            "explorer": self.network_config["explorer"],
            "is_testnet": self.network == "testnet",
            "currency_symbol": self.network_config["currency_symbol"]
        }
    
    def get_faucet_info(self) -> Optional[Dict]:
        """Get faucet information for testnet"""
        if self.network != "testnet":
            return None
        
        return {
            "message": "Get free test tokens from these faucets:",
            "faucets": [
                {
                    "name": "Mumbai Faucet",
                    "url": "https://faucet.polygon.technology/",
                    "tokens": ["MATIC"]
                },
                {
                    "name": "Alchemy Faucet",
                    "url": "https://mumbaifaucet.com/",
                    "tokens": ["MATIC"]
                }
            ]
        }
    
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
            
            network_info = f" ({self.network_config['name']})"
            print(f"🔐 Created new wallet{network_info}: {account.address}")
            
            return {
                "success": True,
                "address": account.address,
                "private_key": private_key,
                "network": self.network
            }
            
        except Exception as e:
            print(f"[ERROR] Error creating wallet: {e}")
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
                "address": account.address,
                "network": self.network
            }
            
        except Exception as e:
            print(f"[ERROR] Error importing wallet: {e}")
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
            print(f"[ERROR] Error getting MATIC balance: {e}")
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
            print(f"[ERROR] Error getting USDC balance: {e}")
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
            "network": self.network,
            "matic": matic_balance,
            "usdc": usdc_balance,
            "matic_usd": matic_balance * 0.5,  # Approximate USD value
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
            
            print(f"[OK] Transaction sent! Hash: {tx_hash.hex()}")
            print(f"🔗 View on explorer: {self.network_config['explorer']}/tx/{tx_hash.hex()}")
            
            # Wait for confirmation (optional)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "status": receipt['status'],
                "block_number": receipt['blockNumber'],
                "explorer_url": f"{self.network_config['explorer']}/tx/{tx_hash.hex()}",
                "network": self.network
            }
            
        except Exception as e:
            print(f"[ERROR] Error sending MATIC: {e}")
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
            
            print(f"[OK] USDC transaction sent! Hash: {tx_hash.hex()}")
            print(f"🔗 View on explorer: {self.network_config['explorer']}/tx/{tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "status": receipt['status'],
                "block_number": receipt['blockNumber'],
                "explorer_url": f"{self.network_config['explorer']}/tx/{tx_hash.hex()}",
                "network": self.network
            }
            
        except Exception as e:
            print(f"[ERROR] Error sending USDC: {e}")
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
            print(f"[ERROR] Error getting transaction: {e}")
            return None
    
    def get_gas_price(self) -> Dict:
        """Get current gas price"""
        try:
            gas_price_wei = self.w3.eth.gas_price
            gas_price_gwei = self.w3.from_wei(gas_price_wei, 'gwei')
            
            return {
                "gas_price_wei": gas_price_wei,
                "gas_price_gwei": float(gas_price_gwei),
                "network": self.network
            }
        except Exception as e:
            print(f"[ERROR] Error getting gas price: {e}")
            return {"gas_price_gwei": 0}


def test_blockchain_manager():
    """Test blockchain manager functionality with network switching"""
    print("[TEST] Testing Blockchain Manager with Network Switching...\n")
    
    # Test 1: Start with TESTNET (default)
    print("=" * 60)
    print("TEST 1: Creating wallet on TESTNET")
    print("=" * 60)
    blockchain_testnet = BlockchainManager("testnet")
    
    wallet = blockchain_testnet.create_wallet()
    if wallet['success']:
        print(f"[OK] Testnet Wallet: {wallet['address']}")
        print(f"   Network: {wallet['network']}")
        
        # Check testnet balance
        balances = blockchain_testnet.get_all_balances(wallet['address'])
        print(f"[OK] Testnet MATIC: {balances['matic']}")
        print(f"[OK] Testnet USDC: {balances['usdc']}")
        
        # Get faucet info
        faucet = blockchain_testnet.get_faucet_info()
        if faucet:
            print(f"\n💧 {faucet['message']}")
            for f in faucet['faucets']:
                print(f"   - {f['name']}: {f['url']}")
    
    # Test 2: Switch to MAINNET
    print("\n" + "=" * 60)
    print("TEST 2: Switching to MAINNET")
    print("=" * 60)
    blockchain_mainnet = BlockchainManager("mainnet")
    
    # Check Vitalik's address on mainnet
    vitalik = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    balances_main = blockchain_mainnet.get_all_balances(vitalik)
    print(f"[OK] Mainnet Address: {vitalik}")
    print(f"   MATIC Balance: {balances_main['matic']}")
    print(f"   USDC Balance: {balances_main['usdc']}")
    
    # Test 3: Network info
    print("\n" + "=" * 60)
    print("TEST 3: Network Information")
    print("=" * 60)
    testnet_info = blockchain_testnet.get_network_info()
    mainnet_info = blockchain_mainnet.get_network_info()
    
    print(f"Testnet: {testnet_info['name']} (Chain ID: {testnet_info['chain_id']})")
    print(f"Mainnet: {mainnet_info['name']} (Chain ID: {mainnet_info['chain_id']})")
    
    print("\n[OK] Blockchain Manager with Network Switching test complete!")
    print("\n💡 TIP: Users can safely test on TESTNET before using MAINNET!")


if __name__ == "__main__":
    test_blockchain_manager()