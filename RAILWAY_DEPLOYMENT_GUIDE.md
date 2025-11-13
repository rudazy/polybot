# Railway Deployment Guide for Polymarket Trading Bot

## 🚂 Railway Configuration

### ✅ Files Created

1. **`railway.json`** - Railway configuration
2. **`Procfile`** - Process file for deployment
3. **`requirements.txt`** - Updated with all dependencies

---

## 🔧 Environment Variables for Railway

Go to your Railway project dashboard → Variables tab and add these:

### **Required Environment Variables:**

```bash
# MongoDB Database
MONGODB_URI=mongodb+srv://your-username:your-password@cluster.mongodb.net/polymarket_bot?retryWrites=true&w=majority

# Polymarket Builder Program (Optional - for trade attribution)
POLYMARKET_BUILDER_API_KEY=your_builder_api_key
POLYMARKET_BUILDER_SECRET=your_builder_secret
POLYMARKET_BUILDER_PASSPHRASE=your_builder_passphrase

# API Configuration
PORT=8000
PYTHON_VERSION=3.11
```

### **Environment Variable Details:**

#### 1. **MONGODB_URI** (REQUIRED)
Your MongoDB Atlas connection string.

**Format:**
```
mongodb+srv://<username>:<password>@<cluster>.mongodb.net/polymarket_bot?retryWrites=true&w=majority
```

**How to get it:**
1. Go to MongoDB Atlas dashboard
2. Click "Connect" on your cluster
3. Choose "Connect your application"
4. Copy the connection string
5. Replace `<username>` and `<password>` with your credentials

#### 2. **POLYMARKET_BUILDER_API_KEY** (Optional)
Your Polymarket Builder Program API key for trade attribution.

**How to get it:**
1. Apply to Polymarket Builder Program
2. Get approved and receive API credentials
3. Add them to Railway

**Note:** Trading works WITHOUT builder credentials, but trades won't be attributed to your builder account.

#### 3. **PORT** (Automatically set by Railway)
Railway automatically sets this. You can leave it as `8000` or omit it.

---

## 📦 Contract Addresses (Pre-configured)

These are already hardcoded in the backend:

```bash
✅ USDC.e Address: 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174
✅ Polymarket Exchange: 0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E
✅ Chain ID: 137 (Polygon Mainnet)
```

**IMPORTANT:**
- This is USDC.e (bridged USDC), NOT native USDC
- Users must deposit USDC.e to trade on Polymarket

---

## 🚀 Deployment Steps

### **1. Commit Changes**

```bash
git add .
git commit -m "Add Railway config and USDC approval functionality"
git push origin main
```

### **2. Railway Configuration**

1. Go to your Railway dashboard
2. Click on your `polymarket-bot-api-production` project
3. Go to **Settings** → **Environment Variables**
4. Add the environment variables listed above

### **3. Verify Deployment**

Once deployed, Railway will automatically:
- Install dependencies from `requirements.txt`
- Start the server using the command in `Procfile`
- Expose your API at: `https://polymarket-bot-api-production.up.railway.app`

### **4. Test the Deployment**

**Check health endpoint:**
```bash
curl https://polymarket-bot-api-production.up.railway.app/
```

Expected response:
```json
{
  "status": "ok",
  "message": "Polymarket Trading Bot API"
}
```

---

## 🔍 Testing USDC Approval

### **1. Create a Test Account**

1. Go to https://polybot.finance
2. Click "Sign Up"
3. Create account with email/password
4. A Safe Wallet will be created automatically

### **2. Fund the Wallet**

You need both POL and USDC.e:

**POL (for gas fees):**
- Send ~0.05-0.1 POL to your wallet address
- Required for USDC approval transaction (~0.01-0.02 POL)

