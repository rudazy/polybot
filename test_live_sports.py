"""
Test what sports markets are available and why they might not show as "live"
"""

from polymarket_api import PolymarketAPI
from datetime import datetime, timedelta

api = PolymarketAPI()

print("\n=== CHECKING SPORTS MARKETS ===\n")

# Get all sports markets
print("1. Fetching ALL sports markets...")
response = api.client.get(api.gamma_markets_endpoint, params={
    "limit": 100,
    "active": "true",
    "closed": "false",
    "archived": "false"
})

if response.status_code != 200:
    print(f"ERROR: Failed to fetch markets: {response.status_code}")
    exit(1)

all_markets = response.json()
print(f"   Total active markets: {len(all_markets)}")

# Filter for sports-related
sports_keywords = ['vs', 'vs.', '@', 'game', 'match', 'nfl', 'nba', 'nhl', 'mlb', 'soccer', 'football', 'basketball']
sports_markets = []

now = datetime.utcnow()
print(f"   Current time (UTC): {now}")

for market in all_markets:
    question = market.get('question', '').lower()

    # Check if it looks like a sports market
    is_sports = any(keyword in question for keyword in sports_keywords)

    if is_sports:
        end_date = market.get('end_date_iso') or market.get('endDate')

        # Parse end date
        hours_until_end = None
        if end_date:
            try:
                # Handle different date formats
                end_str = end_date.replace('Z', '+00:00') if 'Z' in end_date else end_date
                end_dt = datetime.fromisoformat(end_str.split('.')[0])
                hours_until_end = (end_dt - now).total_seconds() / 3600
            except Exception as e:
                print(f"   Date parse error for: {question[:50]}")
                print(f"   End date: {end_date}")
                print(f"   Error: {e}")

        sports_markets.append({
            'question': question,
            'end_date': end_date,
            'hours_until_end': hours_until_end,
            'volume24hr': market.get('volume24hr', 0),
            'liquidity': market.get('liquidity', 0)
        })

print(f"\n2. Found {len(sports_markets)} sports markets\n")

# Show first 10 sports markets with details
print("Sample sports markets:")
for i, market in enumerate(sports_markets[:10], 1):
    hours = market['hours_until_end']
    hours_str = f"{hours:.1f}h" if hours is not None else "unknown"

    is_live = hours is not None and 0 < hours < 24
    status = "LIVE" if is_live else "not live"

    print(f"\n{i}. {market['question'][:70]}...")
    print(f"   Ends in: {hours_str}")
    print(f"   Status: {status}")
    print(f"   Volume 24h: ${market['volume24hr']:,.2f}")

# Count truly live games
live_count = sum(1 for m in sports_markets if m['hours_until_end'] is not None and 0 < m['hours_until_end'] < 24)
print(f"\n3. Markets ending within 24 hours: {live_count}")

# Show which ones would be filtered as "live"
print("\n4. Markets that should show as LIVE:")
for market in sports_markets:
    hours = market['hours_until_end']
    if hours is not None and 0 < hours < 24:
        print(f"   - {market['question'][:70]}...")
        print(f"     Ends in: {hours:.1f} hours")
