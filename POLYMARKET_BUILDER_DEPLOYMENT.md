# Polymarket Builder Program - Complete Deployment Guide

## 🎉 What's New

You now have **gasless trading** via Polymarket Builder Program!

**Benefits:**
- ✅ **FREE GAS** - Users don't pay any gas fees
- ✅ **Builder Attribution** - All trades show "via Polybot.finance"
- ✅ **Leaderboard Tracking** - Volume tracked on Builder leaderboard
- ✅ **Grant Eligibility** - Compete for Polymarket grants (💰)
- ✅ **Better UX** - No POL needed, instant trades

---

## 📦 Architecture

```
┌─────────────────────────┐
│   Python Backend        │  Port 8000
│   (FastAPI)             │
│   - Auth, DB, Markets   │
│   - Wallet management   │
│   - User accounts       │
└───────────┬─────────────┘
            │
            │ HTTP requests
            ↓
┌─────────────────────────┐
│   Node.js Microservice  │  Port 3001
│   (Express)             │
│   - Safe wallet deploy  │
│   - Gasless orders      │
│   - Builder attribution │
└───────────┬─────────────┘
            │
            │ Polymarket CLOB API
            ↓
┌─────────────────────────┐
│   Polymarket Exchange   │
│   - FREE GAS via relay  │
│   - Order matching      │
│   - Builder tracking    │
└─────────────────────────┘
```

---

## 🚀 Quick Start (Local Development)

### Step 1: Install Node.js Dependencies

```bash
cd polymarket-service
npm install
```

**Dependencies installed:**
- `express` - Web server
- `@polymarket/clob-client` - Polymarket API client
- `ethers@5.7.2` - Ethereum library
- `cors` - Cross-origin requests
- `dotenv` - Environment variables

### Step 2: Configure Environment

The `.env` file already contains your Builder API credentials:

```bash
# Check it's there (don't commit this file!)
cat polymarket-service/.env
```

Should show:
```
POLYMARKET_API_KEY=019a4ee9-6c77-7b72-b7e4-0b89429655d5
POLYMARKET_SECRET=f9QFi8t6VrHg9cJC5SnQ1BOqLiz9wQeZAAsBhiw4uak=
POLYMARKET_PASSPHRASE=37baf5ab2bffc4fe8ea3f51dbfb1a4fbb15bb3838d91361628496a996cd80e67
PORT=3001
RPC_URL=https://polygon-rpc.com
```

### Step 3: Start Node.js Microservice

**Terminal 1 (Node.js service):**
```bash
cd polymarket-service
npm start
```

You should see:
```
🚀 Polymarket Builder Service running on port 3001
✅ Health: http://localhost:3001/health
📚 Builder Program enabled
⛽ FREE GAS via Polymarket relayer!
```

### Step 4: Start Python Backend

**Terminal 2 (Python backend):**
```bash
cd /home/user/polybot
python api_server.py
```

### Step 5: Test the Integration

**Terminal 3 (testing):**
```bash
# Test Node.js health
curl http://localhost:3001/health

# Should return:
# {
#   "status": "ok",
#   "service": "Polymarket Service",
#   "version": "1.0.0",
#   "polymarket_host": "https://clob.polymarket.com",
#   "chain_id": 137
# }
```

---

## 🧪 Testing Guide

### Test 1: Health Check ✅

```bash
curl http://localhost:3001/health
```

**Expected:** `{"status": "ok"}`

---

### Test 2: Deploy Safe Wallet (FREE GAS!)

```bash
curl -X POST http://localhost:3001/deploy-safe \
  -H "Content-Type: application/json" \
  -d '{
    "privateKey": "0x1234567890abcdef...",
    "ownerAddress": "0xYourWalletAddress..."
  }'
```

**Expected response:**
```json
{
  "success": true,
  "safeAddress": "0x...",
  "owner": "0x...",
  "message": "Safe wallet deployed with FREE gas via Polymarket relayer!",
  "gasless": true
}
```

