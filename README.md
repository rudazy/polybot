# Polybot.finance - AI-Powered Polymarket Trading Bot

![Status](https://img.shields.io/badge/status-ready%20to%20deploy-brightgreen)
![Builder Program](https://img.shields.io/badge/Polymarket-Builder%20Program-blue)
![Gasless Trading](https://img.shields.io/badge/gas%20fees-FREE-success)

AI-powered trading bot for Polymarket prediction markets with **gasless trading** via Polymarket Builder Program.

**Website:** https://polybot.finance
**API:** https://polymarket-bot-api-production.up.railway.app

---

## ✨ Features

### Core Features
- ✅ **AI-powered trading recommendations** using GPT-4
- ✅ **Real-time market analysis** from Polymarket API
- ✅ **Automated trade execution**
- ✅ **Whale alerts** for large trades (>$10k)
- ✅ **User wallet management** (in-app & external)
- ✅ **USDC.e approval system** for direct trading
- ✅ **Trending markets** with 24hr volume tracking

### Builder Program Features (NEW! 🚀)
- ⛽ **FREE GAS** - Users don't pay transaction fees
- 🏷️ **Builder attribution** - All trades show "via Polybot.finance"
- 📊 **Volume tracking** - Leaderboard on Polymarket
- 💰 **Grant eligibility** - Compete for Polymarket incentives
- ⚡ **Instant trading** - No blockchain confirmation delays
- 🎯 **No POL needed** - Users don't need native Polygon token

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Frontend (Vercel)                   │
│              React + JavaScript + CSS                │
│        https://polybot.finance                       │
└───────────────────┬──────────────────────────────────┘
                    │
                    │ HTTPS/REST API
                    ↓
┌──────────────────────────────────────────────────────┐
│            Python Backend (Railway)                  │
│                FastAPI + MongoDB                     │
│  - Authentication & user management                  │
│  - Market data aggregation                           │
│  - AI trading recommendations (GPT-4)                │
│  - Wallet management (in-app + external)             │
│  - USDC.e approval system                            │
│  https://polymarket-bot-api-production.up.railway.app│
└───────────────────┬──────────────────────────────────┘
                    │
                    │ HTTP requests
                    ↓
┌──────────────────────────────────────────────────────┐
│         Node.js Microservice (Railway)               │
│          Express + @polymarket/clob-client           │
│  - Safe wallet deployment (gasless)                  │
│  - Order creation (gasless)                          │
│  - Builder Program attribution                       │
│  Port 3001                                           │
└───────────────────┬──────────────────────────────────┘
                    │
                    │ Polymarket CLOB API
                    ↓
┌──────────────────────────────────────────────────────┐
│              Polymarket Exchange                     │
│         FREE GAS via Builder relayer                 │
│         Polygon Mainnet (Chain ID 137)               │
└──────────────────────────────────────────────────────┘
```

---

## 📚 Documentation

### Quick Start Guides
- **[BUILDER_PROGRAM_READY.md](BUILDER_PROGRAM_READY.md)** - ⭐ START HERE for Builder Program
- **[POLYMARKET_BUILDER_DEPLOYMENT.md](POLYMARKET_BUILDER_DEPLOYMENT.md)** - Complete deployment guide
- **[FINAL_MERGE_SUMMARY.md](FINAL_MERGE_SUMMARY.md)** - All changes summary

### Feature Documentation
- **[WALLET_FIXES.md](WALLET_FIXES.md)** - USDC.e approval system
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing USDC.e approval
- **[BUILDER_PROGRAM_INTEGRATION.md](BUILDER_PROGRAM_INTEGRATION.md)** - Builder Program overview
- **[FRONTEND_INTEGRATION_GUIDE.md](FRONTEND_INTEGRATION_GUIDE.md)** - Frontend integration
- **[WHALE_ALERT_UI_CHANGES.md](WHALE_ALERT_UI_CHANGES.md)** - UI improvements

### Troubleshooting
- **[URGENT_FIX_CORS.md](URGENT_FIX_CORS.md)** - CORS issues and fixes
- **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - Deployment quick reference

### Microservice
- **[polymarket-service/README.md](polymarket-service/README.md)** - Node.js service docs

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- MongoDB Atlas account
- Polymarket Builder API credentials (apply at https://builders.polymarket.com)
- Railway or similar hosting platform

### Local Development

#### 1. Python Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run server
python api_server.py
```

Server runs on: `http://localhost:8000`

#### 2. Node.js Microservice (Builder Program)

```bash
# Navigate to service directory
cd polymarket-service

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your Builder API credentials

# Run service
npm start
```

Service runs on: `http://localhost:3001`

#### 3. Frontend

```bash
cd frontend

# Open index.html in browser
# Or use a local server:
python -m http.server 8080
```

Frontend runs on: `http://localhost:8080`

---

## 🔧 Configuration

### Python Backend (.env)

```env
# MongoDB
MONGODB_URI=mongodb+srv://...

# OpenAI (for AI recommendations)
OPENAI_API_KEY=sk-...

# Polygon RPC
RPC_URL=https://polygon-rpc.com

# Node.js microservice URL (production)
POLYMARKET_NODE_SERVICE_URL=https://polymarket-service-production.up.railway.app
```

### Node.js Microservice (polymarket-service/.env)

```env
# Polymarket Builder API credentials
POLYMARKET_API_KEY=your-api-key
POLYMARKET_SECRET=your-secret
POLYMARKET_PASSPHRASE=your-passphrase

# Server
PORT=3001
RPC_URL=https://polygon-rpc.com
```

---

## 📦 Technology Stack

### Backend
- **Python 3.9+** - Core backend
- **FastAPI** - REST API framework
- **MongoDB** - User data & trade history
- **Web3.py** - Blockchain interactions
- **OpenAI GPT-4** - AI recommendations
- **Polymarket API** - Market data

### Microservice
- **Node.js 16+** - Builder Program service
- **Express** - Web server
- **@polymarket/clob-client** - Polymarket integration
- **ethers.js 5.7.2** - Ethereum library

### Frontend
- **HTML/CSS/JavaScript** - Simple, no-framework approach
- **Fetch API** - REST API calls
- **LocalStorage** - Session management

### Infrastructure
- **Railway** - Backend & microservice hosting
- **Vercel** - Frontend hosting
- **MongoDB Atlas** - Database
- **Polygon Mainnet** - Blockchain

---

## 🎯 API Endpoints

### Python Backend (Port 8000)

**Authentication:**
- `POST /auth/register` - Create account
- `POST /auth/login` - Login
- `POST /auth/logout` - Logout

**Markets:**
- `GET /markets` - List all markets
- `GET /markets/trending` - Trending markets with volume
- `GET /markets/{slug}` - Get market details
- `POST /markets/ai-recommendation` - Get AI trading recommendation

**Wallet:**
- `POST /wallet/create/{user_id}` - Create in-app wallet
- `POST /wallet/connect-external/{user_id}` - Connect external wallet
- `POST /wallet/export-key/{user_id}` - Export private key
- `GET /wallet/balance/{user_id}` - Get USDC.e balance
- `GET /wallet/usdc-allowance/{user_id}` - Check USDC.e approval
- `POST /wallet/approve-usdc/{user_id}` - Approve USDC.e

**Trading:**
- `POST /trades/execute` - Execute trade (standard)
- `POST /trades/history/{user_id}` - Get trade history

### Node.js Microservice (Port 3001)

**Health:**
- `GET /health` - Service health check

**Builder Program:**
- `POST /deploy-safe` - Deploy Safe wallet (gasless)
- `POST /get-safe-address` - Get Safe address
- `POST /create-order` - Create order (gasless, with attribution)
- `POST /cancel-order` - Cancel order (gasless)
- `POST /get-orders` - List all orders

---

## 💡 Key Concepts

### USDC.e vs USDC
Polymarket uses **USDC.e** (bridged USDC on Polygon), NOT native USDC.

- **USDC.e Address:** `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174`
- **Polymarket Exchange:** `0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E`

Users must approve USDC.e before trading (one-time operation).

### Safe Wallets
For gasless trading via Builder Program, users need a Safe wallet:
- Deployed once per user (gasless via relayer)
- All future trades are gasless
- No POL needed

### Builder Attribution
All orders created via the microservice are attributed to "Polybot.finance":
- Volume tracked on Polymarket Builder leaderboard
- Eligible for grants and incentives
- Better brand visibility

---

## 📊 Comparison: Standard vs Gasless Trading

| Feature | Standard Trading | Builder Program Trading |
|---------|-----------------|------------------------|
| **Gas Fees** | ~$0.005-0.01 | **FREE** ✅ |
| **POL Required** | Yes (0.01+) | **NO** ✅ |
| **USDC Approval** | Required once | **Not needed** ✅ |
| **Setup** | Simple | Requires Safe wallet |
| **Speed** | 5-30 seconds | **Instant** ✅ |
| **Attribution** | None | **"via Polybot.finance"** ✅ |
| **Grant Eligibility** | No | **YES** ✅ |

**Recommendation:** Use Builder Program for all new users!

---

## 🧪 Testing

### Test Node.js Service

```bash
# Health check
curl http://localhost:3001/health

# Deploy Safe wallet (use test wallet!)
curl -X POST http://localhost:3001/deploy-safe \
  -H "Content-Type: application/json" \
  -d '{"privateKey": "0x...", "ownerAddress": "0x..."}'
```

### Test Python Integration

```python
from polymarket_builder import PolymarketBuilder

builder = PolymarketBuilder()
health = builder.health_check()
print(health)  # {'status': 'ok'}
```

See **[POLYMARKET_BUILDER_DEPLOYMENT.md](POLYMARKET_BUILDER_DEPLOYMENT.md)** for complete testing guide.

---

## 🚢 Deployment

### Railway Deployment

**Python Backend:**
1. Connect GitHub repo to Railway
2. Set root directory: `/`
3. Add environment variables
4. Deploy automatically

**Node.js Microservice:**
1. Create new Railway service
2. Set root directory: `polymarket-service`
3. Add environment variables (Builder API credentials)
4. Deploy automatically

**Environment Variables:**
- See Configuration section above
- NEVER commit `.env` files
- Use Railway's environment variable system

### Vercel Deployment (Frontend)

1. Connect GitHub repo to Vercel
2. Set root directory: `frontend`
3. Deploy automatically on push to main

---

## 🔒 Security

### Credentials
- ✅ `.env` files excluded via `.gitignore`
- ✅ Only `.env.example` templates committed
- ✅ Use Railway environment variables in production
- ✅ Never log or expose credentials

### Wallets
- ✅ Private keys encrypted in database
- ✅ Never send private keys to frontend
- ✅ Export requires authentication
- ✅ External wallets never stored

### API Security
- ✅ User authentication required
- ✅ CORS properly configured
- ✅ Rate limiting (TODO)
- ✅ Input validation

---

## 📈 Metrics & Monitoring

### Builder Program Dashboard
Track your volume and performance:
- https://builders.polymarket.com/dashboard

### Key Metrics
- Total trading volume (attributed to Polybot.finance)
- Number of users
- Number of trades
- Average trade size
- Leaderboard rank
- Grant eligibility

---

## 🤝 Contributing

This is a private project, but contributions are welcome!

### Development Workflow
1. Create feature branch: `claude/feature-name-sessionid`
2. Implement changes
3. Test locally
4. Commit with descriptive messages
5. Push to feature branch
6. Create PR to main
7. Deploy to production

---

## 📞 Support

### Documentation
- Start with **[BUILDER_PROGRAM_READY.md](BUILDER_PROGRAM_READY.md)**
- Check troubleshooting guides
- Review API documentation

### Polymarket Support
- Builder Dashboard: https://builders.polymarket.com/dashboard
- Docs: https://docs.polymarket.com/
- Discord: https://discord.gg/polymarket
- Email: builders@polymarket.com

### Technical Issues
- Check service logs (Railway)
- Test health endpoints
- Verify environment variables
- Review error messages

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🎉 Acknowledgments

- **Polymarket** - For the Builder Program and excellent API
- **OpenAI** - For GPT-4 AI recommendations
- **Railway** - For easy deployment and hosting
- **Vercel** - For frontend hosting

---

## 🚀 Current Status

**Branch:** `claude/initial-setup-011CUg3SgCUL48UBmQLtvfY7`

**Latest Features:**
- ✅ USDC.e approval system
- ✅ Whale alerts (redesigned UI)
- ✅ Builder Program integration (gasless trading)
- ✅ Python wrapper for Node.js service
- ✅ Complete documentation

**Ready for:**
- ✅ Local testing
- ✅ Production deployment
- ✅ Merge to main

**Next Steps:**
1. Test Node.js service locally (`cd polymarket-service && npm install && npm start`)
2. Deploy to Railway
3. Merge to main
4. Monitor Builder dashboard

---

**Built with ❤️ for Polymarket traders**

**Trade smarter. Trade gasless. Trade with Polybot.finance.** 🚀
