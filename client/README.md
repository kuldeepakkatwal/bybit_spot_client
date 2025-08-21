# 🚀 Modular Spot Trading Client Library for Bybit

A professional, modular Python library for spot trading on Bybit exchange. Built with clean architecture principles, this library provides independent, reusable components for trading, database management, and real-time order tracking.

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Client Documentation](#client-documentation)
- [Usage Examples](#usage-examples)
- [Database Setup](#database-setup)
- [API Credentials](#api-credentials)
- [Using with Claude Code](#using-with-claude-code)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This library provides three independent clients that can be used separately or together:

- **TradingClient**: Execute spot trades on Bybit
- **DatabaseClient**: Manage order history in PostgreSQL
- **WebSocketClient**: Real-time order status updates
- **OrderManager**: Optional orchestrator combining all three

Perfect for developers building trading bots, portfolio managers, or automated trading strategies.

## ✨ Features

- ✅ **Modular Design** - Use only what you need
- ✅ **Spot Trading Focus** - Optimized for spot markets (no leverage/derivatives)
- ✅ **Real-time Updates** - WebSocket integration for instant order status
- ✅ **Database Integration** - PostgreSQL with connection pooling
- ✅ **Type Hints** - Full typing support for better IDE experience
- ✅ **Error Handling** - Comprehensive error management
- ✅ **Testnet Support** - Safe testing environment
- ✅ **Production Ready** - Used in live trading environments

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│              Your Trading Bot               │
└─────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Trading    │ │   Database   │ │  WebSocket   │
│    Client    │ │    Client    │ │    Client    │
└──────────────┘ └──────────────┘ └──────────────┘
        ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│    Bybit     │ │  PostgreSQL  │ │   Bybit WS   │
│   Exchange   │ │   Database   │ │   Updates    │
└──────────────┘ └──────────────┘ └──────────────┘
```

## 📦 Installation

### Prerequisites

```bash
# Python 3.8+ required
python3 --version

# PostgreSQL (if using DatabaseClient)
psql --version
```

### Install Dependencies

```bash
# Install required packages
pip install pybit psycopg2-binary

# Or use requirements.txt
pip install -r requirements.txt
```

### Project Structure

```
your_project/
├── client/
│   ├── __init__.py
│   ├── trading_client.py
│   ├── database_client.py
│   ├── websocket_client.py
│   └── order_manager.py
├── developer_test_project.py
└── README.md
```

## 🚀 Quick Start

### Minimal Example - Just Trading

```python
from client import TradingClient

# Initialize
trader = TradingClient(
    api_key="your_api_key",
    api_secret="your_api_secret",
    testnet=True
)

# Place a spot order
result = trader.place_spot_order(
    symbol="BTCUSDT",
    side="Buy",
    order_type="Limit",
    qty="0.001",
    price="50000"
)

if result['success']:
    print(f"Order placed: {result['order_id']}")
```

### Complete Example - All Features

```python
from client import TradingClient, DatabaseClient, WebSocketClient

# 1. Initialize clients
trader = TradingClient(api_key="key", api_secret="secret", testnet=True)
db = DatabaseClient(dbname="trading", user="postgres", password="pass")
ws = WebSocketClient(api_key="key", api_secret="secret", testnet=True)

# 2. Setup database
db.create_table("orders", [
    "id SERIAL PRIMARY KEY",
    "order_id VARCHAR(100) UNIQUE",
    "symbol VARCHAR(20)",
    "status VARCHAR(20)"
])

# 3. Setup WebSocket tracking
def on_order_update(order):
    print(f"Order {order['order_id']} status: {order['status']}")
    # Update database
    db.update("orders", 
              {"status": order['status']}, 
              "order_id = %s", 
              (order['order_id'],))

ws.subscribe_orders(on_order_update)
ws.start()

# 4. Place order and save to database
result = trader.place_spot_order("BTCUSDT", "Buy", "Limit", "0.001", "50000")
if result['success']:
    db.insert("orders", {
        "order_id": result['order_id'],
        "symbol": "BTCUSDT",
        "status": "New"
    })
```

## 📚 Client Documentation

### TradingClient

Handles all spot trading operations with Bybit.

```python
from client import TradingClient

trader = TradingClient(api_key, api_secret, testnet=True)
```

**Methods:**
- `place_spot_order(symbol, side, order_type, qty, price)` - Place an order
- `cancel_spot_order(symbol, order_id)` - Cancel an order
- `get_open_orders(symbol)` - Get open orders
- `get_order_history(symbol, limit)` - Get historical orders
- `get_spot_balance(coin)` - Get wallet balance
- `get_ticker(symbol)` - Get current price

### DatabaseClient

Manages PostgreSQL database operations with connection pooling.

```python
from client import DatabaseClient

db = DatabaseClient(
    dbname="trading",
    user="postgres",
    password="password",
    host="localhost",
    port="5432"
)
```

**Methods:**
- `create_table(table_name, columns)` - Create a table
- `insert(table_name, data)` - Insert a record
- `update(table_name, data, where_clause, where_params)` - Update records
- `select(table_name, columns, where_clause, where_params)` - Query records
- `delete(table_name, where_clause, where_params)` - Delete records

### WebSocketClient

Provides real-time updates via WebSocket connection.

```python
from client import WebSocketClient

ws = WebSocketClient(api_key, api_secret, testnet=True)
```

**Methods:**
- `subscribe_orders(callback)` - Get order updates
- `subscribe_positions(callback)` - Get position updates
- `subscribe_executions(callback)` - Get trade executions
- `start()` - Start WebSocket connection
- `stop()` - Stop WebSocket connection

### OrderManager (Optional)

Combines all three clients for convenience.

```python
from client import OrderManager

manager = OrderManager(
    api_key="key",
    api_secret="secret",
    db_params={"dbname": "trading", "user": "postgres", "password": "pass"},
    testnet=True
)

# Setup and use
manager.setup_database("orders", columns=[...])
manager.start_order_tracking()
manager.place_spot_order("BTCUSDT", "Buy", "Limit", "0.001", "50000")
```

## 💡 Usage Examples

### Example 1: Simple DCA Bot

```python
import time
from client import TradingClient

trader = TradingClient(api_key, api_secret, testnet=True)

def dca_buy(symbol, usdt_amount):
    # Get current price
    ticker = trader.get_ticker(symbol)
    if ticker['success']:
        price = float(ticker['last_price'])
        qty = usdt_amount / price
        
        # Place market order
        result = trader.place_spot_order(
            symbol=symbol,
            side="Buy",
            order_type="Market",
            qty=f"{qty:.6f}"
        )
        return result

# Buy $10 of BTC every hour
while True:
    dca_buy("BTCUSDT", 10)
    time.sleep(3600)
```

### Example 2: Order with Database Tracking

```python
from client import TradingClient, DatabaseClient

trader = TradingClient(api_key, api_secret)
db = DatabaseClient(**db_config)

# Place order
result = trader.place_spot_order("BTCUSDT", "Buy", "Limit", "0.001", "50000")

# Save to database
if result['success']:
    db.insert("orders", {
        "order_id": result['order_id'],
        "symbol": "BTCUSDT",
        "side": "Buy",
        "quantity": 0.001,
        "price": 50000,
        "status": "New",
        "created_at": datetime.now()
    })
```

### Example 3: Real-time Order Monitoring

```python
from client import WebSocketClient, DatabaseClient

ws = WebSocketClient(api_key, api_secret)
db = DatabaseClient(**db_config)

def handle_order_update(order):
    # Print update
    print(f"Order {order['order_id']}: {order['status']}")
    
    # Update database
    db.update(
        "orders",
        {"status": order['status'], "updated_at": datetime.now()},
        "order_id = %s",
        (order['order_id'],)
    )
    
    # Custom logic based on status
    if order['status'] == 'Filled':
        print(f"Order {order['order_id']} completed!")

ws.subscribe_orders(handle_order_update)
ws.start()
```

## 🗄️ Database Setup

### PostgreSQL Installation

```bash
# macOS
brew install postgresql
brew services start postgresql

# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql

# Create database
createdb trading_db
```

### Create User

```sql
-- Connect to PostgreSQL
psql -d postgres

-- Create user
CREATE USER trader WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE trading_db TO trader;
```

### Example Table Schema

```python
db = DatabaseClient(dbname="trading_db", user="trader", password="your_password")

db.create_table("spot_orders", [
    "id SERIAL PRIMARY KEY",
    "order_id VARCHAR(100) UNIQUE NOT NULL",
    "timestamp TIMESTAMPTZ DEFAULT NOW()",
    "symbol VARCHAR(20) NOT NULL",
    "side VARCHAR(10) NOT NULL",
    "order_type VARCHAR(20) NOT NULL",
    "quantity DECIMAL(20,8) NOT NULL",
    "price DECIMAL(20,8)",
    "status VARCHAR(50) NOT NULL",
    "filled_qty DECIMAL(20,8) DEFAULT 0"
])
```

## 🔑 API Credentials

### Get Bybit Testnet API Keys

1. Go to [Bybit Testnet](https://testnet.bybit.com/)
2. Register/Login
3. Navigate to API Management
4. Create new API key with spot trading permissions
5. Save your API Key and Secret

### Security Best Practices

```python
# Use environment variables (recommended)
import os
from client import TradingClient

api_key = os.getenv('BYBIT_API_KEY')
api_secret = os.getenv('BYBIT_API_SECRET')

trader = TradingClient(api_key, api_secret, testnet=True)
```

```bash
# .env file (add to .gitignore!)
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
```

## 🤖 Using with Claude Code

This library is designed to work perfectly with Claude Code. Here's how to use it effectively:

### 1. Initial Setup with Claude

```markdown
"I want to create a spot trading bot using the modular client library. 
Please help me set up a bot that:
1. Monitors BTCUSDT price
2. Places buy orders when price drops 5%
3. Tracks all orders in PostgreSQL
4. Updates order status in real-time"
```

### 2. Claude Code Best Practices

```python
# Tell Claude your requirements clearly
"""
Requirements for my trading bot:
- Use TradingClient for orders
- Use DatabaseClient for PostgreSQL
- Use WebSocketClient for real-time updates
- Trade only spot (no leverage)
- Testnet only for safety
"""

# Claude will generate code using the modular clients
from client import TradingClient, DatabaseClient, WebSocketClient
# ... implementation follows
```

### 3. Debugging with Claude

```markdown
"My WebSocket isn't receiving updates. Here's my code: [paste code].
I'm using the modular client library. What's wrong?"
```

### 4. Extending with Claude

```markdown
"Add a feature to my bot that:
1. Calculates profit/loss for each trade
2. Stores P&L in the database
3. Sends summary every hour
Use the existing DatabaseClient for storage."
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. WebSocket Not Receiving Updates
```python
# Ensure WebSocket is started
ws.start()

# Wait for connection
import time
time.sleep(2)

# Check connection status
if ws.is_connected():
    print("WebSocket connected")
```

#### 2. Database Connection Failed
```python
# Check PostgreSQL is running
# macOS: brew services list
# Linux: sudo systemctl status postgresql

# Verify credentials
psql -U your_user -d your_database -h localhost
```

#### 3. Order Value Too Low Error
```python
# Minimum order values (approximate):
# BTCUSDT: 0.001 BTC or $50 equivalent
# Adjust quantity or price:
trader.place_spot_order("BTCUSDT", "Buy", "Limit", "0.001", "50000")
```

#### 4. Account Type Error on Testnet
```python
# Testnet uses UNIFIED account type
# The library handles this automatically
# Just use: testnet=True
```

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 📖 Complete Examples

Check out these files for complete implementations:

- `developer_test_project.py` - Full example showing modular usage
- `test_spot_project.py` - OrderManager integration example
- `client/example_spot_usage.py` - Various trading strategies

## 🤝 Contributing

Contributions are welcome! To extend the library:

1. Keep clients independent and focused
2. Add to existing clients rather than creating new ones
3. Include type hints and docstrings
4. Handle errors gracefully
5. Test with both testnet and mainnet

## 📄 License

MIT License - Use freely in your projects

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section
2. Review example files
3. Use Claude Code for implementation help
4. Check Bybit API documentation

---

Built with ❤️ for the trading community. Happy trading! 🚀