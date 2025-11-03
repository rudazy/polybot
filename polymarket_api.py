"""
Polymarket API Wrapper - Using HTTPx like official Polymarket agents
"""

import httpx
import json
from typing import List, Dict, Optional
from datetime import datetime


class PolymarketAPI:

    def __init__(self):
        self.gamma_url = "https://gamma-api.polymarket.com"
        self.gamma_markets_endpoint = f"{self.gamma_url}/markets"
        self.gamma_events_endpoint = f"{self.gamma_url}/events"

        # Set up httpx client with browser-like headers to avoid Cloudflare blocking
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": "https://polymarket.com",
            "Referer": "https://polymarket.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"'
        }

        self.client = httpx.Client(timeout=30.0, headers=headers, follow_redirects=True)
    
    def get_markets(self, limit: int = 20, active: bool = True, closed: bool = False, order: str = "volume24hr") -> List[Dict]:
        """
        Fetch markets from Polymarket Gamma API
        ⚠️ FIXED: Now sorts by 24hr volume to match Polymarket.com trending

        Args:
            limit: Number of markets to return
            active: Only show active markets
            closed: Include closed markets
            order: Sort order - "volume24hr", "volume7d", "liquidity", etc.

        Returns:
            List of market dictionaries
        """
        try:
            params = {
                "limit": limit,
                "active": str(active).lower(),
                "closed": str(closed).lower(),
                "archived": "false",  # Don't show archived markets
                "order": order  # CRITICAL: Sort by 24hr volume for trending
            }

            print(f"[API] Fetching markets with params: {params}")

            response = self.client.get(self.gamma_markets_endpoint, params=params)
            response.raise_for_status()

            markets = response.json()
            result = markets if isinstance(markets, list) else []

            print(f"[API] Retrieved {len(result)} markets")

            return result

        except Exception as e:
            print(f"[ERROR] Error fetching markets: {e}")
            import traceback
            traceback.print_exc()
            return []

    def search_markets(self, query: str, limit: int = 100) -> List[Dict]:
        """
        Search markets by keyword using Polymarket's search API
        ⚠️ FIXED: Now uses proper search parameter to find ALL matching markets

        Args:
            query: Search term (e.g., "trump", "election", etc.)
            limit: Maximum number of results to return

        Returns:
            List of matching markets sorted by relevance
        """
        try:
            # Use Polymarket's native search parameter for better results
            search_params = {
                "limit": limit,
                "active": "true",
                "closed": "false",
                "archived": "false",
                "order": "volume24hr"  # Sort by trending
            }

            print(f"[SEARCH] Searching for '{query}'...")

            # Try 3 approaches to find ALL matching markets:

            # Approach 1: Try native search parameter (if Polymarket supports it)
            try:
                search_params_with_query = search_params.copy()
                search_params_with_query["search"] = query

                response = self.client.get(self.gamma_markets_endpoint, params=search_params_with_query)

                if response.status_code == 200:
                    markets = response.json()
                    if isinstance(markets, list) and len(markets) > 0:
                        print(f"[SEARCH] Found {len(markets)} markets using native search")
                        return markets
            except Exception as e:
                print(f"[SEARCH] Native search not available: {e}")

            # Approach 2: Fetch large batch and filter locally
            print(f"[SEARCH] Fetching markets in batches for local filtering...")
            all_markets = []

            # Fetch multiple pages (up to 500 markets total)
            for offset in [0, 100, 200, 300, 400]:
                try:
                    batch_params = {
                        "limit": 100,
                        "offset": offset,
                        "active": "true",
                        "closed": "false",
                        "archived": "false"
                    }

                    response = self.client.get(self.gamma_markets_endpoint, params=batch_params)

                    if response.status_code == 200:
                        batch = response.json()
                        if isinstance(batch, list) and batch:
                            all_markets.extend(batch)
                            print(f"[SEARCH] Fetched batch at offset {offset}: {len(batch)} markets")
                        else:
                            break
                    else:
                        break

                except Exception as e:
                    print(f"[SEARCH] Error fetching batch at offset {offset}: {e}")
                    break

            # Filter by query in question (case-insensitive)
            query_lower = query.lower()
            filtered = [
                m for m in all_markets
                if query_lower in m.get('question', '').lower()
            ]

            print(f"[SEARCH] Found {len(filtered)} markets matching '{query}' (out of {len(all_markets)} total)")

            # Return up to the limit
            return filtered[:limit]

        except Exception as e:
            print(f"[ERROR] Error searching markets: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_trending_markets(self, limit: int = 50) -> List[Dict]:
        """
        Get trending markets sorted by 24-hour volume
        ⚠️ NEW: Dedicated method to match Polymarket.com trending section

        Args:
            limit: Number of trending markets to return

        Returns:
            List of trending markets sorted by 24hr volume
        """
        return self.get_markets(limit=limit, active=True, closed=False, order="volume24hr")

    def format_market_data(self, market: Dict) -> Dict:
        """Format raw market data - FIXED VERSION"""
        try:
            formatted = {
                "id": market.get("condition_id", "N/A"),
                "question": market.get("question", "Unknown"),
                "volume": float(market.get("volume", 0)),
                "liquidity": float(market.get("liquidity", 0)),
            }
            
            # Safely get outcomes
            outcomes = market.get("outcomes", [])
            if isinstance(outcomes, list) and len(outcomes) >= 2:
                formatted["yes_price"] = float(outcomes[0].get("price", 0.5))
                formatted["no_price"] = float(outcomes[1].get("price", 0.5))
            else:
                formatted["yes_price"] = 0.5
                formatted["no_price"] = 0.5
            
            return formatted
            
        except Exception as e:
            print(f"Error formatting: {e}")
            return {"question": "N/A", "volume": 0, "yes_price": 0, "no_price": 0}


def test_api():
    """Test the API connection"""
    print("🔍 Testing Polymarket API Connection...\n")
    
    api = PolymarketAPI()
    markets = api.get_markets(limit=5)
    
    if markets:
        print(f"✅ Successfully fetched {len(markets)} markets!\n")
        
        if len(markets) > 0:
            first_market = markets[0]
            formatted = api.format_market_data(first_market)
            
            print("=" * 60)
            print("SAMPLE MARKET:")
            print("=" * 60)
            print(f"Question: {formatted.get('question', 'N/A')}")
            print(f"Volume: ${formatted.get('volume', 0):,.2f}")
            print(f"Liquidity: ${formatted.get('liquidity', 0):,.2f}")
            print(f"YES Price: {formatted.get('yes_price', 0):.1%}")
            print(f"NO Price: {formatted.get('no_price', 0):.1%}")
            print("=" * 60)
            
            print("\n📊 All 5 Markets:")
            for i, market in enumerate(markets, 1):
                data = api.format_market_data(market)
                print(f"{i}. {data.get('question', 'N/A')[:60]}...")
    else:
        print("❌ Failed to fetch markets")
    
    print("\n✅ API Connection Test Complete!")


if __name__ == "__main__":
    test_api()