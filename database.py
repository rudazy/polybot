"""
Database Management for Polymarket Trading Bot
Handles users, trades, settings, and points tracking
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class Database:
    """
    SQLite database manager for the trading bot
    """
    
    def __init__(self, db_path: str = "polymarket_bot.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Connect to the database"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            print(f"✅ Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"❌ Database connection error: {e}")
    
    def create_tables(self):
        """Create all necessary tables"""
        try:
            # Users table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    wallet_address TEXT UNIQUE,
                    subscription_status TEXT DEFAULT 'trial',
                    trial_start_date TEXT,
                    trial_end_date TEXT,
                    subscription_end_date TEXT,
                    points_balance INTEGER DEFAULT 0,
                    total_volume REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Trades table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    market_id TEXT,
                    market_question TEXT,
                    position TEXT,
                    amount REAL,
                    entry_price REAL,
                    exit_price REAL,
                    profit REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'open',
                    executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    closed_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Settings table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    min_probability REAL DEFAULT 0.7,
                    category_filter TEXT DEFAULT 'all',
                    duration_filter INTEGER DEFAULT 168,
                    position_size REAL DEFAULT 100.0,
                    max_daily_trades INTEGER DEFAULT 10,
                    min_liquidity REAL DEFAULT 10000.0,
                    bot_enabled INTEGER DEFAULT 0,
                    notifications_enabled INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Points table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount INTEGER,
                    source TEXT,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Activity log table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action_type TEXT,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            self.conn.commit()
            print("✅ All database tables created successfully!")
            
        except sqlite3.Error as e:
            print(f"❌ Error creating tables: {e}")
    
    # USER OPERATIONS
    
    def create_user(self, email: str, wallet_address: str = None) -> Optional[int]:
        """Create a new user"""
        try:
            trial_start = datetime.now().isoformat()
            trial_end = (datetime.now() + timedelta(days=7)).isoformat()
            
            self.cursor.execute("""
                INSERT INTO users (email, wallet_address, trial_start_date, trial_end_date)
                VALUES (?, ?, ?, ?)
            """, (email, wallet_address, trial_start, trial_end))
            
            user_id = self.cursor.lastrowid
            
            # Create default settings for user
            self.cursor.execute("""
                INSERT INTO settings (user_id) VALUES (?)
            """, (user_id,))
            
            self.conn.commit()
            print(f"✅ User created: {email} (ID: {user_id})")
            return user_id
            
        except sqlite3.IntegrityError:
            print(f"❌ User already exists: {email}")
            return None
        except sqlite3.Error as e:
            print(f"❌ Error creating user: {e}")
            return None
    
    def get_user(self, user_id: int = None, email: str = None) -> Optional[Dict]:
        """Get user by ID or email"""
        try:
            if user_id:
                self.cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            elif email:
                self.cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            else:
                return None
            
            row = self.cursor.fetchone()
            return dict(row) if row else None
            
        except sqlite3.Error as e:
            print(f"❌ Error getting user: {e}")
            return None
    
    def update_user_subscription(self, user_id: int, status: str, end_date: str = None):
        """Update user subscription status"""
        try:
            self.cursor.execute("""
                UPDATE users 
                SET subscription_status = ?, subscription_end_date = ?
                WHERE id = ?
            """, (status, end_date, user_id))
            
            self.conn.commit()
            print(f"✅ Updated subscription for user {user_id}: {status}")
            
        except sqlite3.Error as e:
            print(f"❌ Error updating subscription: {e}")
    
    # TRADE OPERATIONS
    
    def create_trade(self, user_id: int, trade_data: Dict) -> Optional[int]:
        """Record a new trade"""
        try:
            self.cursor.execute("""
                INSERT INTO trades (
                    user_id, market_id, market_question, position, 
                    amount, entry_price, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                trade_data.get('market_id'),
                trade_data.get('market_question'),
                trade_data.get('position'),
                trade_data.get('amount'),
                trade_data.get('entry_price'),
                'open'
            ))
            
            trade_id = self.cursor.lastrowid
            
            # Award points (1 point per $1 volume)
            points = int(trade_data.get('amount', 0))
            self.add_points(user_id, points, 'trade', f"Trade on {trade_data.get('market_question', 'Unknown')[:30]}")
            
            # Update total volume
            self.cursor.execute("""
                UPDATE users 
                SET total_volume = total_volume + ?
                WHERE id = ?
            """, (trade_data.get('amount'), user_id))
            
            self.conn.commit()
            print(f"✅ Trade created: ID {trade_id}")
            return trade_id
            
        except sqlite3.Error as e:
            print(f"❌ Error creating trade: {e}")
            return None
    
    def get_user_trades(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get recent trades for a user"""
        try:
            self.cursor.execute("""
                SELECT * FROM trades 
                WHERE user_id = ? 
                ORDER BY executed_at DESC 
                LIMIT ?
            """, (user_id, limit))
            
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            print(f"❌ Error getting trades: {e}")
            return []
    
    def close_trade(self, trade_id: int, exit_price: float, profit: float):
        """Close a trade and record profit"""
        try:
            self.cursor.execute("""
                UPDATE trades 
                SET exit_price = ?, profit = ?, status = 'closed', closed_at = ?
                WHERE id = ?
            """, (exit_price, profit, datetime.now().isoformat(), trade_id))
            
            self.conn.commit()
            print(f"✅ Trade {trade_id} closed. Profit: ${profit:.2f}")
            
        except sqlite3.Error as e:
            print(f"❌ Error closing trade: {e}")
    
    # SETTINGS OPERATIONS
    
    def get_user_settings(self, user_id: int) -> Optional[Dict]:
        """Get user's trading settings"""
        try:
            self.cursor.execute("SELECT * FROM settings WHERE user_id = ?", (user_id,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
            
        except sqlite3.Error as e:
            print(f"❌ Error getting settings: {e}")
            return None
    
    def update_settings(self, user_id: int, settings: Dict):
        """Update user settings"""
        try:
            updates = []
            values = []
            
            for key, value in settings.items():
                updates.append(f"{key} = ?")
                values.append(value)
            
            values.append(user_id)
            
            query = f"UPDATE settings SET {', '.join(updates)} WHERE user_id = ?"
            self.cursor.execute(query, values)
            
            self.conn.commit()
            print(f"✅ Settings updated for user {user_id}")
            
        except sqlite3.Error as e:
            print(f"❌ Error updating settings: {e}")
    
    # POINTS OPERATIONS
    
    def add_points(self, user_id: int, amount: int, source: str, description: str):
        """Add points to user account"""
        try:
            self.cursor.execute("""
                INSERT INTO points (user_id, amount, source, description)
                VALUES (?, ?, ?, ?)
            """, (user_id, amount, source, description))
            
            self.cursor.execute("""
                UPDATE users 
                SET points_balance = points_balance + ?
                WHERE id = ?
            """, (amount, user_id))
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            print(f"❌ Error adding points: {e}")
    
    def redeem_points(self, user_id: int, amount: int, reward: str) -> bool:
        """Redeem points for rewards"""
        try:
            user = self.get_user(user_id=user_id)
            
            if user and user['points_balance'] >= amount:
                self.cursor.execute("""
                    UPDATE users 
                    SET points_balance = points_balance - ?
                    WHERE id = ?
                """, (amount, user_id))
                
                self.cursor.execute("""
                    INSERT INTO points (user_id, amount, source, description)
                    VALUES (?, ?, ?, ?)
                """, (user_id, -amount, 'redemption', f"Redeemed: {reward}"))
                
                self.conn.commit()
                print(f"✅ User {user_id} redeemed {amount} points for {reward}")
                return True
            else:
                print(f"❌ Insufficient points for user {user_id}")
                return False
                
        except sqlite3.Error as e:
            print(f"❌ Error redeeming points: {e}")
            return False
    
    # STATISTICS
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get comprehensive user statistics"""
        try:
            stats = {}
            
            # Total trades
            self.cursor.execute("SELECT COUNT(*) as total FROM trades WHERE user_id = ?", (user_id,))
            stats['total_trades'] = self.cursor.fetchone()['total']
            
            # Total profit
            self.cursor.execute("SELECT SUM(profit) as total_profit FROM trades WHERE user_id = ? AND status = 'closed'", (user_id,))
            result = self.cursor.fetchone()
            stats['total_profit'] = result['total_profit'] or 0.0
            
            # Win rate
            self.cursor.execute("SELECT COUNT(*) as wins FROM trades WHERE user_id = ? AND profit > 0", (user_id,))
            wins = self.cursor.fetchone()['wins']
            stats['win_rate'] = (wins / max(stats['total_trades'], 1)) * 100
            
            # Active positions
            self.cursor.execute("SELECT COUNT(*) as active FROM trades WHERE user_id = ? AND status = 'open'", (user_id,))
            stats['active_positions'] = self.cursor.fetchone()['active']
            
            return stats
            
        except sqlite3.Error as e:
            print(f"❌ Error getting stats: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✅ Database connection closed")


def test_database():
    """Test database operations"""
    print("🧪 Testing Database...\n")
    
    db = Database("test_bot.db")
    
    # Test 1: Create user
    print("Test 1: Creating user...")
    user_id = db.create_user("test@example.com", "0x123456789")
    
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
            'market_id': 'test-123',
            'market_question': 'Will Bitcoin hit $100k?',
            'position': 'YES',
            'amount': 100.0,
            'entry_price': 0.75
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
    print("✅ Database test complete!")


if __name__ == "__main__":
    test_database()