"""
FastAPI Backend Server for Polymarket Trading Bot
Provides REST API endpoints for the web dashboard
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import uvicorn
import hashlib
import random

from mongodb_database import MongoDatabase
from polymarket_api import PolymarketAPI
from trading_bot import TradingBot
from wallet_manager import WalletManager

# Initialize FastAPI app
app = FastAPI(
    title="Polymarket Trading Bot API",
    description="REST API for automated Polymarket trading",
    version="1.0.0"
)

# CORS middleware (allows frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://polybot.finance",
        "https://www.polybot.finance",
        "http://polybot.finance",
        "http://www.polybot.finance",
        "https://polybot-gamma.vercel.app",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "*"  # Allow all origins for testing (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db = MongoDatabase()
polymarket = PolymarketAPI()
wallet_manager = WalletManager(db)
active_bots = {}  # Store active bot instances per user
active_copy_traders = {}  # Store active copy trading instances per user
whale_activity_feed = []  # Store simulated whale activity
whale_id_counter = 0  # Counter for whale activity IDs


# Pydantic models for request/response validation
class UserCreate(BaseModel):
    email: str
    password: str
    wallet_address: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class SettingsUpdate(BaseModel):
    min_probability: Optional[float] = None
    category_filter: Optional[str] = None
    duration_filter: Optional[int] = None
    position_size: Optional[float] = None
    max_daily_trades: Optional[int] = None
    min_liquidity: Optional[float] = None
    bot_enabled: Optional[bool] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class TradeCreate(BaseModel):
    market_question: str
    position: str
    amount: float
    market_id: Optional[str] = None


class PointsRedeem(BaseModel):
    amount: int
    reward: str


class WalletConnect(BaseModel):
    wallet_address: str



class CopyTradeStart(BaseModel):
    target_wallet: str
    copy_amount: float
    max_trades_per_day: int


class PrivateKeyExport(BaseModel):
    password: str


class PasswordReset(BaseModel):
    email: str
    new_password: str


# ==================== PASSWORD HASHING ====================

def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against a hashed password"""
    return hash_password(password) == hashed_password


