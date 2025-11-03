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
        ⚠️ ENHANCED: Now includes detailed connection diagnostics

        Args:
            connection_string: MongoDB connection URI
        """
        if not connection_string:
            # Try to get from environment variable first
            connection_string = os.environ.get('MONGODB_URI')
            if not connection_string:
                # Fallback to default (for development)
                connection_string = "mongodb+srv://luda:1234luda@cluster0.byvm5pb.mongodb.net/?appName=Cluster0"

        print(f"[DB] Initializing MongoDB connection...")
        print(f"[DB] Connection string: {connection_string[:50]}...")

        try:
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=10000)
            self.db = self.client['polymarket_bot']

            print(f"[DB] Database: {self.db.name}")

            # Collections
            self.users = self.db['users']
            self.trades = self.db['trades']
            self.settings = self.db['settings']
            self.points = self.db['points']
            self.activity = self.db['activity_log']

            print(f"[DB] Testing connection...")
            # Test connection
            server_info = self.client.server_info()
            print(f"[DB] ✅ Connected to MongoDB Atlas!")
            print(f"[DB] MongoDB version: {server_info.get('version', 'unknown')}")

            # List existing collections for debugging
            existing_collections = self.db.list_collection_names()
            print(f"[DB] Existing collections: {existing_collections}")

            # Create indexes
            print(f"[DB] Creating indexes...")
            self.create_indexes()

            print(f"[DB] ✅ MongoDB initialization complete")

        except Exception as e:
            print(f"[DB ERROR] ❌ MongoDB connection failed!")
            print(f"[DB ERROR] Error type: {type(e).__name__}")
            print(f"[DB ERROR] Error message: {str(e)}")

            import traceback
            print(f"[DB ERROR] Stack trace:")
            traceback.print_exc()

            raise
    
    def create_indexes(self):
        """
        Create database indexes for performance
        ⚠️ ENHANCED: Better error handling for existing indexes
        """
        try:
            print(f"[DB] Creating index on users.email (unique)...")
            try:
                self.users.create_index("email", unique=True)
            except Exception as e:
                if "already exists" in str(e):
                    print(f"[DB] Index users.email already exists (OK)")
                else:
                    print(f"[DB WARNING] Could not create users.email index: {e}")

            print(f"[DB] Creating index on users.wallet_address (unique, sparse)...")
            try:
                self.users.create_index("wallet_address", unique=True, sparse=True)
            except Exception as e:
                if "already exists" in str(e):
                    print(f"[DB] Index users.wallet_address already exists (OK)")
                else:
                    print(f"[DB WARNING] Could not create users.wallet_address index: {e}")

            print(f"[DB] Creating index on trades.user_id...")
            try:
                self.trades.create_index("user_id")
            except Exception as e:
                print(f"[DB WARNING] Could not create trades.user_id index: {e}")

            print(f"[DB] Creating index on settings.user_id (unique)...")
            try:
                self.settings.create_index("user_id", unique=True)
            except Exception as e:
                if "already exists" in str(e):
                    print(f"[DB] Index settings.user_id already exists (OK)")
                else:
                    print(f"[DB WARNING] Could not create settings.user_id index: {e}")

            print(f"[DB] Creating index on points.user_id...")
            try:
                self.points.create_index("user_id")
            except Exception as e:
                print(f"[DB WARNING] Could not create points.user_id index: {e}")

            print("[DB] ✅ Database indexes created/verified!")

        except Exception as e:
            print(f"[DB WARNING] Index creation error: {e}")
            import traceback
            traceback.print_exc()
    
    # USER OPERATIONS
    
    def create_user(self, email: str, wallet_address: str = None) -> Optional[str]:
        """
        Create a new user
        ⚠️ ENHANCED: Now includes detailed error logging for debugging
        """
        try:
            print(f"[DB] Creating user: {email}")
            print(f"[DB] Wallet address: {wallet_address}")

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

            print(f"[DB] Inserting user document into database...")

            # Check if MongoDB client is connected
            if not self.client:
                print(f"[DB ERROR] MongoDB client is not initialized!")
                return None

            # Try to insert user
            result = self.users.insert_one(user_doc)
            user_id = str(result.inserted_id)

            print(f"[DB] ✅ User inserted with ID: {user_id}")
            print(f"[DB] Creating default settings for user...")

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

            print(f"[DB] ✅ User created successfully: {email} (ID: {user_id})")
            return user_id

        except Exception as e:
            print(f"[DB ERROR] ❌ Failed to create user: {email}")
            print(f"[DB ERROR] Error type: {type(e).__name__}")
            print(f"[DB ERROR] Error message: {str(e)}")
            print(f"[DB ERROR] Error details: {repr(e)}")

            # Print full stack trace
            import traceback
            print(f"[DB ERROR] Stack trace:")
            traceback.print_exc()

            # Check specific error types
            if "duplicate key" in str(e).lower():
                print(f"[DB ERROR] Duplicate email detected: {email}")
            elif "connection" in str(e).lower():
                print(f"[DB ERROR] MongoDB connection issue")

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
            print(f"[ERROR] Error getting user: {e}")
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
            
            print(f"[OK] Updated subscription for user {user_id}: {status}")

        except Exception as e:
            print(f"[ERROR] Error updating subscription: {e}")
    
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
            
            print(f"[OK] Trade created: ID {trade_id}")
            return trade_id

        except Exception as e:
            print(f"[ERROR] Error creating trade: {e}")
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
            print(f"[ERROR] Error getting trades: {e}")
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
            
            print(f"[OK] Trade {trade_id} closed. Profit: ${profit:.2f}")

        except Exception as e:
            print(f"[ERROR] Error closing trade: {e}")
    
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
            print(f"[ERROR] Error getting settings: {e}")
            return None
    
    def update_settings(self, user_id: str, settings_data: Dict):
        """Update user settings"""
        try:
            self.settings.update_one(
                {"user_id": user_id},
                {"$set": settings_data}
            )
            
            print(f"[OK] Settings updated for user {user_id}")

        except Exception as e:
            print(f"[ERROR] Error updating settings: {e}")
    
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
            print(f"[ERROR] Error adding points: {e}")
    
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
                
                print(f"[OK] User {user_id} redeemed {amount} points for {reward}")
                return True
            else:
                print(f"[ERROR] Insufficient points for user {user_id}")
                return False

        except Exception as e:
            print(f"[ERROR] Error redeeming points: {e}")
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
            print(f"[ERROR] Error getting stats: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("[OK] MongoDB connection closed")


def test_mongodb():
    """Test MongoDB operations"""
    print("[TEST] Testing MongoDB Database...\n")
    
    db = MongoDatabase()
    
    # Test 1: Create user
    print("Test 1: Creating user...")
    user_id = db.create_user("mongodb_test@example.com", "0x987654321")
    
    if user_id:
        print(f"[OK] User created with ID: {user_id}\n")
        
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
    print("[OK] MongoDB test complete!")


if __name__ == "__main__":
    test_mongodb()