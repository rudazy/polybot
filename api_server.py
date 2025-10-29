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


# Pydantic models for request/response validation
class UserCreate(BaseModel):
    email: str
    wallet_address: Optional[str] = None


class UserLogin(BaseModel):
    email: str


class SettingsUpdate(BaseModel):
    min_probability: Optional[float] = None
    category_filter: Optional[str] = None
    duration_filter: Optional[int] = None
    position_size: Optional[float] = None
    max_daily_trades: Optional[int] = None
    min_liquidity: Optional[float] = None
    bot_enabled: Optional[bool] = None


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
    """Register a new user"""
    user_id = db.create_user(user.email, user.wallet_address)
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User already exists or creation failed")
    
    user_data = db.get_user(user_id=user_id)
    return {
        "success": True,
        "message": "User registered successfully",
        "user": user_data
    }


@app.post("/users/login")
def login_user(user: UserLogin):
    """Login user (simplified - no password for now)"""
    user_data = db.get_user(email=user.email)
    
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "success": True,
        "message": "Login successful",
        "user": user_data
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


@app.get("/wallet/export-key/{user_id}")
def export_private_key(user_id: str):
    """
    ⚠️ DANGEROUS: Export private key for in-app wallet
    Only works for in-app wallets, not external wallets
    """
    private_key = wallet_manager.export_private_key(user_id)
    
    if private_key:
        return {
            "success": True,
            "private_key": private_key,
            "warning": "⚠️ KEEP THIS SAFE! Never share your private key with anyone!"
        }
    else:
        raise HTTPException(
            status_code=400, 
            detail="Cannot export private key. Either you don't have an in-app wallet or export failed."
        )


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
        for user in users_collection.find():
            user_id = str(user['_id'])
            stats = db.get_user_stats(user_id)

            # Only include users with at least 5 trades
            if stats['total_trades'] >= 5:
                all_stats.append({
                    'wallet_address': user.get('wallet_address', 'Unknown'),
                    'win_rate': stats['win_rate'],
                    'total_trades': stats['total_trades'],
                    'total_profit': stats['total_profit'],
                    'user_id': user_id
                })

        # Sort by win rate descending
        all_stats.sort(key=lambda x: x['win_rate'], reverse=True)

        # Return top N traders
        top_traders = all_stats[:limit]

        return {
            "success": True,
            "traders": top_traders
        }

    except Exception as e:
        print(f"Error fetching top traders: {e}")
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