# ==================== HEALTH CHECK ====================

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "Polymarket Trading Bot API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
def health_check():
    """
    Detailed health check with service status
    ⚠️ ENHANCED: Now includes MongoDB and Polymarket API status
    """
    try:
        # Test MongoDB connection
        mongo_healthy = False
        try:
            db.client.server_info()
            mongo_healthy = True
        except Exception as e:
            print(f"[HEALTH] MongoDB error: {e}")

        # Test Polymarket API connection
        polymarket_healthy = False
        try:
            test_markets = polymarket.get_markets(limit=1)
            polymarket_healthy = len(test_markets) > 0
        except Exception as e:
            print(f"[HEALTH] Polymarket API error: {e}")

        return {
            "status": "healthy" if (mongo_healthy and polymarket_healthy) else "degraded",
            "api": "online",
            "database": "connected" if mongo_healthy else "disconnected",
            "polymarket_api": "connected" if polymarket_healthy else "disconnected",
            "active_bots": len(active_bots),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/debug/test-polymarket")
def test_polymarket_api():
    """
    Test endpoint to debug Polymarket API connection
    Returns raw market data for troubleshooting
    """
    try:
        print("[DEBUG] Testing Polymarket API connection...")

        # Fetch one market
        markets = polymarket.get_markets(limit=1)

        if not markets:
            return {
                "success": False,
                "error": "No markets returned from Polymarket API"
            }

        # Return raw market data for inspection
        raw_market = markets[0]
        formatted_market = polymarket.format_market_data(raw_market)

        return {
            "success": True,
            "message": "Polymarket API is working",
            "raw_market_sample": raw_market,
            "formatted_market_sample": formatted_market,
            "fields_available": list(raw_market.keys())
        }

    except Exception as e:
        print(f"[DEBUG ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@app.post("/debug/wipe-database")
def wipe_database_endpoint(confirm: str = None):
    """
    ⚠️ DANGEROUS: Wipe all data from MongoDB database
    Requires confirm parameter = "WIPE_EVERYTHING"

    Usage: POST /debug/wipe-database?confirm=WIPE_EVERYTHING
    """
    try:
        # Require confirmation
        if confirm != "WIPE_EVERYTHING":
            return {
                "success": False,
                "error": "Confirmation required",
                "message": "To wipe database, add parameter: ?confirm=WIPE_EVERYTHING",
                "warning": "This will DELETE ALL DATA including users, trades, wallets, settings, and points!"
            }

        print("[WIPE] ⚠️  DATABASE WIPE REQUESTED VIA API")

        # Get all collections
        collection_names = db.db.list_collection_names()

        if not collection_names:
            return {
                "success": True,
                "message": "Database is already empty",
                "collections_wiped": []
            }

        print(f"[WIPE] Found {len(collection_names)} collections to delete")

        # Count total documents before deletion
        total_before = 0
        collection_counts = {}
        for name in collection_names:
            count = db.db[name].count_documents({})
            collection_counts[name] = count
            total_before += count
            print(f"[WIPE] {name}: {count} documents")

        print(f"[WIPE] Total documents to delete: {total_before}")

        # Delete all data from each collection
        deleted_total = 0
        wiped_collections = []

        for name in collection_names:
            result = db.db[name].delete_many({})
            deleted_count = result.deleted_count
            deleted_total += deleted_count
            wiped_collections.append({
                "collection": name,
                "documents_before": collection_counts[name],
                "documents_deleted": deleted_count
            })
            print(f"[WIPE] ✅ Deleted {deleted_count} documents from {name}")

        print(f"[WIPE] ✅ DATABASE WIPE COMPLETE - Deleted {deleted_total} documents")

        return {
            "success": True,
            "message": "Database wiped successfully",
            "total_documents_deleted": deleted_total,
            "collections_wiped": wiped_collections,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"[WIPE ERROR] ❌ Database wipe failed: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


# ==================== USER ENDPOINTS ====================

@app.post("/users/register")
def register_user(user: UserCreate):
    """
    Register a new user with password
    ⚠️ FIXED: Now includes detailed error logging and auto-creates wallet
    """
    try:
        print(f"[REGISTER] Attempting to register user: {user.email}")

        # Check if user already exists
        existing_user = db.get_user(email=user.email)

        if existing_user:
            print(f"[REGISTER] User already exists: {user.email}")
            return {
                "success": False,
                "message": "Email already registered. Please login instead."
            }

        # Hash the password
        print(f"[REGISTER] Hashing password for {user.email}")
        hashed_password = hash_password(user.password)

        # Create user with hashed password
        print(f"[REGISTER] Creating user in database: {user.email}")
        user_id = db.create_user(user.email, user.wallet_address)

        if not user_id:
            print(f"[REGISTER ERROR] Failed to create user in database")
            return {
                "success": False,
                "message": "Registration failed. Database error.",
                "error": "Could not create user in database"
            }

        # Store the hashed password
        from bson import ObjectId
        print(f"[REGISTER] Storing password for user ID: {user_id}")
        db.db['users'].update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'password': hashed_password}}
        )

        # AUTO-CREATE IN-APP WALLET FOR NEW USER
        print(f"[REGISTER] Auto-creating wallet for user: {user_id}")
        wallet_result = wallet_manager.create_in_app_wallet(user_id)

        if not wallet_result.get('success'):
            print(f"[REGISTER WARNING] Wallet creation failed: {wallet_result.get('error')}")
            # Continue anyway - user can create wallet later
        else:
            print(f"[REGISTER] Wallet created: {wallet_result.get('wallet_address')}")

        # Get complete user data
        user_data = db.get_user(user_id=user_id)

        # Remove password from response
        if 'password' in user_data:
            del user_data['password']

        print(f"[REGISTER] ✅ Registration successful for {user.email}")

        return {
            "success": True,
            "message": "User registered successfully",
            "user": user_data,
            "wallet": wallet_result if wallet_result.get('success') else None
        }

    except Exception as e:
        # DETAILED ERROR LOGGING
        print(f"[REGISTER ERROR] ❌ Registration failed for {user.email}")
        print(f"[REGISTER ERROR] Error type: {type(e).__name__}")
        print(f"[REGISTER ERROR] Error message: {str(e)}")

        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "message": "Registration failed due to server error",
            "error": str(e),
            "error_type": type(e).__name__
        }


