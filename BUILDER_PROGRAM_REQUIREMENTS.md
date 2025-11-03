# Polymarket Builder Program Integration Requirements

## ⚠️ IMPORTANT NOTE

**The current Polybot.finance codebase is written in Python (FastAPI backend).**

**The Polymarket Builder Program requires Node.js/TypeScript** and uses the following packages:
- `@polymarket/clob-client` (Node.js only)
- `@polymarket/builder-signing-sdk` (Node.js only)
- `@polymarket/relayer-client` (Node.js only)

These packages are **NOT available for Python** and would require a complete rewrite of the trading/order execution portion of the application.

---

## Option 1: Rewrite Trading Module in Node.js/TypeScript

To integrate with the Polymarket Builder Program, you would need to:

### 1. Create a Node.js Microservice

Create a separate Node.js service that handles:
- Order creation and execution
- Builder attribution
- Safe wallet deployment
- Gasless transactions

### 2. Required NPM Packages

```bash
npm install @polymarket/clob-client
npm install @polymarket/builder-signing-sdk
npm install @polymarket/relayer-client
npm install ethers@5.7.2
```

### 3. Architecture Changes

```
┌─────────────────────────────────────────────────────────┐
│                   CURRENT ARCHITECTURE                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Python FastAPI Backend (api_server.py)                 │
│    ↓                                                      │
│  Python Polymarket API (polymarket_api.py)              │
│    ↓                                                      │
│  Python Wallet Manager (wallet_manager.py)              │
│    ↓                                                      │
│  Python Blockchain Manager (blockchain_manager.py)      │
│                                                           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              PROPOSED HYBRID ARCHITECTURE                │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Python FastAPI Backend (api_server.py)                 │
│    ↓                                                      │
│  Python Polymarket API (polymarket_api.py) [Markets]    │
│    ↓                                                      │
│  HTTP Request → Node.js Trading Service                 │
│    ↓                                                      │
│  @polymarket/clob-client [Builder Attribution]          │
│    ↓                                                      │
│  Polymarket CLOB API [Orders with Builder Headers]      │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### 4. Node.js Trading Service Example

```javascript
// trading-service/index.js
const express = require('express');
const { ClobClient } = require("@polymarket/clob-client");
const { BuilderConfig } = require("@polymarket/builder-signing-sdk");
const { ethers } = require("ethers");

const app = express();
app.use(express.json());

// Builder configuration with signing server
const builderConfig = new BuilderConfig({
  remoteBuilderConfig: {
    url: process.env.BUILDER_SIGNING_SERVER_URL
  }
});

// Execute trade with Builder attribution
app.post('/api/trade', async (req, res) => {
  try {
    const { privateKey, marketId, side, price, size, proxyAddress } = req.body;

    const wallet = new ethers.Wallet(privateKey);

    const client = new ClobClient(
      "https://clob.polymarket.com",
      137, // Polygon chain ID
      wallet,
      undefined,
      proxyAddress ? 1 : 0, // SignatureType
      proxyAddress,
      undefined,
      false,
      builderConfig // BUILDER ATTRIBUTION!
    );

    await client.setCreds(client.createOrDeriveAPIKey());

    const order = await client.createOrder({
      tokenID: marketId,
      price: price.toString(),
      size: size.toString(),
      side: side,
      feeRateBps: "0" // No fees for builder orders
    });

    const response = await client.postOrder(order);

    res.json({
      success: true,
      orderID: response.orderID,
      message: "Order placed with Polybot.finance attribution!"
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`Trading service running on port ${PORT}`);
});
```

### 5. Update Python Backend to Call Node.js Service

```python
# api_server.py
import requests

@app.post("/trades/manual")
def create_manual_trade(user_id: str, trade: TradeCreate):
    """Execute a manual trade via Node.js trading service"""

    # Get user's wallet
    wallet_data = db.get_wallet(user_id)
    private_key = wallet_manager.export_private_key(user_id)

    # Call Node.js trading service
    trading_service_url = os.environ.get('TRADING_SERVICE_URL', 'http://localhost:3001')

    response = requests.post(f"{trading_service_url}/api/trade", json={
        "privateKey": private_key,
        "marketId": trade.market_id,
        "side": "BUY" if trade.position == "YES" else "SELL",
        "price": 0.75,
        "size": trade.amount,
        "proxyAddress": wallet_data.get('proxy_wallet_address')
    })

    return response.json()
```

---

## Option 2: Use Polymarket HTTP API (Current Approach)

**Limitation:** Without the Builder Program SDK, you:
- ❌ Don't get builder attribution
- ❌ Can't access gasless transactions
- ❌ Won't appear on Builder Leaderboard
- ❌ Not eligible for builder grants

**Benefit:**
- ✅ Stay in Python ecosystem
- ✅ Simpler architecture
- ✅ No microservices needed

---

## Recommended Path Forward

### Short Term (Stay in Python)
1. ✅ Continue using current Python implementation
2. ✅ Use Polymarket Gamma API for markets/data
3. ✅ Use Web3.py for blockchain interactions
4. Focus on building user base and features

### Long Term (Builder Program)
When ready to scale and get builder benefits:

1. **Apply for Builder Program**
   - Visit: https://builders.polymarket.com/
   - Get API credentials

2. **Deploy Node.js Trading Service**
   - Create separate microservice
   - Deploy on Railway/Render alongside Python backend

3. **Deploy Builder Signing Server**
   - Secure service to sign builder headers
   - Store credentials safely

4. **Integrate Services**
   - Python handles: Auth, DB, Markets, UI
   - Node.js handles: Order execution with builder attribution

---

## Estimated Development Time

| Task | Time Estimate |
|------|---------------|
| Node.js trading service | 2-3 days |
| Builder signing server | 1 day |
| Python integration | 1 day |
| Testing & deployment | 1-2 days |
| Safe wallet deployment | 2-3 days |
| **Total** | **7-12 days** |

---

## Benefits After Integration

1. **Free Gas Fees** - Users don't pay Polygon gas
2. **Leaderboard Presence** - Visibility on Polymarket
3. **Grant Eligibility** - Compete for Polymarket grants ($)
4. **Better UX** - Faster, cheaper trades
5. **Volume Attribution** - All trades credited to Polybot.finance

---

## Questions?

Contact Polymarket Builder Support:
- Docs: https://docs.polymarket.com/
- Discord: https://discord.gg/polymarket
- Email: builders@polymarket.com
