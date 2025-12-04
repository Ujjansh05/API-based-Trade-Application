import sqlite3
from datetime import datetime, date
import os

class OrderTracker:
    def __init__(self, db_path='orders.db'):
        # Store database in user's local app data
        app_data = os.path.join(os.getenv('LOCALAPPDATA'), 'AntigravityTrader')
        os.makedirs(app_data, exist_ok=True)
        self.db_path = os.path.join(app_data, db_path)
        self.init_db()
    
    def init_db(self):
        """Create orders table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT,
                symbol TEXT,
                quantity INTEGER,
                order_type TEXT,
                strategy TEXT,
                price REAL,
                status TEXT DEFAULT 'PENDING',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def add_order(self, order_id, symbol, quantity, order_type, strategy, price=0):
        """Add a new order to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (order_id, symbol, quantity, order_type, strategy, price, status)
            VALUES (?, ?, ?, ?, ?, ?, 'PLACED')
        ''', (order_id, symbol, quantity, order_type, strategy, price))
        conn.commit()
        conn.close()
        print(f"Order logged: {order_id} - {symbol} {order_type} x{quantity}")
    
    def get_today_count(self):
        """Get number of orders placed today"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        today = date.today().isoformat()
        cursor.execute('''
            SELECT COUNT(*) FROM orders 
            WHERE DATE(timestamp) = ?
        ''', (today,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_today_orders(self):
        """Get all orders placed today"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        today = date.today().isoformat()
        cursor.execute('''
            SELECT order_id, symbol, quantity, order_type, strategy, price, status, timestamp
            FROM orders 
            WHERE DATE(timestamp) = ?
            ORDER BY timestamp DESC
        ''', (today,))
        rows = cursor.fetchall()
        conn.close()
        
        orders = []
        for row in rows:
            orders.append({
                'order_id': row[0],
                'symbol': row[1],
                'quantity': row[2],
                'order_type': row[3],
                'strategy': row[4],
                'price': row[5],
                'status': row[6],
                'timestamp': row[7]
            })
        return orders
    
    def get_recent_orders(self, limit=50):
        """Get recent orders"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT order_id, symbol, quantity, order_type, strategy, price, status, timestamp
            FROM orders 
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        orders = []
        for row in rows:
            orders.append({
                'order_id': row[0],
                'symbol': row[1],
                'quantity': row[2],
                'order_type': row[3],
                'strategy': row[4],
                'price': row[5],
                'status': row[6],
                'timestamp': row[7]
            })
        return orders

# Global instance
order_tracker = OrderTracker()