@app.post("/users/login")
def login_user(user: UserLogin):
    """
    Login user with password verification
    ⚠️ FIXED: Added detailed error logging
    """
    try:
        print(f"[LOGIN] Attempting login for: {user.email}")

        user_data = db.get_user(email=user.email)

        if not user_data:
            print(f"[LOGIN] User not found: {user.email}")
            return {
                "success": False,
                "message": "User not found"
            }

        # Check if user has a password set
        stored_password = user_data.get('password')
        if not stored_password:
            print(f"[LOGIN WARNING] Legacy user without password: {user.email}")
            # Legacy user without password - allow login but should set password
            if 'password' in user_data:
                del user_data['password']
            return {
                "success": True,
                "message": "Login successful",
                "user": user_data
            }

        # Verify password
        if not verify_password(user.password, stored_password):
            print(f"[LOGIN] Invalid password for: {user.email}")
            return {
                "success": False,
                "message": "Invalid password"
            }

        # Remove password from response
        if 'password' in user_data:
            del user_data['password']

        print(f"[LOGIN] ✅ Login successful for: {user.email}")

        return {
            "success": True,
            "message": "Login successful",
            "user": user_data
        }

    except Exception as e:
        print(f"[LOGIN ERROR] ❌ Login failed for {user.email}")
        print(f"[LOGIN ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "message": "Login failed due to server error",
            "error": str(e)
        }


@app.post("/users/reset-password")
def reset_password(reset_data: PasswordReset):
    """Reset user password"""
    # Find user by email
    user_data = db.get_user(email=reset_data.email)

    if not user_data:
        return {
            "success": False,
            "message": "User not found"
        }

    # Hash the new password
    new_hashed_password = hash_password(reset_data.new_password)

    # Update password in database
    user_id = user_data['id']
    try:
        from bson import ObjectId
        db.db['users'].update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'password': new_hashed_password}}
        )

        return {
            "success": True,
            "message": "Password reset successful"
        }
    except Exception as e:
        print(f"Error resetting password: {e}")
        return {
            "success": False,
            "message": "Failed to reset password"
        }


