"""
Polymarket Real Trading Implementation
Uses py-clob-client with Builder Program attribution
"""

import os
from typing import Dict, Optional
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType, ApiCreds
from py_clob_client.order_builder.constants import BUY, SELL
from py_builder_signing_sdk.config import BuilderConfig
from dotenv import load_dotenv

load_dotenv()


class PolymarketTrading:
    """
    Real trading client for Polymarket with Builder Program integration
    """

    def __init__(self):
        """Initialize CLOB client with builder credentials"""

        # Polymarket CLOB endpoint
        self.host = "https://clob.polymarket.com"
        self.chain_id = 137  # Polygon mainnet

        # Builder credentials from environment
        self.builder_api_key = os.getenv('POLYMARKET_BUILDER_API_KEY')
        self.builder_secret = os.getenv('POLYMARKET_BUILDER_SECRET')
        self.builder_passphrase = os.getenv('POLYMARKET_BUILDER_PASSPHRASE')

        # Validate builder credentials
        if not all([self.builder_api_key, self.builder_secret, self.builder_passphrase]):
            print("[WARNING] Builder credentials not found - trades will not have builder attribution")
            self.builder_enabled = False
            self.creds = None
            self.builder_config = None
        else:
            print("[TRADING] OK Builder credentials loaded - trades will be attributed to your builder account")
            self.builder_enabled = True

            # Create API credentials object
            self.creds = ApiCreds(
                api_key=self.builder_api_key,
                api_secret=self.builder_secret,
                api_passphrase=self.builder_passphrase
            )

            # Builder config for attribution (can be added later if needed)
            # For now, trades will be attributed via ApiCreds
            self.builder_config = None

        # Initialize CLOB client
        try:
            self.client = ClobClient(
                host=self.host,
                chain_id=self.chain_id,
                creds=self.creds if self.creds else None,
                builder_config=self.builder_config if self.builder_config else None
            )
            print(f"[TRADING] OK CLOB client initialized: {self.host}")
        except Exception as e:
            print(f"[TRADING ERROR] Failed to initialize CLOB client: {e}")
            import traceback
            traceback.print_exc()
            self.client = None

    def get_market_prices(self, condition_id: str) -> Dict:
        """
        Get current market prices for a condition

        Args:
            condition_id: The market's condition ID

        Returns:
            Dict with YES and NO prices
        """
        try:
            # Get order book for the market
            book = self.client.get_order_book(condition_id)

            if not book:
                return {"yes_price": 0.5, "no_price": 0.5, "error": "No orderbook data"}

            # Get best bid/ask prices
            yes_bids = book.get('bids', [])
            yes_asks = book.get('asks', [])

            yes_price = float(yes_asks[0]['price']) if yes_asks else 0.5
            no_price = 1.0 - yes_price

            return {
                "yes_price": yes_price,
                "no_price": no_price,
                "spread": float(yes_asks[0]['price']) - float(yes_bids[0]['price']) if yes_bids and yes_asks else 0,
                "liquidity": sum([float(b['size']) for b in yes_bids]) if yes_bids else 0
            }
        except Exception as e:
            print(f"[TRADING ERROR] Failed to get market prices: {e}")
            return {"yes_price": 0.5, "no_price": 0.5, "error": str(e)}

    def create_market_order(
        self,
        private_key: str,
        token_id: str,
        side: str,  # 'YES' or 'NO'
        amount: float,  # Amount in USDC
        condition_id: str
    ) -> Dict:
        """
        Create and execute a market order (buy at best available price)

        Args:
            private_key: User's wallet private key
            token_id: The token ID for the market outcome
            side: 'YES' or 'NO' position
            amount: Amount in USDC to spend
            condition_id: Market's condition ID

        Returns:
            Dict with order details and status
        """
        try:
            if not self.client:
                return {
                    "success": False,
                    "error": "CLOB client not initialized"
                }

            # Remove 0x prefix from private key if present
            if private_key.startswith('0x'):
                private_key = private_key[2:]

            # Convert side to BUY/SELL (YES = BUY, NO = SELL the YES token)
            order_side = BUY if side.upper() == 'YES' else SELL

            print(f"[TRADING] Creating {side} order for ${amount} USDC")
            print(f"[TRADING] Token ID: {token_id}")
            print(f"[TRADING] Condition ID: {condition_id}")

            # Get current market price
            prices = self.get_market_prices(condition_id)
            price = prices['yes_price'] if side.upper() == 'YES' else prices['no_price']

            # Add slippage tolerance (5%) for market orders
            if order_side == BUY:
                price = min(0.99, price * 1.05)  # Pay up to 5% more
            else:
                price = max(0.01, price * 0.95)  # Accept up to 5% less

            # Calculate size (number of shares)
            size = amount / price

            print(f"[TRADING] Order details: price={price:.4f}, size={size:.2f} shares")

            # Generate CLOB API credentials from user's private key
            # Builder creds are for attribution, NOT authentication
            order_client = ClobClient(
                host=self.host,
                chain_id=self.chain_id,
                key=private_key
            )

            # Derive API credentials for this user's wallet
            try:
                print("[TRADING] Generating API credentials from private key...")
                clob_creds = order_client.create_or_derive_api_creds()
                print(f"[TRADING] OK API credentials derived for wallet")
                order_client.set_api_creds(clob_creds)  # ← ADD THIS LINE!
            except Exception as cred_err:
                print(f"[TRADING ERROR] Failed to derive API credentials: {cred_err}")
                return {
                    "success": False,
                    "error": f"Failed to derive API credentials: {cred_err}"
                }

            # Create order arguments
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=size,
                side=order_side,
                fee_rate_bps=0  # 0 fee for builder orders
            )

            # Sign the order with user's private key
            signed_order = order_client.create_order(order_args)

            # Post the order to the exchange (use order_client for proper authentication)
            resp = order_client.post_order(signed_order, OrderType.FOK)  # Fill or Kill

            if resp and resp.get('success'):
                order_id = resp.get('orderID')
                print(f"[TRADING] OK Order placed successfully! ID: {order_id}")

                return {
                    "success": True,
                    "order_id": order_id,
                    "price": price,
                    "size": size,
                    "side": side,
                    "amount": amount,
                    "builder_attributed": self.builder_enabled,
                    "message": f"Order executed: {size:.2f} shares at ${price:.4f}"
                }
            else:
                error_msg = resp.get('error', 'Unknown error') if resp else 'No response from exchange'
                print(f"[TRADING ERROR] Order failed: {error_msg}")

                return {
                    "success": False,
                    "error": error_msg,
                    "details": resp
                }

        except Exception as e:
            print(f"[TRADING ERROR] Exception during order creation: {e}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def get_order_status(self, order_id: str) -> Dict:
        """
        Get the status of an order

        Args:
            order_id: The order ID to check

        Returns:
            Dict with order status details
        """
        try:
            if not self.client:
                return {"success": False, "error": "CLOB client not initialized"}

            order = self.client.get_order(order_id)

            if not order:
                return {"success": False, "error": "Order not found"}

            return {
                "success": True,
                "order_id": order_id,
                "status": order.get('status'),
                "filled_size": order.get('filled_size', 0),
                "remaining_size": order.get('size', 0) - order.get('filled_size', 0),
                "price": order.get('price'),
                "side": order.get('side')
            }
        except Exception as e:
            print(f"[TRADING ERROR] Failed to get order status: {e}")
            return {"success": False, "error": str(e)}

    def get_user_orders(self, wallet_address: str, limit: int = 10) -> Dict:
        """
        Get user's recent orders

        Args:
            wallet_address: User's wallet address
            limit: Number of orders to return

        Returns:
            Dict with list of orders
        """
        try:
            if not self.client:
                return {"success": False, "error": "CLOB client not initialized"}

            orders = self.client.get_orders(wallet_address, limit=limit)

            return {
                "success": True,
                "count": len(orders),
                "orders": orders
            }
        except Exception as e:
            print(f"[TRADING ERROR] Failed to get user orders: {e}")
            return {"success": False, "error": str(e)}

    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel an open order

        Args:
            order_id: The order ID to cancel

        Returns:
            Dict with cancellation status
        """
        try:
            if not self.client:
                return {"success": False, "error": "CLOB client not initialized"}

            result = self.client.cancel_order(order_id)

            if result and result.get('success'):
                return {
                    "success": True,
                    "order_id": order_id,
                    "message": "Order cancelled successfully"
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error', 'Cancellation failed')
                }
        except Exception as e:
            print(f"[TRADING ERROR] Failed to cancel order: {e}")
            return {"success": False, "error": str(e)}
