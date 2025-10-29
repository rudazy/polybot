# Polymarket Bot - Vercel Deployment Guide (UPDATED)

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **MongoDB Atlas**: Your MongoDB connection string
3. **GitHub Account**: Your code repository

## Important Fixes Applied

This deployment guide has been updated to fix the following issues:
- ✅ Added Mangum adapter for FastAPI on Vercel
- ✅ Fixed API routing configuration
- ✅ Improved MongoDB environment variable handling
- ✅ Updated vercel.json for proper serverless deployment
- ✅ Fixed CORS configuration for production

## Step-by-Step Deployment

### 1. Commit Your Changes

```bash
# Add all files including the fixes
git add .

# Commit with descriptive message
git commit -m "Fix Vercel deployment: add mangum, update routing, fix env vars"

# Push to GitHub
git push origin main
```

### 2. Deploy to Vercel

#### Option A: Using Vercel Dashboard (Recommended)

1. Go to [vercel.com](https://vercel.com) and login
2. Click **"Add New Project"**
3. Import your GitHub repository
4. Configure the project:
   - **Framework Preset**: Other
   - **Root Directory**: ./
   - **Build Command**: (leave empty)
   - **Output Directory**: (leave empty - handled by vercel.json)

5. Add Environment Variables (CRITICAL):
   - Click **"Environment Variables"**
   - Add: `MONGODB_URI` = `your_mongodb_connection_string`
   - Example: `mongodb+srv://username:password@cluster.mongodb.net/polymarket_bot`

6. Click **"Deploy"**
7. Wait 2-3 minutes for deployment to complete

#### Option B: Using Vercel CLI

```bash
# Install Vercel CLI globally
npm i -g vercel

# Login to Vercel
vercel login

# Deploy (first time)
vercel

# Follow the prompts:
# - Setup and deploy? Yes
# - Which scope? (select your account)
# - Link to existing project? No
# - What's your project name? polymarket-bot
# - In which directory is your code? ./
# - Want to override settings? No

# Add environment variables
vercel env add MONGODB_URI

# Deploy to production
vercel --prod
```

## Environment Variables

**CRITICAL**: You MUST set these in Vercel Dashboard or CLI:

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `MONGODB_URI` | MongoDB connection string | **YES** | `mongodb+srv://user:pass@cluster.mongodb.net/polymarket_bot` |

### How to Add Environment Variables in Vercel:

1. Go to your project in Vercel Dashboard
2. Click **Settings** → **Environment Variables**
3. Add `MONGODB_URI` with your connection string
4. Make sure to add it for **Production**, **Preview**, and **Development**
5. Click **Save**
6. **IMPORTANT**: After adding env vars, redeploy your project!

## Post-Deployment Testing

### 1. Test Your Deployment

Visit your deployed URL (e.g., `https://polymarket-bot.vercel.app`)

### 2. Verify API is Working

Test these endpoints:

1. **Health Check**: `https://your-app.vercel.app/api/`
   - Should return: `{"status": "online", "message": "Polymarket Trading Bot API", ...}`

2. **Markets**: `https://your-app.vercel.app/api/markets?limit=5`
   - Should return list of markets

3. **Network Status** (requires login): `https://your-app.vercel.app/api/network/status/test`

### 3. Test All Features

Once deployed, test these features:

- ✅ **Registration**: Create a new account
- ✅ **Login**: Login with your account
- ✅ **Wallet Creation**: Create in-app wallet or connect MetaMask
- ✅ **Network Switching**: Switch between testnet/mainnet
- ✅ **Trending Markets**: Should load market data
- ✅ **Top 5 Traders**: Should show leaderboard
- ✅ **Trading**: Execute a test trade

### 4. Check Vercel Function Logs

If something doesn't work:

1. Go to Vercel Dashboard → Your Project → **Deployments**
2. Click on the latest deployment
3. Click **Functions** tab
4. Look for errors in the logs

### 2. Configure Custom Domain (Optional)

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your custom domain
3. Follow DNS configuration instructions

## Important Notes

### ⚠️ Limitations on Vercel

1. **Serverless Functions**: Backend runs as serverless functions (not persistent)
2. **Execution Time**: Max 60 seconds per request on Free plan
3. **Background Jobs**: Trading bots won't run continuously
4. **MongoDB**: Keep your MongoDB Atlas connection string secure

### 🔄 For Production Trading Bot

If you need persistent background processes (trading bot running 24/7), consider:

1. **Railway.app** - Better for long-running processes
2. **Render.com** - Free tier with persistent services
3. **DigitalOcean App Platform** - Full Python support
4. **AWS/GCP/Azure** - Full control

### 📊 Alternative: Hybrid Approach

- **Frontend**: Deploy to Vercel (free, fast)
- **Backend**: Deploy to Railway/Render (persistent processes)
- Update `API_URL` in `frontend/app.js` to point to backend URL

## Troubleshooting

### Issue: "Can't register - check API server"

**Fix:**
1. Check that `MONGODB_URI` environment variable is set in Vercel
2. Go to Vercel Dashboard → Settings → Environment Variables
3. Make sure the MongoDB connection string is correct
4. Redeploy after adding/changing environment variables

### Issue: "Can't switch network"

**Fix:**
1. Make sure you're logged in first
2. The API endpoint should be `/api/network/switch/{user_id}`
3. Check browser console for errors (F12)
4. Verify the API is responding: visit `https://your-app.vercel.app/api/`

### Issue: "Top 5 wallets not showing"

**Fix:**
1. This is normal for new deployments (no users yet)
2. The API will return demo/sample traders automatically
3. Check API endpoint: `https://your-app.vercel.app/api/traders/top`
4. Look for errors in Vercel function logs

### Issue: "Can't see trending markets"

**Fix:**
1. The app fetches from Polymarket API
2. Check that `/api/markets` endpoint is working
3. Test: `https://your-app.vercel.app/api/markets?limit=10`
4. If it returns data, check browser console for frontend errors
5. Clear browser cache and reload

### Error: Module not found (mangum)

**Fix:**
- Make sure `requirements.txt` includes `mangum==0.17.0`
- Redeploy after updating requirements.txt

### Error: MongoDB connection failed

**Fix:**
- Verify `MONGODB_URI` environment variable is set correctly
- Check MongoDB Atlas allows connections from all IPs (0.0.0.0/0)
  - Go to MongoDB Atlas → Network Access → Add IP Address → Allow from Anywhere
- Whitelist Vercel's IP addresses or use 0.0.0.0/0
- Make sure database user has read/write permissions

### Error: 500 Internal Server Error

**Fix:**
1. Check Vercel Function logs:
   - Go to Vercel Dashboard → Your Project → Deployments
   - Click on latest deployment → Functions tab
   - Look for error messages
2. Verify all environment variables are set
3. Test API endpoints individually
4. Check if MongoDB is accessible

### Error: CORS issues

**Fix:**
- The API is configured to allow all origins (`allow_origins=["*"]`)
- If you still get CORS errors, check browser console
- Make sure you're using `/api` prefix for all API calls
- Verify the frontend is using the correct API_URL

## Local Development

```bash
# Run backend
python api_server.py

# Open frontend
# Open frontend/index.html in browser
# Or use live-server: npx live-server frontend
```

## Project Structure

```
polymarket-bot/
├── api/
│   └── index.py          # Vercel serverless entry point
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── api_server.py         # FastAPI backend
├── mongodb_database.py
├── wallet_manager.py
├── blockchain_manager.py
├── trading_bot.py
├── polymarket_api.py
├── faucet_manager.py
├── vercel.json           # Vercel configuration
├── requirements.txt      # Python dependencies
└── .vercelignore        # Files to ignore

```

## Monitoring

- **Vercel Dashboard**: Monitor deployments and function logs
- **MongoDB Atlas**: Monitor database usage
- **Vercel Analytics**: Track frontend performance (optional)

## Support

- Vercel Docs: https://vercel.com/docs
- MongoDB Atlas: https://www.mongodb.com/docs/atlas/
- FastAPI: https://fastapi.tiangolo.com/

---

**Note**: This deployment is optimized for demo/testing. For production trading with real money, use a dedicated server with 24/7 uptime.
