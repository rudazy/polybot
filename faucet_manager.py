"""
Faucet Manager for Polymarket Trading Bot
Helps users get test tokens and fund their wallets
"""

import requests
import time
from typing import Dict, Optional
from blockchain_manager import BlockchainManager

# Polygon Mumbai Testnet Faucets (for testing)
POLYGON_FAUCET_URL = "https://faucet.polygon.technology/"
ALCHEMY_FAUCET = "https://mumbaifaucet.com/"

# Test Token Amounts
TEST_MATIC_AMOUNT = 0.1  # Small amount for testing
TEST_USDC_AMOUNT = 10.0  # $10 USDC for testing


class FaucetManager:
    """
    Manages test token distribution and wallet funding
    """
    
    def __init__(self, blockchain: BlockchainManager):
        """Initialize faucet manager"""
        self.blockchain = blockchain
        print("✅ Faucet Manager initialized")
    
    # ==================== POLYGON FAUCET ====================
    
    def get_polygon_faucet_instructions(self, wallet_address: str) -> Dict:
        """
        Get instructions for claiming Polygon MATIC from faucets
        
        Args:
            wallet_address: User's wallet address
            
        Returns:
            Dictionary with faucet URLs and instructions
        """
        return {
            "wallet_address": wallet_address,
            "instructions": "Visit these faucets to get free test MATIC:",
            "faucets": [
                {
                    "name": "Official Polygon Faucet",
                    "url": "https://faucet.polygon.technology/",
                    "amount": "0.5 MATIC",
                    "requirements": "None - just paste your address",
                    "wait_time": "24 hours between claims"
                },
                {
                    "name": "Alchemy Faucet",
                    "url": "https://mumbaifaucet.com/",
                    "amount": "0.5 MATIC",
                    "requirements": "Alchemy account (free)",
                    "wait_time": "24 hours between claims"
                },
                {
                    "name": "QuickNode Faucet",
                    "url": "https://faucet.quicknode.com/polygon/mumbai",
                    "amount": "0.1 MATIC",
                    "requirements": "Twitter account",
                    "wait_time": "12 hours between claims"
                }
            ],
            "note": "Copy your wallet address and paste it on any of these faucet sites to get free test MATIC."
        }
    
    # ==================== BALANCE CHECKING ====================
    
    def check_funding_status(self, wallet_address: str) -> Dict:
        """
        Check if wallet has been funded
        
        Args:
            wallet_address: Wallet to check
            
        Returns:
            Funding status with recommendations
        """
        try:
            from web3 import Web3
        checksummed_address = Web3.to_checksum_address(wallet_address)
        balances = self.blockchain.get_all_balances(checksummed_address)
            
            matic_balance = balances['matic']
            usdc_balance = balances['usdc']
            
            # Determine funding status
            needs_matic = matic_balance < 0.01
            needs_usdc = usdc_balance < 1.0
            
            status = {
                "wallet_address": wallet_address,
                "matic_balance": matic_balance,
                "usdc_balance": usdc_balance,
                "needs_funding": needs_matic or needs_usdc,
                "recommendations": []
            }
            
            if needs_matic:
                status["recommendations"].append({
                    "token": "MATIC",
                    "reason": "Need MATIC for gas fees",
                    "action": "Visit Polygon faucet to get free MATIC",
                    "min_amount": 0.01
                })
            
            if needs_usdc:
                status["recommendations"].append({
                    "token": "USDC",
                    "reason": "Need USDC for trading",
                    "action": "Get USDC from exchange or swap",
                    "min_amount": 10.0
                })
            
            if not needs_matic and not needs_usdc:
                status["message"] = "✅ Wallet is funded and ready to trade!"
            else:
                status["message"] = "⚠️ Wallet needs funding before trading"
            
            return status
            
        except Exception as e:
            print(f"❌ Error checking funding status: {e}")
            return {
                "error": str(e),
                "needs_funding": True
            }
    
    # ==================== FUNDING GUIDE ====================
    
    def get_funding_guide(self) -> Dict:
        """
        Get comprehensive guide for funding wallet
        
        Returns:
            Step-by-step funding guide
        """
        return {
            "title": "How to Fund Your Wallet",
            "steps": [
                {
                    "step": 1,
                    "title": "Get MATIC (for gas fees)",
                    "description": "You need MATIC to pay for transaction fees on Polygon",
                    "methods": [
                        "Use Polygon Faucet (free for testing)",
                        "Buy on Coinbase/Binance and transfer",
                        "Bridge from Ethereum using Polygon Bridge"
                    ]
                },
                {
                    "step": 2,
                    "title": "Get USDC (for trading)",
                    "description": "USDC is used for trading on Polymarket",
                    "methods": [
                        "Buy USDC on exchange (Coinbase/Binance)",
                        "Transfer USDC to Polygon network",
                        "Swap other tokens for USDC on QuickSwap"
                    ]
                },
                {
                    "step": 3,
                    "title": "Transfer to your wallet",
                    "description": "Send tokens to your wallet address",
                    "important": [
                        "⚠️ Make sure to use Polygon network (not Ethereum!)",
                        "⚠️ Double-check wallet address before sending",
                        "⚠️ Start with small test amount first"
                    ]
                },
                {
                    "step": 4,
                    "title": "Verify receipt",
                    "description": "Check your wallet balance to confirm",
                    "action": "Refresh balance in dashboard"
                }
            ],
            "quick_links": {
                "polygon_faucet": "https://faucet.polygon.technology/",
                "coinbase": "https://www.coinbase.com/",
                "polygon_bridge": "https://wallet.polygon.technology/polygon/bridge",
                "quickswap": "https://quickswap.exchange/"
            }
        }
    
    # ==================== TRANSACTION MONITORING ====================
    
    def wait_for_funding(self, wallet_address: str, timeout: int = 300) -> Dict:
        """
        Wait for wallet to receive funds (useful for testing)
        
        Args:
            wallet_address: Wallet to monitor
            timeout: Maximum wait time in seconds
            
        Returns:
            Status when funds received or timeout
        """
        print(f"⏳ Monitoring {wallet_address} for incoming funds...")
        
        start_time = time.time()
        initial_balances = self.blockchain.get_all_balances(wallet_address)
        
        while time.time() - start_time < timeout:
            current_balances = self.blockchain.get_all_balances(wallet_address)
            
            # Check if any balance increased
            if (current_balances['matic'] > initial_balances['matic'] or 
                current_balances['usdc'] > initial_balances['usdc']):
                
                print(f"✅ Funds received!")
                return {
                    "success": True,
                    "funded": True,
                    "matic_received": current_balances['matic'] - initial_balances['matic'],
                    "usdc_received": current_balances['usdc'] - initial_balances['usdc'],
                    "new_balances": current_balances
                }
            
            time.sleep(10)  # Check every 10 seconds
        
        print("⏱️ Timeout - no funds received")
        return {
            "success": False,
            "funded": False,
            "message": "Timeout waiting for funds"
        }
    
    # ==================== MINIMUM BALANCE CHECKS ====================
    
    def has_sufficient_gas(self, wallet_address: str, estimated_gas: float = 0.01) -> bool:
        """
        Check if wallet has enough MATIC for gas
        
        Args:
            wallet_address: Wallet to check
            estimated_gas: Estimated gas needed in MATIC
            
        Returns:
            True if sufficient gas available
        """
        matic_balance = self.blockchain.get_matic_balance(wallet_address)
        return matic_balance >= estimated_gas
    
    def has_sufficient_trading_balance(self, wallet_address: str, trade_amount: float) -> bool:
        """
        Check if wallet has enough USDC for trading
        
        Args:
            wallet_address: Wallet to check
            trade_amount: Required USDC amount
            
        Returns:
            True if sufficient balance available
        """
        usdc_balance = self.blockchain.get_usdc_balance(wallet_address)
        return usdc_balance >= trade_amount
    
    def get_funding_requirements(self, trade_amount: float) -> Dict:
        """
        Calculate funding requirements for a trade
        
        Args:
            trade_amount: Desired trade size in USDC
            
        Returns:
            Required balances
        """
        # Estimate gas costs (rough approximation)
        estimated_gas_matic = 0.05  # ~0.05 MATIC for multiple transactions
        gas_cost_usd = estimated_gas_matic * 0.5  # Approximate USD value
        
        return {
            "trade_amount_usdc": trade_amount,
            "required_usdc": trade_amount,
            "required_matic": estimated_gas_matic,
            "estimated_gas_cost_usd": gas_cost_usd,
            "total_required_usd": trade_amount + gas_cost_usd,
            "recommendation": f"Fund wallet with at least ${trade_amount + 5:.2f} USDC and 0.1 MATIC"
        }


