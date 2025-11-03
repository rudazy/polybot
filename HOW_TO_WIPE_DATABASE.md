# How to Wipe All Database Accounts

## ⚡ FASTEST METHOD: Use API Endpoint (Recommended)

I just added a database wipe API endpoint that you can call from your browser or terminal.

### Step 1: Call the Wipe Endpoint

**Using your browser:**
```
https://polymarket-bot-api-production.up.railway.app/debug/wipe-database?confirm=WIPE_EVERYTHING
```

**Using curl:**
```bash
curl -X POST "https://polymarket-bot-api-production.up.railway.app/debug/wipe-database?confirm=WIPE_EVERYTHING"
```

### Step 2: Verify Wipe Completed

You'll get a response like:
```json
{
  "success": true,
  "message": "Database wiped successfully",
  "total_documents_deleted": 157,
  "collections_wiped": [
    {
      "collection": "users",
      "documents_before": 45,
      "documents_deleted": 45
    },
    {
      "collection": "wallets",
      "documents_before": 45,
      "documents_deleted": 45
    },
    {
      "collection": "settings",
      "documents_before": 45,
      "documents_deleted": 45
    },
    {
      "collection": "trades",
      "documents_before": 22,
      "documents_deleted": 22
    }
  ],
  "timestamp": "2025-11-03T..."
}
```

✅ **Done!** All users, wallets, trades, settings wiped.

---

## 🔧 METHOD 2: Run Script on Railway

If the API endpoint doesn't work, run the script directly on Railway.

### Step 1: SSH into Railway

```bash
railway run bash
```

### Step 2: Run Force Wipe Script

```bash
python force_wipe_db.py
```

This will immediately wipe all data (no confirmation needed).

---

## 🌐 METHOD 3: MongoDB Atlas Web Interface

If both above methods fail, wipe manually via MongoDB Atlas.

### Step 1: Go to MongoDB Atlas

1. Visit: https://cloud.mongodb.com/
2. Login with your credentials

### Step 2: Navigate to Collections

1. Click "Clusters" → Your cluster
2. Click "Browse Collections"
3. Select database: `polymarket_bot`

### Step 3: Delete All Documents from Each Collection

For EACH collection (users, wallets, trades, settings, points, activity_log):

1. Click the collection name
2. Click the "..." menu (three dots)
3. Select "Delete Documents"
4. In the filter, enter: `{}`
5. Click "Delete"
6. Confirm deletion

**Repeat for all collections:**
- users
- wallets
- trades
- settings
- points
- activity_log

---

## ✅ Verify Database is Empty

After wiping, check that database is empty:

### Option 1: Check via API

```bash
curl https://polymarket-bot-api-production.up.railway.app/health
```

You should see user count = 0 (or the health endpoint doesn't show user count, but registration should work after wipe).

### Option 2: Check MongoDB Atlas

Go to Collections → Each collection should show "0 documents"

---

## 🧪 Test After Wipe

Try registering a new user:

```bash
curl -X POST https://polymarket-bot-api-production.up.railway.app/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test123@example.com","password":"test123"}'
```

**Expected:**
```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {...},
  "wallet": {
    "wallet_address": "0x...",
    "wallet_type": "in-app"
  }
}
```

---

## 🚨 Common Issues

### Issue: "confirm parameter required"

You forgot to add `?confirm=WIPE_EVERYTHING` to the URL.

**Fix:**
```
# Wrong
https://...up.railway.app/debug/wipe-database

# Right
https://...up.railway.app/debug/wipe-database?confirm=WIPE_EVERYTHING
```

### Issue: "Method Not Allowed"

Make sure you're using **POST**, not GET.

**Fix:**
```bash
curl -X POST "https://...?confirm=WIPE_EVERYTHING"
```

### Issue: Database wipe endpoint returns 404

Railway hasn't deployed the latest code yet. Wait 2-3 minutes for deployment to complete.

---

## 📊 What Gets Deleted

When you wipe the database, ALL of these are deleted:

| Collection | Data Lost |
|------------|-----------|
| `users` | All user accounts |
| `wallets` | All wallet addresses and encrypted private keys |
| `trades` | All trading history |
| `settings` | All user settings and bot configurations |
| `points` | All points balances and transactions |
| `activity_log` | All activity logs |

**⚠️ THIS CANNOT BE UNDONE!**

---

## 🎯 Recommended Flow

For development/testing:

1. **Wipe database** using API endpoint
2. **Test registration** with fresh account
3. **Test wallet creation**
4. **Test trading features**
5. **Repeat** as needed during development

For production:

1. **DON'T WIPE!** 😄
2. Use unique test emails instead
3. Or create separate test database

---

## 💡 Pro Tip

During development, you can wipe and test quickly:

```bash
# 1. Wipe database
curl -X POST "https://polymarket-bot-api-production.up.railway.app/debug/wipe-database?confirm=WIPE_EVERYTHING"

# 2. Test registration immediately
curl -X POST https://polymarket-bot-api-production.up.railway.app/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'

# 3. Check if it worked
curl https://polymarket-bot-api-production.up.railway.app/health
```

---

**Last Updated:** November 3, 2025
**Status:** ✅ Wipe endpoint deployed and ready to use
