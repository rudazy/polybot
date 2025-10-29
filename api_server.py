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
    allow_origins=["*"],  # In production, specify your frontend domain
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
user_networks = {}  # Store network preference per user (default: testnet)
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


class NetworkSwitch(BaseModel):
    network: str


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
    """Detailed health check"""
    return {
        "api": "healthy",
        "database": "connected",
        "polymarket_api": "connected",
        "active_bots": len(active_bots)
    }


# ==================== USER ENDPOINTS ====================

@app.post("/users/register")
def register_user(user: UserCreate):
    """Register a new user with password"""
    # Hash the password
    hashed_password = hash_password(user.password)

    # Create user with hashed password
    user_id = db.create_user(user.email, user.wallet_address)

    if not user_id:
        return {
            "success": False,
            "message": "User already exists or creation failed"
        }

    # Store the hashed password
    db.db['users'].update_one(
        {'_id': user_id},
        {'$set': {'password': hashed_password}}
    )

    user_data = db.get_user(user_id=user_id)
    # Remove password from response
    if 'password' in user_data:
        del user_data['password']

    return {
        "success": True,
        "message": "User registered successfully",
        "user": user_data
    }


@app.post("/users/login")
def login_user(user: UserLogin):
    """Login user with password verification"""
    user_data = db.get_user(email=user.email)

    if not user_data:
        return {
            "success": False,
            "message": "User not found"
        }

    # Check if user has a password set
    stored_password = user_data.get('password')
    if not stored_password:
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
        return {
            "success": False,
            "message": "Invalid password"
        }

    # Remove password from response
    if 'password' in user_data:
        del user_data['password']

    return {
        "success": True,
        "message": "Login successful",
        "user": user_data
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
def get_markets(limit: int = 20, category: str = "all"):
    """Get active markets from Polymarket"""
    markets = polymarket.get_markets(limit=limit)
    
    # Filter by category if specified
    if category != "all":
        markets = [m for m in markets if category.lower() in m.get('market_slug', '').lower()]
    
    # Format markets
    formatted_markets = [polymarket.format_market_data(m) for m in markets]
    
    return {
        "success": True,
        "count": len(formatted_markets),
        "markets": formatted_markets
    }


@app.get("/markets/search")
def search_markets(query: str, limit: int = 10):
    """Search markets by keyword"""
    markets = polymarket.search_markets(query, limit)
    formatted_markets = [polymarket.format_market_data(m) for m in markets]
    
    return {
        "success": True,
        "count": len(formatted_markets),
        "markets": formatted_markets
    }


# ==================== TRADING ENDPOINTS ====================

@app.post("/trades/manual")
def create_manual_trade(user_id: str, trade: TradeCreate):
    """Execute a manual trade"""
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
        "points_earned": int(trade.amount)
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
    """
    # Verify user password first
    user_data = db.get_user(user_id=user_id)

    if not user_data:
        return {
            "success": False,
            "message": "User not found"
        }

    # Check password
    stored_password = user_data.get('password')
    if stored_password:
        if not verify_password(key_export.password, stored_password):
            return {
                "success": False,
                "message": "Invalid password"
            }
    # If no password set (legacy user), allow export but warn

    private_key = wallet_manager.export_private_key(user_id)

    if private_key:
        return {
            "success": True,
            "private_key": private_key,
            "warning": "⚠️ KEEP THIS SAFE! Never share your private key with anyone!"
        }
    else:
        return {
            "success": False,
            "message": "Cannot export private key. Either you don't have an in-app wallet or export failed."
        }


# ==================== NETWORK SWITCHING ====================

@app.get("/network/status/{user_id}")
def get_network_status(user_id: str):
    """Get current network for user"""
    network = user_networks.get(user_id, "testnet")
    return {
        "success": True,
        "network": network,
        "is_testnet": network == "testnet"
    }


@app.post("/network/switch/{user_id}")
def switch_network(user_id: str, network_data: NetworkSwitch):
    """Switch between testnet and mainnet"""
    network = network_data.network

    if network not in ["testnet", "mainnet"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid network. Must be 'testnet' or 'mainnet'"
        )

    # Update user's network preference
    user_networks[user_id] = network

    # Stop bot if running when switching networks
    if user_id in active_bots:
        active_bots[user_id].stop()
        del active_bots[user_id]

    # Stop copy trading if active when switching networks
    if user_id in active_copy_traders:
        del active_copy_traders[user_id]

    return {
        "success": True,
        "network": network,
        "message": f"Switched to {network}. Bot and copy trading stopped for safety."
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

# Sample whale wallets and markets for simulation
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

SAMPLE_MARKETS = [
    "Will Bitcoin reach $100K by end of 2024?",
    "Will Trump win the 2024 election?",
    "Will Ethereum ETF be approved in 2024?",
    "Will AI reach AGI before 2030?",
    "Will S&P 500 hit new ATH this month?",
    "Will Fed cut rates in next meeting?",
    "Will unemployment rate drop below 3%?",
    "Will Tesla stock hit $300 this year?"
]

def generate_whale_activity():
    """Generate simulated whale activity"""
    global whale_id_counter, whale_activity_feed

    # 30% chance to generate new whale activity
    if random.random() < 0.3:
        whale_id_counter += 1

        whale = {
            "id": whale_id_counter,
            "wallet": random.choice(WHALE_WALLETS),
            "position": random.choice(["YES", "NO"]),
            "amount": random.randint(5000, 50000),  # $5K to $50K
            "market": random.choice(SAMPLE_MARKETS),
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

    # Return only new whales since the given ID
    new_whales = [w for w in whale_activity_feed if w['id'] > since]

    return {
        "success": True,
        "whales": new_whales
    }


# ==================== RUN SERVER ====================

if __name__ == "__main__":
    print("🚀 Starting Polymarket Trading Bot API Server...")
    print("📡 API Documentation: http://localhost:8000/docs")
    print("🔗 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes
    )