**What this does:**
- Creates a Safe wallet for the user
- Uses Polymarket relayer (FREE GAS - no POL needed!)
- One-time operation per user
- Safe address used for all future trades

---

### Test 3: Get Safe Address (Without Deploying)

```bash
curl -X POST http://localhost:3001/get-safe-address \
  -H "Content-Type: application/json" \
  -d '{
    "privateKey": "0x1234567890abcdef..."
  }'
```

**Expected response:**
```json
{
  "success": true,
  "safeAddress": "0x...",
  "deployed": true
}
```

---

### Test 4: Create Gasless Order (NO GAS FEES!)

```bash
curl -X POST http://localhost:3001/create-order \
  -H "Content-Type: application/json" \
  -d '{
    "privateKey": "0x1234567890abcdef...",
    "safeAddress": "0x...",
    "tokenID": "21742633143463906290569050155826241533067272736897614950488156847949938836455",
    "side": "BUY",
    "price": "0.75",
    "size": "10"
  }'
```

**Expected response:**
```json
{
  "success": true,
  "orderID": "0x...",
  "order": {...},
  "message": "Order placed with FREE gas via Polymarket relayer!",
  "gasless": true,
  "builderAttribution": true
}
```

**What this does:**
- Creates a BUY order for $10 at 75% probability
- Uses Polymarket relayer (FREE GAS!)
- Order attributed to "Polybot.finance"
- No POL needed!
- Instant execution

---

### Test 5: List Orders

```bash
curl -X POST http://localhost:3001/get-orders \
  -H "Content-Type: application/json" \
  -d '{
    "privateKey": "0x1234567890abcdef...",
    "safeAddress": "0x..."
  }'
```

**Expected response:**
```json
{
  "success": true,
  "orders": [
    {
      "id": "0x...",
      "side": "BUY",
      "price": "0.75",
      "size": "10",
      "status": "open"
    }
  ],
  "count": 1
}
```

---

### Test 6: Cancel Order (Gasless)

```bash
curl -X POST http://localhost:3001/cancel-order \
  -H "Content-Type: application/json" \
  -d '{
    "privateKey": "0x1234567890abcdef...",
    "safeAddress": "0x...",
    "orderID": "0x..."
  }'
```

**Expected response:**
```json
{
  "success": true,
  "message": "Order canceled with FREE gas!",
  "gasless": true
}
```

---

## 🐍 Python Integration

### Use the Python Wrapper

```python
from polymarket_builder import PolymarketBuilder

# Initialize
builder = PolymarketBuilder()

# Check service is running
health = builder.health_check()
print(f"Status: {health['status']}")

# Deploy Safe wallet
result = builder.deploy_safe(
    private_key=user_private_key,
    owner_address=user_wallet_address
)

safe_address = result['safeAddress']
print(f"✅ Safe deployed: {safe_address}")

# Create gasless order
order = builder.create_order(
    private_key=user_private_key,
    safe_address=safe_address,
    token_id=market_token_id,
    side="BUY",
    price=0.75,
    size=10
)

print(f"✅ Order placed: {order['orderID']}")
print(f"⛽ Gas cost: FREE! (via Polymarket relayer)")
print(f"🏷️ Attribution: Polybot.finance")
```

### Add to API Endpoints

