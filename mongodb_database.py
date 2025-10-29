"""
MongoDB Database Management for Polymarket Trading Bot
Uses MongoDB Atlas cloud database
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os


class MongoDatabase:
    """
    MongoDB database manager for the trading bot
    """
    
    def __init__(self, connection_string: str = None):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection URI
        """
        if not connection_string:
            connection_string = "mongodb+srv://luda:1234luda@cluster0.byvm5pb.mongodb.net/?appName=Cluster0"
        
        try:
            self.client = MongoClient(connection_string)
            self.db = self.client['polymarket_bot']
            
            # Collections
            self.users = self.db['users']
            self.trades = self.db['trades']
            self.settings = self.db['settings']
            self.points = self.db['points']
            self.activity = self.db['activity_log']
            
            # Test connection
            self.client.server_info()
            print("✅ Connected to MongoDB Atlas!")
            
            # Create indexes
            self.create_indexes()
            
        except Exception as e:
            print(f"❌ MongoDB connection error: {e}")
            raise
    
    def create_indexes(self):
        """Create database indexes for performance"""
        try:
            self.users.create_index("email", unique=True)
            self.users.create_index("wallet_address", unique=True, sparse=True)
            self.trades.create_index("user_id")
            self.settings.create_index("user_id", unique=True)
            self.points.create_index("user_id")
            print("✅ Database indexes created!")
        except Exception as e:
            print(f"⚠️ Index creation warning: {e}")
    
    # USER OPERATIONS
    
    def create_user(self, email: str, wallet_address: str = None) -> Optional[str]:
        """Create a new user"""
        try:
            trial_start = datetime.now()
            trial_end = trial_start + timedelta(days=7)
            
            user_doc = {
                "email": email,
                "wallet_address": wallet_address,
                "subscription_status": "trial",
                "trial_start_date": trial_start,
                "trial_end_date": trial_end,
                "subscription_end_date": None,
                "points_balance": 0,
                "total_volume": 0.0,
                "created_at": datetime.now()
            }
            
            result = self.users.insert_one(user_doc)
            user_id = str(result.inserted_id)
            
            # Create default settings
            settings_doc = {
                "user_id": user_id,
                "min_probability": 0.7,
                "category_filter": "all",
                "duration_filter": 168,
                "position_size": 100.0,
                "max_daily_trades": 10,
                "min_liquidity": 10000.0,
                "bot_enabled": False,
                "notifications_enabled": True,
                "stop_loss": 10.0,  # Default 10% stop loss
                "take_profit": 20.0  # Default 20% take profit
            }
            self.settings.insert_one(settings_doc)
            
            print(f"✅ User created: {email} (ID: {user_id})")
            return user_id
            
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return None
    
    def get_user(self, user_id: str = None, email: str = None) -> Optional[Dict]:
        """Get user by ID or email"""
        try:
            if user_id:
                from bson.objectid import ObjectId
                user = self.users.find_one({"_id": ObjectId(user_id)})
            elif email:
                user = self.users.find_one({"email": email})
            else:
                return None
            
            if user:
                user['id'] = str(user['_id'])
                del user['_id']
            
            return user
            
        except Exception as e:
            print(f"❌ Error getting user: {e}")
            return None
    
    def update_user_subscription(self, user_id: str, status: str, end_date: datetime = None):
        """Update user subscription status"""
        try:
            from bson.objectid import ObjectId
            
            self.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "subscription_status": status,
                        "subscription_end_date": end_date
                    }
                }
            )
            
            print(f"✅ Updated subscription for user {user_id}: {status}")
            
        except Exception as e:
            print(f"❌ Error updating subscription: {e}")
    
    # TRADE OPERATIONS
    
    def create_trade(self, user_id: str, trade_data: Dict) -> Optional[str]:
        """Record a new trade"""
        try:
            trade_doc = {
                "user_id": user_id,
                "market_id": trade_data.get('market_id'),
                "market_question": trade_data.get('market_question'),
                "position": trade_data.get('position'),
                "amount": trade_data.get('amount'),
                "entry_price": trade_data.get('entry_price'),
                "exit_price": None,
                "profit": 0.0,
                "status": "open",
                "executed_at": datetime.now(),
                "closed_at": None
            }
            
            result = self.trades.insert_one(trade_doc)
            trade_id = str(result.inserted_id)
            
            # Award points (1 point per $1 volume)
            points = int(trade_data.get('amount', 0))
            self.add_points(
                user_id, 
                points, 
                'trade', 
                f"Trade on {trade_data.get('market_question', 'Unknown')[:30]}"
            )
            
            # Update total volume
            from bson.objectid import ObjectId
            self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$inc": {"total_volume": trade_data.get('amount', 0)}}
            )
            
            print(f"✅ Trade created: ID {trade_id}")
            return trade_id
            
        except Exception as e:
            print(f"❌ Error creating trade: {e}")
            return None
    
    def get_user_trades(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent trades for a user"""
        try:
            trades = list(self.trades.find(
                {"user_id": user_id}
            ).sort("executed_at", -1).limit(limit))
            
            for trade in trades:
                trade['id'] = str(trade['_id'])
                del trade['_id']
            
            return trades
            
        except Exception as e:
            print(f"❌ Error getting trades: {e}")
            return []
    
    def close_trade(self, trade_id: str, exit_price: float, profit: float):
        """Close a trade and record profit"""
        try:
            from bson.objectid import ObjectId
            
            self.trades.update_one(
                {"_id": ObjectId(trade_id)},
                {
                    "$set": {
                        "exit_price": exit_price,
                        "profit": profit,
                        "status": "closed",
                        "closed_at": datetime.now()
                    }
                }
            )
            
            print(f"✅ Trade {trade_id} closed. Profit: ${profit:.2f}")
            
        except Exception as e:
            print(f"❌ Error closing trade: {e}")
    
    # SETTINGS OPERATIONS
    
    def get_user_settings(self, user_id: str) -> Optional[Dict]:
        """Get user's trading settings"""
        try:
            settings = self.settings.find_one({"user_id": user_id})
            
            if settings:
                settings['id'] = str(settings['_id'])
                del settings['_id']
            
            return settings
            
        except Exception as e:
            print(f"❌ Error getting settings: {e}")
            return None
    
    def update_settings(self, user_id: str, settings_data: Dict):
        """Update user settings"""
        try:
            self.settings.update_one(
                {"user_id": user_id},
                {"$set": settings_data}
            )
            
            print(f"✅ Settings updated for user {user_id}")
            
        except Exception as e:
            print(f"❌ Error updating settings: {e}")
    
    # POINTS OPERATIONS
    
    def add_points(self, user_id: str, amount: int, source: str, description: str):
        """Add points to user account"""
        try:
            from bson.objectid import ObjectId
            
            # Record points transaction
            points_doc = {
                "user_id": user_id,
                "amount": amount,
                "source": source,
                "description": description,
                "created_at": datetime.now()
            }
            self.points.insert_one(points_doc)
            
            # Update user balance
            self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$inc": {"points_balance": amount}}
            )
            
        except Exception as e:
            print(f"❌ Error adding points: {e}")
    
    def redeem_points(self, user_id: str, amount: int, reward: str) -> bool:
        """Redeem points for rewards"""
        try:
            from bson.objectid import ObjectId
            
            user = self.get_user(user_id=user_id)
            
            if user and user['points_balance'] >= amount:
                # Deduct points
                self.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$inc": {"points_balance": -amount}}
                )
                
                # Record redemption
                points_doc = {
                    "user_id": user_id,
                    "amount": -amount,
                    "source": "redemption",
                    "description": f"Redeemed: {reward}",
                    "created_at": datetime.now()
                }
                self.points.insert_one(points_doc)
                
                print(f"✅ User {user_id} redeemed {amount} points for {reward}")
                return True
            else:
                print(f"❌ Insufficient points for user {user_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error redeeming points: {e}")
            return False
    
    # STATISTICS
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get comprehensive user statistics"""
        try:
            stats = {}
            
            # Total trades
            stats['total_trades'] = self.trades.count_documents({"user_id": user_id})
            
            # Total profit
            pipeline = [
                {"$match": {"user_id": user_id, "status": "closed"}},
                {"$group": {"_id": None, "total_profit": {"$sum": "$profit"}}}
            ]
            result = list(self.trades.aggregate(pipeline))
            stats['total_profit'] = result[0]['total_profit'] if result else 0.0
            
            # Win rate
            wins = self.trades.count_documents({"user_id": user_id, "profit": {"$gt": 0}})
            stats['win_rate'] = (wins / max(stats['total_trades'], 1)) * 100
            
            # Active positions
            stats['active_positions'] = self.trades.count_documents({"user_id": user_id, "status": "open"})
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("✅ MongoDB connection closed")


def test_mongodb():
    """Test MongoDB operations"""
    print("🧪 Testing MongoDB Database...\n")
    
    db = MongoDatabase()
    
    # Test 1: Create user
    print("Test 1: Creating user...")
    user_id = db.create_user("mongodb_test@example.com", "0x987654321")
    
    if user_id:
        print(f"✅ User created with ID: {user_id}\n")
        
        # Test 2: Get user
        print("Test 2: Retrieving user...")
        user = db.get_user(user_id=user_id)
        print(f"User: {user['email']}")
        print(f"Trial ends: {user['trial_end_date']}\n")
        
        # Test 3: Create trade
        print("Test 3: Creating trade...")
        trade_data = {
            'market_id': 'mongo-test-123',
            'market_question': 'Will Ethereum reach $5000?',
            'position': 'YES',
            'amount': 250.0,
            'entry_price': 0.80
        }
        trade_id = db.create_trade(user_id, trade_data)
        
        # Test 4: Get stats
        print("\nTest 4: Getting user stats...")
        stats = db.get_user_stats(user_id)
        print(f"Total trades: {stats['total_trades']}")
        print(f"Total profit: ${stats['total_profit']:.2f}")
        print(f"Win rate: {stats['win_rate']:.1f}%\n")
        
        # Test 5: Check points
        user = db.get_user(user_id=user_id)
        print(f"Points balance: {user['points_balance']} points")
        print(f"Total volume: ${user['total_volume']}\n")
    
    db.close()
    print("✅ MongoDB test complete!")


if __name__ == "__main__":
    test_mongodb()