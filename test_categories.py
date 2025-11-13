"""
Check what categories/tags markets have
"""

from polymarket_api import PolymarketAPI

api = PolymarketAPI()

print("\n=== CHECKING MARKET CATEGORIES ===\n")

# Get markets
response = api.client.get(api.gamma_markets_endpoint, params={
    "limit": 100,
    "active": "true",
    "closed": "false"
})

markets = response.json()
print(f"Total markets: {len(markets)}")

# Check what fields contain category info
print("\n1. Checking available category fields:")
if markets:
    sample = markets[0]
    category_fields = ['tag', 'tags', 'category', 'categories', 'groupItemTitle', 'events']

    for field in category_fields:
        if field in sample:
            print(f"   {field}: {sample.get(field)}")

# Check events field more carefully
print("\n2. Checking 'events' field structure:")
if markets and 'events' in markets[0]:
    event = markets[0]['events'][0] if markets[0]['events'] else None
    if event:
        print(f"   Event keys: {event.keys()}")
        print(f"   Event title: {event.get('title')}")
        print(f"   Event ticker: {event.get('ticker')}")

# Try to find sports markets by searching for specific queries
print("\n3. Trying to search for sports markets:")
sports_queries = ['NBA', 'NFL', 'NBA game', 'football', 'basketball']

for query in sports_queries:
    response = api.client.get(api.gamma_markets_endpoint, params={
        "limit": 10,
        "active": "true",
        "closed": "false"
    })

    if response.status_code == 200:
        results = response.json()
        matching = [m for m in results if query.lower() in m.get('question', '').lower()]
        if matching:
            print(f"\n   Query '{query}': Found {len(matching)} markets")
            for m in matching[:2]:
                print(f"      - {m.get('question')[:80]}")
        else:
            print(f"   Query '{query}': No matches")