```python
# api_server.py

from polymarket_builder import PolymarketBuilder

# Initialize builder
builder = PolymarketBuilder()

@app.post("/wallet/deploy-safe/{user_id}")
def deploy_safe_wallet(user_id: str):
    """Deploy Safe wallet for gasless trading"""
    user_data = db.get_user(user_id=user_id)
    private_key = wallet_manager.export_private_key(user_id)
    wallet_address = user_data['wallet_address']

    result = builder.deploy_safe(
        private_key=private_key,
        owner_address=wallet_address
    )

    if result['success']:
        # Save Safe address to user's database record
        db.update_user(user_id, {
            'safe_address': result['safeAddress']
        })

    return result


@app.post("/trades/execute-gasless/{user_id}")
def execute_gasless_trade(user_id: str, trade_data: TradeCreate):
    """Execute trade with FREE gas via Builder Program"""
    user_data = db.get_user(user_id=user_id)
    private_key = wallet_manager.export_private_key(user_id)

    # Get or create Safe address
    safe_address = user_data.get('safe_address')
    if not safe_address:
        # Deploy Safe wallet first
        deploy_result = builder.deploy_safe(
            private_key=private_key,
            owner_address=user_data['wallet_address']
        )
        safe_address = deploy_result['safeAddress']
        db.update_user(user_id, {'safe_address': safe_address})

    # Create gasless order
    order = builder.create_order(
        private_key=private_key,
        safe_address=safe_address,
        token_id=trade_data.market_id,
        side='BUY' if trade_data.position == 'YES' else 'SELL',
        price=trade_data.price,
        size=trade_data.amount
    )

    return {
        "success": order['success'],
        "order_id": order.get('orderID'),
        "message": "✅ Trade executed with FREE gas via Polybot.finance!",
        "gasless": True,
        "builder_attribution": True
    }
```

---

## 🚀 Production Deployment

### Option 1: Railway (Recommended)

**Deploy Node.js Microservice:**

1. **Create new Railway service:**
   - Go to Railway dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repo
   - Set root directory: `polymarket-service`

2. **Set environment variables:**
   ```
   POLYMARKET_API_KEY=019a4ee9-6c77-7b72-b7e4-0b89429655d5
   POLYMARKET_SECRET=f9QFi8t6VrHg9cJC5SnQ1BOqLiz9wQeZAAsBhiw4uak=
   POLYMARKET_PASSPHRASE=37baf5ab2bffc4fe8ea3f51dbfb1a4fbb15bb3838d91361628496a996cd80e67
   PORT=3001
   RPC_URL=https://polygon-rpc.com
   ```

3. **Railway will auto-detect:**
   - `package.json` present
   - Run `npm install`
   - Run `npm start`
   - Deploy! ✅

4. **Get the service URL:**
   ```
   Example: https://polymarket-service-production.up.railway.app
   ```

5. **Update Python backend environment:**
   ```bash
   # In Railway Python service settings, add:
   POLYMARKET_NODE_SERVICE_URL=https://polymarket-service-production.up.railway.app
   ```

6. **Test production deployment:**
   ```bash
   curl https://polymarket-service-production.up.railway.app/health
   ```

---

### Option 2: Docker Compose (Both Services Together)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  python-backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - POLYMARKET_NODE_SERVICE_URL=http://node-service:3001
    depends_on:
      - node-service

  node-service:
    build: ./polymarket-service
    ports:
      - "3001:3001"
    environment:
      - POLYMARKET_API_KEY=${POLYMARKET_API_KEY}
      - POLYMARKET_SECRET=${POLYMARKET_SECRET}
      - POLYMARKET_PASSPHRASE=${POLYMARKET_PASSPHRASE}
```

Run both services:
```bash
docker-compose up -d
```

---

## 📊 Comparison: Before vs After

| Feature | Before (Direct USDC) | After (Builder Program) |
|---------|---------------------|------------------------|
| **Gas Fees** | $0.01-0.05 per trade | **FREE!** ✅ |
| **POL Needed** | Yes (~0.05 POL) | **NO** ✅ |
| **USDC Approval** | Required (one-time) | **Not needed** ✅ |
| **Speed** | 5-30 seconds | **Instant** ✅ |
| **Attribution** | None | **"via Polybot.finance"** ✅ |
| **Leaderboard** | Not tracked | **Tracked** ✅ |
| **Grants** | Not eligible | **Eligible** ✅ |
| **User Experience** | Medium | **Excellent** ✅ |

---

## 🔥 Common Issues & Solutions

### Issue 1: "ECONNREFUSED" when calling Node service

**Cause:** Node.js service not running

**Solution:**
```bash
# Terminal 1: Start Node.js service
cd polymarket-service
npm start

