# 🚀 Deploy to Railway - Quick Start

## Step 1: Set Environment Variables in Railway

Go to: https://railway.app/project/your-project-id/settings

Click **Variables** tab and add:

```bash
MONGODB_URI=mongodb+srv://your-username:your-password@cluster.mongodb.net/polymarket_bot?retryWrites=true&w=majority
```

Optional (for Builder Program):
```bash
POLYMARKET_BUILDER_API_KEY=your_key
POLYMARKET_BUILDER_SECRET=your_secret
POLYMARKET_BUILDER_PASSPHRASE=your_passphrase
```

---

## Step 2: Commit and Push

```bash
# Add all changes
git add .

# Commit with message
git commit -m "Add Railway config and fix USDC approval

- Created railway.json and Procfile for Railway deployment
- Added USDC.e approval button and handleApproveUSDC() function
- Updated frontend to use Railway API in production
- Fixed all USDC references to USDC.e
- Verified contract addresses (USDC.e and Polymarket Exchange)
- Added comprehensive deployment documentation"

# Push to GitHub
git push origin main
```

---

## Step 3: Wait for Railway Deployment

Railway will automatically:
1. Detect the push
2. Install dependencies
3. Deploy to production

**Your API:** https://polymarket-bot-api-production.up.railway.app

---

## Step 4: Verify It's Working

```bash
# Check health
curl https://polymarket-bot-api-production.up.railway.app/

# Should see:
{
  "status": "ok",
  "message": "Polymarket Trading Bot API"
}
```

---

## Step 5: Test USDC Approval

1. Go to https://polybot.finance
2. Create test account
3. Fund wallet with:
   - ~0.05 POL (for gas)
   - ~5 USDC.e (for trading)
4. Click **"Approve USDC.e"** button
5. Confirm transaction
6. See "✓ Approved" when done
7. Trade!

---

## ✅ Files Modified (Ready to Commit)

**New Files:**
- railway.json
- Procfile
- RAILWAY_DEPLOYMENT_GUIDE.md
- PRODUCTION_FIXES_SUMMARY.md
- DEPLOY_NOW.md

**Modified Files:**
- requirements.txt
- frontend/index.html (added approve button)
- frontend/app.js (added handleApproveUSDC function)
- frontend/styles.css (added .btn-approve styles)
- polymarket_integration.py (USDC.e comment)

---

## 🎯 That's It!

Just run the git commands above and Railway will handle the rest!

**Questions?** Check RAILWAY_DEPLOYMENT_GUIDE.md for detailed info.