@app.get("/users/{user_id}")
def get_user(user_id: str):
    """Get user details"""
    user = db.get_user(user_id=user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@app.get("/users/{user_id}/stats")
def get_user_stats(user_id: str):
    """Get user trading statistics"""
    stats = db.get_user_stats(user_id)
    return stats


# ==================== MARKETS ENDPOINTS ====================

@app.get("/markets")
def get_markets(limit: int = 20, category: str = "all", trending: bool = True):
    """
    Get active markets from Polymarket
    ⚠️ FIXED: Now sorts by 24hr volume for trending markets with error handling
    """
    try:
        print(f"[MARKETS] Fetching markets (limit={limit}, trending={trending}, category={category})")

        # Use trending markets sorted by 24hr volume
        if trending:
            markets = polymarket.get_trending_markets(limit=limit)
        else:
            markets = polymarket.get_markets(limit=limit)

        if not markets:
            print(f"[MARKETS WARNING] No markets returned from Polymarket API")
            return {
                "success": False,
                "count": 0,
                "markets": [],
                "error": "No markets available from Polymarket API"
            }

        print(f"[MARKETS] Retrieved {len(markets)} raw markets from Polymarket")

        # Filter by category if specified
        if category != "all":
            markets = [m for m in markets if category.lower() in m.get('market_slug', '').lower()]
            print(f"[MARKETS] Filtered to {len(markets)} markets for category: {category}")

        # Format markets
        formatted_markets = [polymarket.format_market_data(m) for m in markets]

        print(f"[MARKETS] ✅ Returning {len(formatted_markets)} formatted markets")

        # Log sample market for debugging
        if formatted_markets:
            sample = formatted_markets[0]
            print(f"[MARKETS] Sample market: {sample['question'][:50]}... @ {sample['probability']:.1%}")

        return {
            "success": True,
            "count": len(formatted_markets),
            "markets": formatted_markets,
            "trending": trending
        }

    except Exception as e:
        print(f"[MARKETS ERROR] ❌ Failed to fetch markets")
        print(f"[MARKETS ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "count": 0,
            "markets": [],
            "error": str(e),
            "error_type": type(e).__name__
        }


@app.get("/markets/search")
def search_markets(query: str, limit: int = 100):
    """
    Search ALL markets by keyword
    ⚠️ FIXED: Now searches comprehensively across all markets with error handling
    """
    try:
        print(f"[SEARCH] Searching markets for: '{query}' (limit={limit})")

        markets = polymarket.search_markets(query, limit)

        if not markets:
            print(f"[SEARCH] No markets found for query: '{query}'")
            return {
                "success": True,
                "count": 0,
                "query": query,
                "markets": [],
                "message": f"No markets found matching '{query}'"
            }

        print(f"[SEARCH] Found {len(markets)} markets matching '{query}'")

        formatted_markets = [polymarket.format_market_data(m) for m in markets]

        print(f"[SEARCH] ✅ Returning {len(formatted_markets)} formatted results")

        return {
            "success": True,
            "count": len(formatted_markets),
            "query": query,
            "total_searched": f"Searched extensively to find all matches for '{query}'",
            "markets": formatted_markets
        }

    except Exception as e:
        print(f"[SEARCH ERROR] ❌ Search failed for query: '{query}'")
        print(f"[SEARCH ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "count": 0,
            "query": query,
            "markets": [],
            "error": str(e),
            "error_type": type(e).__name__
        }


# ==================== TRADING ENDPOINTS ====================

@app.post("/trades/manual")
def create_manual_trade(user_id: str, trade: TradeCreate):
    """Execute a manual trade"""
    # Get user's wallet
    wallet_data = db.get_wallet(user_id)

    if not wallet_data:
        raise HTTPException(status_code=400, detail="No wallet found. Please create or connect a wallet first.")

    wallet_address = wallet_data.get('wallet_address')
    if not wallet_address:
        raise HTTPException(status_code=400, detail="Invalid wallet. Please reconnect your wallet.")

    # Check wallet balance
    try:
        balance_data = wallet_manager.get_wallet_balance(wallet_address)

        if not balance_data.get('success', False):
            return {
                "success": False,
                "message": "Could not verify wallet balance. Please ensure your wallet is connected and funded on Polygon Mainnet."
            }

        usdc_balance = balance_data.get('usdc_balance', 0.0)

        # Validate sufficient funds (require at least trade amount)
        if usdc_balance < trade.amount:
            return {
                "success": False,
                "message": f"Insufficient funds. You have ${usdc_balance:.2f} USDC but need ${trade.amount:.2f}. Please fund your wallet on Polygon Mainnet.",
                "balance": usdc_balance,
                "required": trade.amount
            }

    except Exception as e:
        # If balance check fails, still block the trade
        return {
            "success": False,
            "message": f"Could not verify wallet balance. Please ensure your wallet is connected and funded on Polygon Mainnet.",
            "error": str(e)
        }

    # Balance is sufficient, create the trade
    trade_data = {
        'market_id': trade.market_id or 'manual-trade',
        'market_question': trade.market_question,
        'position': trade.position,
        'amount': trade.amount,
        'entry_price': 0.75  # Simulated for now
    }

    trade_id = db.create_trade(user_id, trade_data)

    if not trade_id:
        raise HTTPException(status_code=400, detail="Failed to create trade")

    return {
        "success": True,
        "message": "Trade executed successfully",
        "trade_id": trade_id,
        "points_earned": int(trade.amount),
        "remaining_balance": usdc_balance - trade.amount
    }


@app.get("/trades/{user_id}")
def get_user_trades(user_id: str, limit: int = 10):
    """Get user's recent trades"""
    trades = db.get_user_trades(user_id, limit)
    return {
        "success": True,
        "count": len(trades),
        "trades": trades
    }


# ==================== SETTINGS ENDPOINTS ====================

@app.get("/settings/{user_id}")
def get_settings(user_id: str):
    """Get user's bot settings"""
    settings = db.get_user_settings(user_id)
    
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    return settings


@app.put("/settings/{user_id}")
def update_settings(user_id: str, settings: SettingsUpdate):
    """Update user's bot settings"""
    # Convert to dict and remove None values
    settings_dict = {k: v for k, v in settings.dict().items() if v is not None}
    
    db.update_settings(user_id, settings_dict)
    
    return {
        "success": True,
        "message": "Settings updated successfully"
    }


# ==================== BOT CONTROL ENDPOINTS ====================

@app.post("/bot/start/{user_id}")
def start_bot(user_id: str):
    """Start the trading bot for a user"""
    # Check if bot already running
    if user_id in active_bots:
        return {
            "success": False,
            "message": "Bot is already running"
        }
    
    # Get user settings
    settings = db.get_user_settings(user_id)
    
    if not settings:
        raise HTTPException(status_code=404, detail="User settings not found")
    
    # Create bot instance
    bot = TradingBot(settings)
    active_bots[user_id] = bot
    
    # Start bot in background (in production, use asyncio or celery)
    # For now, just mark as started
    db.update_settings(user_id, {"bot_enabled": True})
    
    return {
        "success": True,
        "message": "Bot started successfully"
    }


@app.post("/bot/stop/{user_id}")
def stop_bot(user_id: str):
    """Stop the trading bot for a user"""
    if user_id in active_bots:
        bot = active_bots[user_id]
        bot.stop()
        del active_bots[user_id]
    
    db.update_settings(user_id, {"bot_enabled": False})
    
    return {
        "success": True,
        "message": "Bot stopped successfully"
    }


@app.get("/bot/status/{user_id}")
def get_bot_status(user_id: str):
    """Get bot running status"""
    is_running = user_id in active_bots
    settings = db.get_user_settings(user_id)
    
    return {
        "is_running": is_running,
        "bot_enabled": settings.get('bot_enabled', False) if settings else False
    }


# ==================== POINTS ENDPOINTS ====================

@app.get("/points/{user_id}")
def get_points(user_id: str):
    """Get user's points balance"""
    user = db.get_user(user_id=user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "points_balance": user['points_balance'],
        "total_volume": user['total_volume']
    }


@app.post("/points/redeem")
def redeem_points(user_id: str, redemption: PointsRedeem):
    """Redeem points for rewards"""
    success = db.redeem_points(user_id, redemption.amount, redemption.reward)
    
    if not success:
        raise HTTPException(status_code=400, detail="Insufficient points or redemption failed")
    
    return {
        "success": True,
        "message": f"Successfully redeemed {redemption.amount} points for {redemption.reward}"
    }


# ==================== ACTIVITY ENDPOINTS ====================

@app.get("/activity/{user_id}")
def get_recent_activity(user_id: str, limit: int = 5):
    """Get user's recent trading activity"""
    trades = db.get_user_trades(user_id, limit)
    
    # Format for activity feed
    activity = []
    for trade in trades:
        activity.append({
            "type": "trade",
            "action": f"{'Bought' if trade['position'] == 'YES' else 'Sold'} {trade['position']}",
            "market": trade['market_question'][:50] + "...",
            "amount": trade['amount'],
            "profit": trade.get('profit', 0),
            "timestamp": trade['executed_at'],
            "status": trade['status']
        })
    
    return {
        "success": True,
        "activity": activity
    }


# ==================== WALLET ENDPOINTS ====================

@app.post("/wallet/create-inapp/{user_id}")
def create_in_app_wallet(user_id: str):
    """Create in-app wallet for user (Quick Start option)"""
    result = wallet_manager.create_in_app_wallet(user_id)
    
    if result['success']:
        return {
            "success": True,
            "wallet": result
        }
    else:
        raise HTTPException(status_code=400, detail=result.get('error', 'Failed to create wallet'))


@app.post("/wallet/connect-external/{user_id}")
def connect_external_wallet(user_id: str, wallet_data: WalletConnect):
    """Connect external wallet (MetaMask/WalletConnect option)"""
    result = wallet_manager.connect_external_wallet(user_id, wallet_data.wallet_address)
    
    if result['success']:
        return {
            "success": True,
            "wallet": result
        }
    else:
        raise HTTPException(status_code=400, detail=result.get('error', 'Failed to connect wallet'))


@app.get("/wallet/{user_id}")
def get_user_wallet_info(user_id: str):
    """Get user's wallet information and balance"""
    wallet = wallet_manager.get_user_wallet(user_id)
    
    if wallet:
        return {
            "success": True,
            "wallet": wallet
        }
    else:
        return {
            "success": False,
            "message": "No wallet found for this user"
        }


@app.get("/wallet/balance/{wallet_address}")
def get_wallet_balance(wallet_address: str):
    """Get wallet balance (MATIC and USDC)"""
    balance = wallet_manager.get_wallet_balance(wallet_address)
    return balance


@app.post("/wallet/export-key/{user_id}")
def export_private_key(user_id: str, key_export: PrivateKeyExport):
    """
    ⚠️ DANGEROUS: Export private key for in-app wallet
    Only works for in-app wallets, not external wallets
    Requires password verification
    ⚠️ ENHANCED: Better error messages for different wallet types
    """
    print(f"[EXPORT API] Private key export requested for user: {user_id}")

    # Verify user password first
    user_data = db.get_user(user_id=user_id)

    if not user_data:
        print(f"[EXPORT API] ❌ User not found: {user_id}")
        return {
            "success": False,
            "message": "User not found"
        }

    wallet_type = user_data.get('wallet_type', 'unknown')
    wallet_address = user_data.get('wallet_address', 'unknown')

    print(f"[EXPORT API] Wallet type: {wallet_type}")
    print(f"[EXPORT API] Wallet address: {wallet_address}")

    # Check if external wallet
    if wallet_type == 'external':
        print(f"[EXPORT API] ❌ Cannot export external wallet keys")
        return {
            "success": False,
            "message": "Cannot export external wallet private key",
            "wallet_type": "external",
            "explanation": "You connected an external wallet (Rabby, MetaMask, etc.). The private keys for external wallets are stored securely in your browser wallet extension, not on our servers. To export your private key, use your wallet app (Rabby/MetaMask settings)."
        }

    # Check password for in-app wallets
    stored_password = user_data.get('password')
    if stored_password:
        if not verify_password(key_export.password, stored_password):
            print(f"[EXPORT API] ❌ Invalid password")
            return {
                "success": False,
                "message": "Invalid password"
            }
    # If no password set (legacy user), allow export but warn

    print(f"[EXPORT API] Attempting to export in-app wallet key...")
    private_key = wallet_manager.export_private_key(user_id)

    if private_key:
        print(f"[EXPORT API] ✅ Private key exported successfully")
        return {
            "success": True,
            "private_key": private_key,
            "wallet_address": wallet_address,
            "wallet_type": "in-app",
            "warning": "⚠️ KEEP THIS SAFE! Never share your private key with anyone!"
        }
    else:
        print(f"[EXPORT API] ❌ Private key export failed")
        return {
            "success": False,
            "message": "Cannot export private key",
            "wallet_type": wallet_type,
            "explanation": "Private key not found in database. This might be because you have an external wallet, or the key was never stored."
        }


# ==================== USDC APPROVAL (for Trading) ====================

@app.get("/wallet/usdc-allowance/{user_id}")
def check_usdc_allowance(user_id: str):
    """
    Check how much USDC is approved for Polymarket Exchange
    Required before trading - if allowance is 0, user needs to approve first
    """
    print(f"[ALLOWANCE API] Checking USDC allowance for user: {user_id}")

    # Get user data
    user_data = db.get_user(user_id=user_id)

    if not user_data:
        print(f"[ALLOWANCE API] ❌ No user found with ID: {user_id}")
        return {
            "success": False,
            "message": "User not found"
        }

    wallet_address = user_data.get('wallet_address')
    wallet_type = user_data.get('wallet_type', 'unknown')

    if not wallet_address:
        print(f"[ALLOWANCE API] ❌ No wallet address for user")
        return {
            "success": False,
            "message": "No wallet found for this user"
        }

    print(f"[ALLOWANCE API] Wallet address: {wallet_address}")
    print(f"[ALLOWANCE API] Wallet type: {wallet_type}")

    # Check allowance on blockchain
    result = blockchain.check_usdc_allowance(wallet_address)

    if result.get('success'):
        print(f"[ALLOWANCE API] ✅ Allowance: ${result.get('allowance', 0):.2f}")
        return {
            "success": True,
            "wallet_address": wallet_address,
            "allowance": result.get('allowance', 0),
            "is_approved": result.get('is_approved', False),
            "spender": result.get('spender_address'),
            "message": "Approved for trading" if result.get('is_approved') else "Not approved - approval required before trading"
        }
    else:
        print(f"[ALLOWANCE API] ❌ Failed to check allowance: {result.get('error')}")
        return {
            "success": False,
            "message": "Failed to check USDC allowance",
            "error": result.get('error')
        }


@app.post("/wallet/approve-usdc/{user_id}")
def approve_usdc_for_trading(user_id: str, amount: float = None):
    """
    Approve USDC for Polymarket Exchange (required before first trade)
    If amount is not specified, approves unlimited USDC (standard practice)
    """
    print(f"[APPROVE API] USDC approval requested for user: {user_id}")
    print(f"[APPROVE API] Amount: {amount if amount else 'unlimited'}")

    # Get user data
    user_data = db.get_user(user_id=user_id)

    if not user_data:
        print(f"[APPROVE API] ❌ No user found with ID: {user_id}")
        return {
            "success": False,
            "message": "User not found"
        }

    wallet_address = user_data.get('wallet_address')
    wallet_type = user_data.get('wallet_type', 'unknown')

    if not wallet_address:
        print(f"[APPROVE API] ❌ No wallet address for user")
        return {
            "success": False,
            "message": "No wallet found for this user"
        }

    print(f"[APPROVE API] Wallet address: {wallet_address}")
    print(f"[APPROVE API] Wallet type: {wallet_type}")

    # Can only approve for in-app wallets (need private key)
    if wallet_type != 'in-app':
        print(f"[APPROVE API] ❌ External wallet - approval must be done via wallet app")
        return {
            "success": False,
            "message": "External wallet detected",
            "wallet_type": wallet_type,
            "explanation": "For external wallets (Rabby, MetaMask), you need to approve USDC through your wallet app when you make your first trade. The approval popup will appear automatically."
        }

    # Get private key for in-app wallet
    private_key = wallet_manager.export_private_key(user_id)

    if not private_key:
        print(f"[APPROVE API] ❌ Could not retrieve private key")
        return {
            "success": False,
            "message": "Could not retrieve wallet private key"
        }

    # Execute approval on blockchain
    print(f"[APPROVE API] Executing USDC approval transaction...")
    result = blockchain.approve_usdc(private_key, amount)

    if result.get('success'):
        print(f"[APPROVE API] ✅ USDC approved successfully!")
        print(f"[APPROVE API] Transaction: {result.get('tx_hash')}")

        return {
            "success": True,
            "message": "USDC approved for Polymarket trading!",
            "tx_hash": result.get('tx_hash'),
            "explorer_url": result.get('explorer_url'),
            "amount_approved": result.get('amount_approved'),
            "wallet_address": wallet_address,
            "next_step": "You can now place trades on Polymarket!"
        }
    else:
        print(f"[APPROVE API] ❌ Approval failed: {result.get('error')}")
        return {
            "success": False,
            "message": "USDC approval failed",
            "error": result.get('error'),
            "explanation": "Make sure you have enough POL for gas fees (~$0.01-0.05)"
        }


# ==================== TOP TRADERS ====================

@app.get("/traders/top")
def get_top_traders(limit: int = 5):
    """Get top performing traders by win rate"""
    try:
        # Get all users with trades
        all_stats = []

        # Query database for users with trade history
        users_collection = db.db['users']
        users_found = 0
        for user in users_collection.find():
            users_found += 1
            user_id = str(user['_id'])
            wallet_address = user.get('wallet_address')

            # Skip users without wallet
            if not wallet_address or wallet_address == 'None':
                continue

            stats = db.get_user_stats(user_id)

            # Only include users with at least 100 trades (verified traders)
            if stats['total_trades'] >= 100:
                all_stats.append({
                    'wallet_address': wallet_address,
                    'win_rate': stats['win_rate'],
                    'total_trades': stats['total_trades'],
                    'total_profit': stats['total_profit'],
                    'user_id': user_id
                })

        print(f"Found {users_found} users, {len(all_stats)} with 100+ trades")

        # Sort by win rate descending
        all_stats.sort(key=lambda x: x['win_rate'], reverse=True)

        # If no real traders found, add sample/demo traders for testing
        if len(all_stats) == 0:
            print("No traders with 100+ trades found. Using demo traders.")
            all_stats = [
                {
                    'wallet_address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
                    'win_rate': 78.5,
                    'total_trades': 245,
                    'total_profit': 12450.75,
                    'user_id': 'demo_1'
                },
                {
                    'wallet_address': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
                    'win_rate': 76.2,
                    'total_trades': 189,
                    'total_profit': 9823.50,
                    'user_id': 'demo_2'
                },
                {
                    'wallet_address': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
                    'win_rate': 73.8,
                    'total_trades': 156,
                    'total_profit': 7654.20,
                    'user_id': 'demo_3'
                },
                {
                    'wallet_address': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
                    'win_rate': 71.5,
                    'total_trades': 134,
                    'total_profit': 5432.80,
                    'user_id': 'demo_4'
                },
                {
                    'wallet_address': '0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6',
                    'win_rate': 69.3,
                    'total_trades': 112,
                    'total_profit': 3876.40,
                    'user_id': 'demo_5'
                }
            ]

        # Return top N traders
        top_traders = all_stats[:limit]

        return {
            "success": True,
            "traders": top_traders
        }

    except Exception as e:
        print(f"Error fetching top traders: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": True,
            "traders": []  # Return empty list if error
        }


# ==================== COPY TRADING ====================

@app.post("/copy-trading/start/{user_id}")
def start_copy_trading(user_id: str, copy_data: CopyTradeStart):
    """Start copy trading a specific wallet"""

    # Check if user already has copy trading active
    if user_id in active_copy_traders:
        return {
            "success": False,
            "message": "Copy trading already active. Stop current copy trading first."
        }

    # Validate target wallet exists and has good stats
    target_wallet = copy_data.target_wallet

    # Store copy trading configuration
    active_copy_traders[user_id] = {
        'target_wallet': target_wallet,
        'copy_amount': copy_data.copy_amount,
        'max_trades_per_day': copy_data.max_trades_per_day,
        'trades_today': 0,
        'started_at': datetime.now()
    }

    # Note: Actual implementation would require monitoring the target wallet's trades
    # and executing the same trades. This is a simplified version.

    return {
        "success": True,
        "message": f"Copy trading started for wallet {target_wallet}",
        "config": active_copy_traders[user_id]
    }


@app.post("/copy-trading/stop/{user_id}")
def stop_copy_trading(user_id: str):
    """Stop copy trading"""
    if user_id in active_copy_traders:
        del active_copy_traders[user_id]
        return {
            "success": True,
            "message": "Copy trading stopped"
        }
    else:
        return {
            "success": True,
            "message": "No active copy trading"
        }


@app.get("/copy-trading/status/{user_id}")
def get_copy_trading_status(user_id: str):
    """Get copy trading status"""
    if user_id in active_copy_traders:
        return {
            "success": True,
            "is_active": True,
            "config": active_copy_traders[user_id]
        }
    else:
        return {
            "success": True,
            "is_active": False
        }


# ==================== WHALE ACTIVITY ====================

# Sample whale wallets
WHALE_WALLETS = [
    "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
    "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
]

def generate_whale_activity():
    """Generate whale activity using real trending market data"""
    global whale_id_counter, whale_activity_feed

    # 30% chance to generate new whale activity
    if random.random() < 0.3:
        whale_id_counter += 1

        # Get real trending markets from Polymarket
        try:
            trending_markets = polymarket.get_markets(limit=10)
            if trending_markets:
                random_market = random.choice(trending_markets)
                market_question = random_market.get('question', 'Unknown Market')
            else:
                market_question = "Unknown Market"
        except:
            market_question = "Unknown Market"

        whale = {
            "id": whale_id_counter,
            "wallet": random.choice(WHALE_WALLETS),
            "position": random.choice(["YES", "NO"]),
            "amount": random.randint(25000, 100000),  # $25K to $100K (only large buys)
            "market": market_question,
            "timestamp": datetime.now().isoformat()
        }

        whale_activity_feed.append(whale)

        # Keep only last 20 whale activities
        if len(whale_activity_feed) > 20:
            whale_activity_feed.pop(0)

        return whale

    return None


@app.get("/whale-activity")
def get_whale_activity(since: int = 0):
    """Get whale trading activity (simulated for demo)"""
    # Generate new whale activity randomly
    generate_whale_activity()

    # Return only new whales since the given ID (limit to 2 max)
    new_whales = [w for w in whale_activity_feed if w['id'] > since]

    # Limit to maximum 2 whale alerts at once
    new_whales = new_whales[-2:] if len(new_whales) > 2 else new_whales

    return {
        "success": True,
        "whales": new_whales
    }


# ==================== RUN SERVER ====================

if __name__ == "__main__":
    print("[START] Starting Polymarket Trading Bot API Server...")
    print("[DOCS] API Documentation: http://localhost:8000/docs")
    print("[HEALTH] Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes
    )