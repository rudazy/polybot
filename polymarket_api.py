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
    
    def get_markets(self, limit: int = 20, active: bool = True, closed: bool = False) -> List[Dict]:
        """Fetch markets from Polymarket Gamma API"""
        try:
            params = {
                "limit": limit,
                "active": str(active).lower(),
                "closed": str(closed).lower()
            }

            response = self.client.get(self.gamma_markets_endpoint, params=params)
            response.raise_for_status()

            markets = response.json()
            return markets if isinstance(markets, list) else []

        except Exception as e:
            print(f"Error fetching markets: {e}")
            return []

    def search_markets(self, query: str, limit: int = 50) -> List[Dict]:
        """Search markets by keyword - fetches multiple pages for comprehensive results"""
        try:
            all_markets = []

            # Fetch multiple pages to get comprehensive results
            # Polymarket has thousands of markets, so we need to fetch in batches
            for offset in [0, 100, 200, 300, 400]:
                try:
                    batch_params = {
                        "limit": 100,
                        "offset": offset,
                        "active": "true",
                        "closed": "false"
                    }

                    response = self.client.get(self.gamma_markets_endpoint, params=batch_params)

                    if response.status_code == 200:
                        batch = response.json()
                        if isinstance(batch, list) and batch:
                            all_markets.extend(batch)
                        else:
                            # No more results, stop fetching
                            break
                    else:
                        # If one batch fails, continue with what we have
                        break

                except Exception as e:
                    print(f"Error fetching batch at offset {offset}: {e}")
                    # Continue with what we have
                    break

            # If we got no markets from batching, fall back to single request
            if not all_markets:
                all_markets = self.get_markets(limit=200, active=True, closed=False)

            # Filter by query in question (case-insensitive)
            query_lower = query.lower()
            filtered = [
                m for m in all_markets
                if query_lower in m.get('question', '').lower()
            ]

            # Return up to the limit
            return filtered[:limit]

        except Exception as e:
            print(f"Error searching markets: {e}")
            return []
    
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