**USDC.e (for trading):**
- Bridge USDC from Ethereum to Polygon using [Polygon Bridge](https://wallet.polygon.technology/bridge)
- Or buy USDC.e directly on Polygon
- Send USDC.e to your wallet address

**Check balances:**
```bash
curl https://polymarket-bot-api-production.up.railway.app/wallet/{user_id}
```

### **3. Approve USDC.e**

**Option A: From UI**
1. Login to your dashboard at https://polybot.finance
2. Look for the green **"Approve USDC.e"** button in the Wallet section
3. Click it and confirm the transaction
4. Wait ~30 seconds for blockchain confirmation
5. Button will change to "✓ Approved"

**Option B: Via API**
```bash
curl -X POST https://polymarket-bot-api-production.up.railway.app/wallet/approve-usdc/{user_id}
```

**Success response:**
```json
{
  "success": true,
  "message": "USDC approved for Polymarket trading!",
  "tx_hash": "0x...",
  "explorer_url": "https://polygonscan.com/tx/0x...",
  "amount_approved": "unlimited"
}
```

### **4. Verify Approval**

Check if USDC.e is approved:
```bash
curl https://polymarket-bot-api-production.up.railway.app/wallet/usdc-allowance/{user_id}
```

Expected response (if approved):
```json
{
  "success": true,
  "allowance": "115792089237316195423570985008687907853269984665640564039457584007913129639935",
  "is_approved": true,
  "wallet_address": "0x..."
}
```

### **5. Place a Test Trade**

Once approved, you can trade:

1. Go to the Manual Trading section
2. Paste a Polymarket URL or click a market from trending/live sports
3. Select YES or NO
4. Enter amount (e.g., 1 USDC.e)
5. Click "Execute Trade"

---

## 🐛 Troubleshooting

### **Issue: "USDC approval failed"**

**Cause:** Not enough POL for gas fees

**Solution:**
```bash
# Check POL balance
curl https://polymarket-bot-api-production.up.railway.app/wallet/{user_id}

# If POL balance < 0.01, send more POL to the wallet address
```

### **Issue: "Insufficient POL for gas fees"**

**Solution:**
Send at least 0.05 POL to your wallet's owner address (for Safe Wallets) or wallet address (for in-app wallets).

### **Issue: "External wallet detected"**

**Cause:** You connected an external wallet (MetaMask, Rabby)

**Solution:**
For external wallets, USDC approval happens automatically when you make your first trade. The wallet will show an approval popup.

### **Issue: Railway deployment fails**

**Check logs:**
1. Go to Railway dashboard
2. Click on your deployment
3. View logs for errors

**Common fixes:**
- Verify all environment variables are set
- Check MongoDB connection string is correct
- Ensure `requirements.txt` is up to date

---

## 📊 Monitoring

### **Check Backend Health**

```bash
# Basic health check
curl https://polymarket-bot-api-production.up.railway.app/

# Check wallet status
curl https://polymarket-bot-api-production.up.railway.app/wallet/{user_id}

# Check USDC allowance
curl https://polymarket-bot-api-production.up.railway.app/wallet/usdc-allowance/{user_id}
```

### **Railway Logs**

View real-time logs in Railway dashboard to monitor:
- API requests
- USDC approval transactions
- Trade executions
- Errors

---

## 🔐 Security Notes

1. **Never commit `.env` file to git** - It contains secrets
2. **Use environment variables in Railway** for all sensitive data
3. **USDC.e approval is safe** - It only approves the Polymarket Exchange contract
4. **Unlimited approval is standard** - Used by all DEXes to reduce gas fees
5. **Private keys are encrypted** in MongoDB

---

## ✅ Deployment Checklist

- [ ] Railway project created
- [ ] GitHub repo connected to Railway
- [ ] All environment variables set in Railway
- [ ] Code pushed to GitHub (main branch)
- [ ] Deployment successful (check Railway logs)
- [ ] Health endpoint responds
- [ ] Test account created
- [ ] Wallet funded with POL and USDC.e
- [ ] USDC.e approval works
- [ ] Test trade executes successfully

---

## 🆘 Support

If you encounter issues:

1. **Check Railway logs** for detailed error messages
2. **Verify environment variables** are set correctly
3. **Test locally first** with `uvicorn api_server:app --reload`
4. **Check Polygon network status** at [Polygonscan](https://polygonscan.com)

---

## 📝 File Summary

### **Backend Files Modified:**
- ✅ `railway.json` - Railway config (NEW)
- ✅ `Procfile` - Start command (NEW)
- ✅ `requirements.txt` - Updated dependencies
- ✅ `api_server.py` - Already has `/wallet/approve-usdc` endpoint
- ✅ `blockchain_manager.py` - Already has `approve_usdc()` method
- ✅ `polymarket_integration.py` - USDC.e address comment updated

### **Frontend Files Modified:**
- ✅ `frontend/index.html` - Added "Approve USDC.e" button
- ✅ `frontend/app.js` - Added `handleApproveUSDC()` function
- ✅ `frontend/styles.css` - Added `.btn-approve` styles

---

## 🎉 Success!

Your Polymarket trading bot is now production-ready with:

✅ Railway deployment configuration
✅ USDC.e approval functionality (UI + API)
✅ Proper error handling and logging
✅ Transaction confirmation and feedback
✅ Correct contract addresses verified

**Next step:** Push to GitHub and let Railway auto-deploy!