def test_faucet_manager():
    """Test faucet manager functionality"""
    print("🧪 Testing Faucet Manager...\n")
    
    # Initialize
    from blockchain_manager import BlockchainManager
    blockchain = BlockchainManager()
    faucet = FaucetManager(blockchain)
    
    # Test 1: Get faucet instructions
    print("📝 Test 1: Getting faucet instructions...")
    test_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    instructions = faucet.get_polygon_faucet_instructions(test_address)
    print(f"✅ Address: {instructions['wallet_address']}")
    print(f"   Available faucets: {len(instructions['faucets'])}")
    for faucet_info in instructions['faucets']:
        print(f"   - {faucet_info['name']}: {faucet_info['amount']}")
    
    # Test 2: Check funding status
    print("\n📝 Test 2: Checking funding status...")
    status = faucet.check_funding_status(test_address)
    print(f"✅ MATIC Balance: {status['matic_balance']}")
    print(f"   USDC Balance: {status['usdc_balance']}")
    print(f"   Needs Funding: {status['needs_funding']}")
    if status['recommendations']:
        print(f"   Recommendations: {len(status['recommendations'])}")
    
    # Test 3: Get funding guide
    print("\n📝 Test 3: Getting funding guide...")
    guide = faucet.get_funding_guide()
    print(f"✅ {guide['title']}")
    print(f"   Steps: {len(guide['steps'])}")
    
    # Test 4: Calculate funding requirements
    print("\n📝 Test 4: Calculating funding requirements...")
    requirements = faucet.get_funding_requirements(100.0)
    print(f"✅ Trade Amount: ${requirements['trade_amount_usdc']}")
    print(f"   Required USDC: ${requirements['required_usdc']}")
    print(f"   Required MATIC: {requirements['required_matic']}")
    print(f"   Total USD: ${requirements['total_required_usd']:.2f}")
    
    # Test 5: Check gas sufficiency
    print("\n📝 Test 5: Checking gas sufficiency...")
    has_gas = faucet.has_sufficient_gas(test_address)
    print(f"✅ Has sufficient gas: {has_gas}")
    
    print("\n✅ Faucet Manager test complete!")


if __name__ == "__main__":
    test_faucet_manager()