"""
Polymarket API Wrapper - FIXED VERSION
"""

import requests
import json
from typing import List, Dict, Optional
from datetime import datetime


class PolymarketAPI:
    
    def __init__(self):
        self.base_url = "https://clob.polymarket.com"
        self.gamma_url = "https://gamma-api.polymarket.com"
        self.headers = {"Content-Type": "application/json"}
    
    def get_markets(self, limit: int = 20, active: bool = True) -> List[Dict]:
        """Fetch active markets from Polymarket"""
        try:
            endpoint = f"{self.gamma_url}/markets"
            params = {"limit": limit, "active": active, "closed": False}
            
            response = requests.get(endpoint, params=params, headers=self.headers)
            response.raise_for_status()
            
            markets = response.json()
            return markets if isinstance(markets, list) else []
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching markets: {e}")
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