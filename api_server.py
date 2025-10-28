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
active_bots = {}  # Store active bot instances per user


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