# Terminal 2: Test
curl http://localhost:3001/health
```

---

### Issue 2: "Invalid API credentials"

**Cause:** Missing or incorrect Builder API credentials in `.env`

**Solution:**
```bash
# Check .env file exists
cat polymarket-service/.env

# Should contain:
# POLYMARKET_API_KEY=...
# POLYMARKET_SECRET=...
# POLYMARKET_PASSPHRASE=...

# If missing, copy from .env.example and add your credentials
cp polymarket-service/.env.example polymarket-service/.env
nano polymarket-service/.env
```

---

### Issue 3: "Module not found" errors

**Cause:** Dependencies not installed

**Solution:**
```bash
cd polymarket-service
npm install
```

---

### Issue 4: "Safe deployment failed"

**Cause:** Invalid private key or network issue

**Solution:**
- Check private key format (must start with 0x)
- Check RPC_URL is working
- Try again (network might be slow)

---

### Issue 5: "Order creation failed"

**Cause:** Safe not deployed yet

**Solution:**
```bash
# Deploy Safe first
curl -X POST http://localhost:3001/deploy-safe -H "Content-Type: application/json" -d '{"privateKey": "0x...", "ownerAddress": "0x..."}'

# Then create order
curl -X POST http://localhost:3001/create-order -H "Content-Type: application/json" -d '{...}'
```

---

## 📈 Monitoring

### Check Builder Program Stats

1. **Go to Polymarket Builder Dashboard:**
   - https://builders.polymarket.com/dashboard
   - Login with your Builder account

2. **Check metrics:**
   - Total volume attributed to Polybot.finance
   - Number of trades
   - Leaderboard rank
   - Grant eligibility

### Check Service Logs

**Node.js service:**
```bash
cd polymarket-service
npm start

# Logs show:
# [DEPLOY] Deploying Safe wallet...
# [ORDER] Creating BUY order: 10 @ 0.75
# [SUCCESS] Order placed: 0x...
```

**Python backend:**
```python
# In your code:
logger.info(f"[BUILDER] Creating gasless order...")
```

---

## ✅ Testing Checklist

Before going live, test:

- [ ] Node.js service starts without errors
- [ ] Health check returns `{"status": "ok"}`
- [ ] Safe wallet deployment works
- [ ] Get Safe address works
- [ ] Order creation works (gasless!)
- [ ] Order listing works
- [ ] Order cancellation works
- [ ] Python integration works
- [ ] Production deployment works
- [ ] Railway environment variables set
- [ ] Both services communicate

---

## 🎯 Success Criteria

Your Builder Program integration is successful when:

- ✅ Node.js service running on port 3001
- ✅ Python backend running on port 8000
- ✅ Users can deploy Safe wallets (gasless)
- ✅ Users can create orders (gasless)
- ✅ No gas fees charged to users
- ✅ Orders show "via Polybot.finance" attribution
- ✅ Volume tracked on Builder leaderboard
- ✅ Everything works in production (Railway)

---

## 📞 Support

**Polymarket Builder Program:**
- Dashboard: https://builders.polymarket.com/dashboard
- Docs: https://docs.polymarket.com/
- Discord: https://discord.gg/polymarket
- Email: builders@polymarket.com

**Technical Issues:**
- Check logs first
- Test health endpoint
- Verify environment variables
- Try with smaller amounts first

---

## 🎊 You're Ready!

**Next steps:**
1. Test locally (both services)
2. Deploy Node.js to Railway
3. Update Python backend with service URL
4. Test in production
5. Monitor Builder dashboard
6. Track volume and compete for grants!

**Congratulations!** You now have gasless trading with builder attribution! 🚀

All your users' trades will be:
- ⛽ **FREE GAS** (no POL needed)
- 🏷️ **Attributed to Polybot.finance**
- 📊 **Tracked on leaderboard**
- 💰 **Eligible for grants**

**LET'S GO!** 🎉
