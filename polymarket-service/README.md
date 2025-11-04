# Polymarket Microservice

Node.js microservice for Polymarket Builder Program integration.

## 🚀 Features

- ✅ **FREE GAS** via Polymarket relayer
- ✅ **Safe Wallet deployment** (gasless)
- ✅ **Gasless trading** (no POL needed!)
- ✅ **Builder Program integration**
- ✅ **Order management** (create, cancel, list)

---

## 📦 Installation

```bash
cd polymarket-service
npm install
```

---

## ⚙️ Configuration

1. **Copy environment file:**
```bash
cp .env.example .env
```

2. **Add your Builder API credentials to `.env`:**
```env
POLYMARKET_API_KEY=your-api-key-here
POLYMARKET_SECRET=your-secret-here
POLYMARKET_PASSPHRASE=your-passphrase-here
```

⚠️ **NEVER commit `.env` to git!**

---

## 🏃 Running

### Development Mode (with auto-reload)
```bash
npm run dev
```

### Production Mode
```bash
npm start
```

Server runs on: `http://localhost:3001`

---

## 📡 API Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "Polymarket Service",
  "version": "1.0.0",
  "timestamp": "2024-11-04T...",
  "polymarket_host": "https://clob.polymarket.com",
  "chain_id": 137
}
```

---

### Deploy Safe Wallet (FREE GAS!)
```http
POST /deploy-safe
Content-Type: application/json

{
  "privateKey": "0x...",
  "ownerAddress": "0x..."
}
```

**Response:**
```json
{
  "success": true,
  "safeAddress": "0x...",
  "owner": "0x...",
  "message": "Safe wallet deployed with FREE gas via Polymarket relayer!",
  "gasless": true
}
```

---

### Get Safe Address
```http
POST /get-safe-address
Content-Type: application/json

{
  "privateKey": "0x..."
}
```

**Response:**
```json
{
  "success": true,
  "safeAddress": "0x...",
  "deployed": true
}
```

---

### Create Order (GASLESS!)
```http
POST /create-order
Content-Type: application/json

{
  "privateKey": "0x...",
  "safeAddress": "0x...",
  "tokenID": "21742633143463906290569050155826241533067272736897614950488156847949938836455",
  "side": "BUY",
  "price": "0.75",
  "size": "10"
}
```

**Response:**
```json
{
  "success": true,
  "orderID": "0x...",
  "order": { ... },
  "message": "Order placed with FREE gas via Polymarket relayer!",
  "gasless": true,
  "builderAttribution": true
}
```

---

### Cancel Order
```http
POST /cancel-order
Content-Type: application/json

{
  "privateKey": "0x...",
  "safeAddress": "0x...",
  "orderID": "0x..."
}
```

---

### Get Orders
```http
POST /get-orders
Content-Type: application/json

{
  "privateKey": "0x...",
  "safeAddress": "0x..."
}
```

**Response:**
```json
{
  "success": true,
  "orders": [...],
  "count": 5
}
```

---

## 🔗 Integration with Python Backend

### Example: Call from Python

```python
import requests

# Deploy Safe wallet (FREE GAS)
response = requests.post('http://localhost:3001/deploy-safe', json={
    'privateKey': user_private_key,
    'ownerAddress': user_wallet_address
})

data = response.json()
safe_address = data['safeAddress']

# Create order (GASLESS)
response = requests.post('http://localhost:3001/create-order', json={
    'privateKey': user_private_key,
    'safeAddress': safe_address,
    'tokenID': market_id,
    'side': 'BUY',
    'price': '0.75',
    'size': '10'
})

order = response.json()
print('Order placed:', order['orderID'])
```

---

## 🚀 Deployment

### Railway

1. **Create new service in Railway**
2. **Connect to GitHub repo**
3. **Set environment variables:**
   ```
   POLYMARKET_API_KEY=your-key
   POLYMARKET_SECRET=your-secret
   POLYMARKET_PASSPHRASE=your-passphrase
   PORT=3001
   ```
4. **Deploy!**

Railway will auto-detect `package.json` and run `npm start`.

---

## 🔒 Security Notes

⚠️ **CRITICAL:**
- NEVER commit `.env` to git
- NEVER share your API credentials
- Use environment variables in production
- Keep `.gitignore` up to date

---

## ✅ Benefits

| Feature | Before (Direct USDC) | After (Relayer) |
|---------|---------------------|-----------------|
| Gas fees | $0.01-0.05 per trade | **FREE!** ✅ |
| Approval | Required | **Not needed** ✅ |
| POL needed | Yes | **NO** ✅ |
| Speed | 5-30 seconds | **Instant** ✅ |
| Attribution | None | **Polybot.finance** ✅ |

---

## 🧪 Testing

```bash
# Test health endpoint
curl http://localhost:3001/health

# Test with real credentials (development only)
curl -X POST http://localhost:3001/deploy-safe \
  -H "Content-Type: application/json" \
  -d '{
    "privateKey": "0x...",
    "ownerAddress": "0x..."
  }'
```

---

## 📚 Documentation

- Polymarket Docs: https://docs.polymarket.com/
- Builder Program: https://builders.polymarket.com/
- CLOB Client: https://github.com/Polymarket/clob-client

---

## 🐛 Troubleshooting

### "Invalid API credentials"
→ Check your `.env` file has correct credentials

### "Network error"
→ Check RPC_URL is working

### "Order failed"
→ Check Safe wallet is deployed first

---

## 📝 License

MIT
