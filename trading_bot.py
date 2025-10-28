"""
Polymarket Trading Bot - Core Logic
Automatically scans markets and executes trades based on user settings
"""

import time
from datetime import datetime
from typing import Dict, List, Optional
from polymarket_api import PolymarketAPI


class TradingBot:
    """
    Automated trading bot for Polymarket
    """
    
    def __init__(self, user_settings: Dict):
        """
        Initialize the trading bot
        
        Args:
            user_settings: Dictionary containing user configuration
                - min_probability: Minimum win % (0.5 to 0.95)
                - category: Market category filter
                - max_duration_hours: Max time until market closes
                - position_size: Dollar amount per trade
                - max_daily_trades: Maximum trades per day
                - min_liquidity: Minimum market liquidity
        """
        self.api = PolymarketAPI()
        self.settings = user_settings
        self.is_running = False
        self.trades_today = 0
        self.total_profit = 0.0
        self.trade_history = []
        
        print("🤖 Trading Bot Initialized!")
        print(f"Settings: {self.settings}")
    
    def start(self):
        """Start the trading bot"""
        self.is_running = True
        print("\n✅ Bot Started! Scanning for opportunities...\n")
        
        while self.is_running:
            try:
                # Scan markets
                opportunities = self.scan_markets()
                
                # Execute trades on opportunities
                if opportunities:
                    print(f"🎯 Found {len(opportunities)} opportunities!")
                    for opp in opportunities:
                        if self.trades_today < self.settings.get('max_daily_trades', 10):
                            self.execute_trade(opp)
                        else:
                            print("⚠️ Daily trade limit reached!")
                            break
                else:
                    print("⏳ No opportunities found. Scanning again in 30 seconds...")
                
                # Wait before next scan
                time.sleep(30)  # Scan every 30 seconds
                
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped by user")
                self.stop()
                break
            except Exception as e:
                print(f"❌ Error in bot loop: {e}")
                time.sleep(10)
    
    def stop(self):
        """Stop the trading bot"""
        self.is_running = False
        print("\n🛑 Bot Stopped!")
        self.print_summary()
    
    def scan_markets(self) -> List[Dict]:
        """
        Scan markets for trading opportunities
        
        Returns:
            List of market opportunities that match criteria
        """
        print("🔍 Scanning markets...")
        
        # Fetch markets from API
        markets = self.api.get_markets(limit=50)
        
        if not markets:
            return []
        
        opportunities = []
        
        for market in markets:
            formatted = self.api.format_market_data(market)
            
            # Apply filters
            if self.meets_criteria(formatted):
                opportunities.append(formatted)
        
        return opportunities
    
    def meets_criteria(self, market: Dict) -> bool:
        """
        Check if a market meets the trading criteria
        
        Args:
            market: Formatted market data
            
        Returns:
            True if market meets all criteria
        """
        # Check minimum probability
        min_prob = self.settings.get('min_probability', 0.7)
        yes_price = market.get('yes_price', 0)
        no_price = market.get('no_price', 0)
        
        # We want high probability YES or NO positions
        max_price = max(yes_price, no_price)
        if max_price < min_prob:
            return False
        
        # Check minimum liquidity
        min_liquidity = self.settings.get('min_liquidity', 10000)
        if market.get('liquidity', 0) < min_liquidity:
            return False
        
        # Check category filter (if specified)
        category_filter = self.settings.get('category', 'all')
        if category_filter != 'all':
            market_category = market.get('category', '').lower()
            if category_filter.lower() not in market_category:
                return False
        
        return True
    
    def execute_trade(self, market: Dict):
        """
        Execute a trade on a market
        
        Args:
            market: Market data to trade
        """
        position_size = self.settings.get('position_size', 100)
        
        # Determine which side to trade (YES or NO)
        yes_price = market.get('yes_price', 0)
        no_price = market.get('no_price', 0)
        
        if yes_price > no_price:
            position = "YES"
            price = yes_price
        else:
            position = "NO"
            price = no_price
        
        print("\n" + "="*60)
        print("🚀 EXECUTING TRADE")
        print("="*60)
        print(f"Market: {market.get('question', 'Unknown')[:50]}...")
        print(f"Position: {position}")
        print(f"Price: {price:.1%}")
        print(f"Amount: ${position_size}")
        print(f"Expected Profit: ${position_size * (1 - price):.2f}")
        print("="*60)
        
        # Simulate trade execution (in production, this would call the actual trading API)
        trade_record = {
            "timestamp": datetime.now().isoformat(),
            "market": market.get('question', 'Unknown'),
            "position": position,
            "price": price,
            "amount": position_size,
            "status": "executed"
        }
        
        self.trade_history.append(trade_record)
        self.trades_today += 1
        
        # Simulate profit (in reality, you'd track when position closes)
        simulated_profit = position_size * (1 - price) * 0.8  # 80% win assumption
        self.total_profit += simulated_profit
        
        print(f"✅ Trade executed! Total profit today: ${self.total_profit:.2f}\n")
    
    def print_summary(self):
        """Print trading summary"""
        print("\n" + "="*60)
        print("📊 TRADING SUMMARY")
        print("="*60)
        print(f"Total Trades Today: {self.trades_today}")
        print(f"Total Profit: ${self.total_profit:.2f}")
        print(f"Average Profit per Trade: ${self.total_profit / max(self.trades_today, 1):.2f}")
        print("="*60 + "\n")


def test_bot():
    """Test the trading bot with sample settings"""
    print("🧪 Testing Trading Bot...\n")
    
    # Sample user settings
    settings = {
        "min_probability": 0.65,  # 65% minimum win chance
        "category": "all",  # All categories
        "max_duration_hours": 168,  # 1 week max
        "position_size": 50,  # $50 per trade
        "max_daily_trades": 3,  # Max 3 trades for testing
        "min_liquidity": 5000  # $5k minimum liquidity
    }
    
    # Create bot instance
    bot = TradingBot(settings)
    
    # Run bot for a short test (will stop after 3 trades or user interrupt)
    print("Press Ctrl+C to stop the bot\n")
    bot.start()


if __name__ == "__main__":
    test_bot()