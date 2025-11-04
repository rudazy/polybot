"""
Polymarket Builder Program Integration

This module provides a Python wrapper for the Node.js microservice
that handles Polymarket Builder Program functionality (gasless trading).

Architecture:
    Python Backend (this file) → Node.js Microservice → Polymarket CLOB API

Features:
    - Deploy Safe wallets (FREE GAS via relayer)
    - Create gasless orders with builder attribution
    - Cancel orders (gasless)
    - Query order status

Usage:
    builder = PolymarketBuilder()

    # Deploy Safe wallet
    result = builder.deploy_safe(private_key, owner_address)
    safe_address = result['safeAddress']

    # Create order (gasless!)
    order = builder.create_order(
        private_key=private_key,
        safe_address=safe_address,
        token_id="21742633143463906290569050155826241533067272736897614950488156847949938836455",
        side="BUY",
        price=0.75,
        size=10
    )
"""

import os
import requests
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class PolymarketBuilder:
    """
    Python wrapper for Polymarket Builder Program Node.js microservice.

    This class provides methods to interact with the Node.js service
    running on port 3001, which handles gasless trading via Polymarket's
    Builder Program relayer.
    """

    def __init__(self, node_service_url: str = None):
        """
        Initialize the PolymarketBuilder client.

        Args:
            node_service_url: URL of the Node.js microservice (default: http://localhost:3001)
        """
        self.node_service_url = node_service_url or os.environ.get(
            'POLYMARKET_NODE_SERVICE_URL',
            'http://localhost:3001'
        )
        logger.info(f"[BUILDER] Initialized with service URL: {self.node_service_url}")

    def health_check(self) -> Dict:
        """
        Check if the Node.js microservice is running and healthy.

        Returns:
            Dict with health status information

        Example:
            >>> builder = PolymarketBuilder()
            >>> status = builder.health_check()
            >>> print(status['status'])  # 'ok'
        """
        try:
            response = requests.get(
                f"{self.node_service_url}/health",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"[BUILDER] Health check failed: {e}")
            return {
                "success": False,
                "error": "Node.js microservice not reachable",
                "details": str(e)
            }

    def deploy_safe(self, private_key: str, owner_address: str) -> Dict:
        """
        Deploy a Safe wallet for gasless trading (FREE GAS via Polymarket relayer).

        This is a one-time operation per user. Once deployed, the Safe address
        can be reused for all future trades.

        Args:
            private_key: User's private key (0x...)
            owner_address: User's wallet address (0x...)

        Returns:
            Dict containing:
                - success: bool
                - safeAddress: str (0x...)
                - owner: str (0x...)
                - message: str
                - gasless: bool (True)

        Example:
            >>> result = builder.deploy_safe(
            ...     private_key="0x123...",
            ...     owner_address="0xabc..."
            ... )
            >>> safe_address = result['safeAddress']
            >>> print(f"Safe deployed at: {safe_address}")
        """
        try:
            logger.info(f"[BUILDER] Deploying Safe wallet for owner: {owner_address}")

            response = requests.post(
                f"{self.node_service_url}/deploy-safe",
                json={
                    "privateKey": private_key,
                    "ownerAddress": owner_address
                },
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            if result.get('success'):
                logger.info(f"[BUILDER] ✅ Safe deployed: {result.get('safeAddress')}")
            else:
                logger.error(f"[BUILDER] ❌ Safe deployment failed: {result.get('error')}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"[BUILDER] Deploy Safe request failed: {e}")
            return {
                "success": False,
                "error": "Failed to deploy Safe wallet",
                "details": str(e)
            }

    def get_safe_address(self, private_key: str) -> Dict:
        """
        Get the Safe wallet address for a user without deploying.

        Useful to check if a Safe wallet already exists or what the
        deterministic address would be.

        Args:
            private_key: User's private key (0x...)

        Returns:
            Dict containing:
                - success: bool
                - safeAddress: str (0x...)
                - deployed: bool

        Example:
            >>> result = builder.get_safe_address("0x123...")
            >>> if result['deployed']:
            ...     print(f"Safe exists at: {result['safeAddress']}")
        """
        try:
            response = requests.post(
                f"{self.node_service_url}/get-safe-address",
                json={"privateKey": private_key},
                timeout=10
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"[BUILDER] Get Safe address request failed: {e}")
            return {
                "success": False,
                "error": "Failed to get Safe address",
                "details": str(e)
            }

    def create_order(
        self,
        private_key: str,
        safe_address: str,
        token_id: str,
        side: str,
        price: float,
        size: float
    ) -> Dict:
        """
        Create a gasless order with builder attribution (NO GAS FEES!).

        This order will be attributed to "Polybot.finance" in the Builder Program,
        tracking volume and making you eligible for grants.

        Args:
            private_key: User's private key (0x...)
            safe_address: User's Safe wallet address (0x...)
            token_id: Market token ID (long string)
            side: "BUY" or "SELL"
            price: Order price (0.0 to 1.0, e.g., 0.75 = 75%)
            size: Order size in USDC (e.g., 10 = $10)

        Returns:
            Dict containing:
                - success: bool
                - orderID: str (0x...)
                - order: dict (order details)
                - message: str
                - gasless: bool (True)
                - builderAttribution: bool (True)

        Example:
            >>> order = builder.create_order(
            ...     private_key="0x123...",
            ...     safe_address="0xabc...",
            ...     token_id="21742633143463906290569050155826241533067272736897614950488156847949938836455",
            ...     side="BUY",
            ...     price=0.75,
            ...     size=10
            ... )
            >>> print(f"Order placed: {order['orderID']}")
        """
        try:
            logger.info(f"[BUILDER] Creating {side} order: {size} @ {price}")

            response = requests.post(
                f"{self.node_service_url}/create-order",
                json={
                    "privateKey": private_key,
                    "safeAddress": safe_address,
                    "tokenID": token_id,
                    "side": side.upper(),
                    "price": str(price),
                    "size": str(size)
                },
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            if result.get('success'):
                logger.info(f"[BUILDER] ✅ Order created: {result.get('orderID')}")
            else:
                logger.error(f"[BUILDER] ❌ Order failed: {result.get('error')}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"[BUILDER] Create order request failed: {e}")
            return {
                "success": False,
                "error": "Failed to create order",
                "details": str(e)
            }

    def cancel_order(
        self,
        private_key: str,
        safe_address: str,
        order_id: str
    ) -> Dict:
        """
        Cancel an existing order (gasless).

        Args:
            private_key: User's private key (0x...)
            safe_address: User's Safe wallet address (0x...)
            order_id: Order ID to cancel (0x...)

        Returns:
            Dict containing:
                - success: bool
                - message: str
                - gasless: bool (True)

        Example:
            >>> result = builder.cancel_order(
            ...     private_key="0x123...",
            ...     safe_address="0xabc...",
            ...     order_id="0xdef..."
            ... )
        """
        try:
            logger.info(f"[BUILDER] Canceling order: {order_id}")

            response = requests.post(
                f"{self.node_service_url}/cancel-order",
                json={
                    "privateKey": private_key,
                    "safeAddress": safe_address,
                    "orderID": order_id
                },
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            if result.get('success'):
                logger.info(f"[BUILDER] ✅ Order canceled: {order_id}")
            else:
                logger.error(f"[BUILDER] ❌ Cancel failed: {result.get('error')}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"[BUILDER] Cancel order request failed: {e}")
            return {
                "success": False,
                "error": "Failed to cancel order",
                "details": str(e)
            }

    def get_orders(
        self,
        private_key: str,
        safe_address: str
    ) -> Dict:
        """
        Get all orders for a Safe wallet.

        Args:
            private_key: User's private key (0x...)
            safe_address: User's Safe wallet address (0x...)

        Returns:
            Dict containing:
                - success: bool
                - orders: List[dict]
                - count: int

        Example:
            >>> result = builder.get_orders("0x123...", "0xabc...")
            >>> for order in result['orders']:
            ...     print(f"Order: {order['id']} - {order['side']} @ {order['price']}")
        """
        try:
            response = requests.post(
                f"{self.node_service_url}/get-orders",
                json={
                    "privateKey": private_key,
                    "safeAddress": safe_address
                },
                timeout=10
            )
            response.raise_for_status()

            result = response.json()

            if result.get('success'):
                logger.info(f"[BUILDER] Retrieved {result.get('count', 0)} orders")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"[BUILDER] Get orders request failed: {e}")
            return {
                "success": False,
                "error": "Failed to get orders",
                "details": str(e),
                "orders": [],
                "count": 0
            }


# Example usage in your existing code
if __name__ == "__main__":
    # Initialize builder client
    builder = PolymarketBuilder()

    # Check health
    health = builder.health_check()
    print(f"Service status: {health.get('status')}")

    # Example: Deploy Safe wallet
    # result = builder.deploy_safe(
    #     private_key="0x...",
    #     owner_address="0x..."
    # )
    # print(f"Safe address: {result['safeAddress']}")

    # Example: Create order
    # order = builder.create_order(
    #     private_key="0x...",
    #     safe_address="0x...",
    #     token_id="...",
    #     side="BUY",
    #     price=0.75,
    #     size=10
    # )
    # print(f"Order ID: {order['orderID']}")
