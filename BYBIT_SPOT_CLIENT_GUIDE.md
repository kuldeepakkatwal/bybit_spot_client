# BybitSpotClient - Complete Developer Guide

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Credentials](#api-credentials)
- [Core Features](#core-features)
- [API Reference](#api-reference)
- [WebSocket Features](#websocket-features)
- [Account Types](#account-types)
- [Error Handling](#error-handling)
- [Testnet vs Mainnet](#testnet-vs-mainnet)
- [Complete Examples](#complete-examples)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

`BybitSpotClient` is a Python client library for Bybit's spot trading API. It provides a clean, simple interface for:
- Spot trading operations (place, cancel, check orders)
- Real-time WebSocket data streams
- Account balance management
- Market data retrieval

**Key Features:**
- Supports both testnet and mainnet
- WebSocket for real-time updates
- No database dependencies
- Direct API access without unnecessary abstractions
- Spot trading only (no derivatives/futures)

## Installation

### Prerequisites
```bash
# Required Python version
Python 3.7+

# Install dependencies
pip install pybit==5.6.2
pip install websocket-client==1.6.4
```

### Project Structure
```
bybit_spot_client/
├── client/
│   ├── bybit_spot_client.py    # Main client library
│   └── ...
├── test/                        # Test scripts
└── requirements.txt             # Dependencies
```

## Quick Start

```python
from bybit_spot_client import BybitSpotClient

# Initialize client
client = BybitSpotClient(
    api_key="your_api_key",
    api_secret="your_api_secret",
    testnet=True  # Use False for mainnet
)

# Place a limit order
response = client.place_spot_order(
    symbol="BTCUSDT",
    side="Buy",
    order_type="Limit",
    qty="0.001",
    price="50000"
)

if response['success']:
    print(f"Order placed! ID: {response['order_id']}")
```

## API Credentials

### Getting API Keys

#### Testnet (for testing with fake money):
1. Go to https://testnet.bybit.com
2. Register/Login
3. Navigate to API Management
4. Create new API key with spot trading permissions
5. Save your API Key and Secret

#### Mainnet (real trading):
1. Go to https://www.bybit.com
2. Login to your account
3. Go to Account & Security → API Management
4. Create API key with spot trading permissions
5. **Important:** Keep your API credentials secure!

### Security Best Practices
```python
# Never hardcode credentials
import os
API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')

# Or use a config file (add to .gitignore)
from config import API_KEY, API_SECRET
```

## Core Features

### Trading Operations
- Place spot orders (limit and market)
- Cancel orders
- Check order status
- View order history

### Market Data
- Get current ticker/price
- Check trading pairs

### Account Management
- Check spot balances
- Support for multiple account types (UNIFIED, FUND)

### WebSocket Real-time Data
- Order updates
- Trade executions
- Balance changes

## API Reference

### Initialization

```python
client = BybitSpotClient(api_key, api_secret, testnet=True)
```

**Parameters:**
- `api_key` (str): Your Bybit API key
- `api_secret` (str): Your Bybit API secret
- `testnet` (bool): True for testnet, False for mainnet

### Trading Methods

#### place_spot_order()
Places a spot order on Bybit.

```python
response = client.place_spot_order(
    symbol="BTCUSDT",      # Trading pair
    side="Buy",            # "Buy" or "Sell"
    order_type="Limit",    # "Limit" or "Market"
    qty="0.001",           # Quantity in base currency
    price="50000"          # Price (required for Limit orders)
)
```

**Returns:**
```python
{
    'success': True,
    'order_id': '1234567890',
    'response': {...}  # Full Bybit response
}
```

#### cancel_spot_order()
Cancels an open order.

```python
response = client.cancel_spot_order(
    symbol="BTCUSDT",
    order_id="1234567890"
)
```

#### get_open_orders()
Retrieves all open orders.

```python
# Get all open orders
response = client.get_open_orders()

# Get orders for specific symbol
response = client.get_open_orders(symbol="BTCUSDT")

# Check specific order
response = client.get_open_orders(order_id="1234567890")
```

#### get_order_history()
Gets historical orders.

```python
response = client.get_order_history(
    symbol="BTCUSDT",  # Optional: filter by symbol
    limit=50           # Number of records (default: 50)
)
```

### Market Data Methods

#### get_ticker()
Gets current price and market data.

```python
response = client.get_ticker("BTCUSDT")

# Returns:
{
    'success': True,
    'symbol': 'BTCUSDT',
    'last_price': '67890.50',
    'bid': '67890.00',
    'ask': '67891.00',
    'volume_24h': '1234.56'
}
```

### Account Methods

#### get_spot_balance()
Checks wallet balance.

```python
# Get all balances (default account)
response = client.get_spot_balance()

# Get specific coin balance
response = client.get_spot_balance(coin="USDT")

# Get balance from specific account type
response = client.get_spot_balance(account_type="UNIFIED")
response = client.get_spot_balance(account_type="FUND")  # Mainnet only
```

**Account Types:**
- `UNIFIED`: Trading account (default for testnet)
- `FUND`: Funding account (mainnet only)
- `SPOT`: Spot account (mainnet)

## WebSocket Features

### Real-time Order Updates

```python
# Define callback function
def on_order_update(message):
    # Message contains raw data from Bybit
    for order in message.get('data', []):
        print(f"Order {order.get('orderId')}: {order.get('orderStatus')}")

# Subscribe to updates
client.subscribe_orders(on_order_update)

# Start WebSocket
client.start_websocket()

# ... your application runs ...

# Stop when done
client.stop_websocket()
```

### Available Subscriptions

#### subscribe_orders()
Real-time order status updates.
```python
client.subscribe_orders(callback_function)
```

#### subscribe_executions()
Trade fill notifications.
```python
def on_execution(message):
    for exec in message.get('data', []):
        print(f"Filled: {exec.get('execQty')} @ {exec.get('execPrice')}")

client.subscribe_executions(on_execution)
```

#### subscribe_wallet()
Balance change notifications.
```python
def on_wallet_update(message):
    print(f"Wallet updated: {message}")

client.subscribe_wallet(on_wallet_update)
```

#### subscribe_custom()
Subscribe to any Bybit WebSocket topic.
```python
client.subscribe_custom("topic_name", callback_function)
```

#### unsubscribe()
Stop receiving updates for a topic.
```python
client.unsubscribe("order")
```

## Account Types

### Testnet
- **UNIFIED**: The only account type available on testnet
- Contains both trading balance and funding
- Used for all operations

### Mainnet
- **UNIFIED**: Main trading account
- **FUND**: Deposit/withdrawal account
- **SPOT**: Legacy spot trading account

### Checking Different Accounts
```python
# On testnet (only UNIFIED works)
unified_balance = client.get_spot_balance(account_type="UNIFIED")

# On mainnet (multiple accounts)
trading_balance = client.get_spot_balance(account_type="UNIFIED")
funding_balance = client.get_spot_balance(account_type="FUND")
```

## Error Handling

### Common Errors and Solutions

#### 1. Order value exceeded lower limit
```python
# Error Code: 170140
# Cause: Order size too small OR market orders not supported on testnet
# Solution: Use larger quantities or switch to limit orders
```

#### 2. Insufficient balance
```python
# Cause: Not enough funds in account
# Solution: Check balance before placing order
balance = client.get_spot_balance(coin="USDT")
```

#### 3. Invalid API key
```python
# Cause: Wrong credentials or permissions
# Solution: Verify API key has spot trading permissions
```

#### 4. Order does not exist
```python
# When canceling: Order already filled or cancelled
# Solution: Check order status first
```

### Error Response Format
```python
{
    'success': False,
    'error': 'Error message from Bybit',
    'response': {
        'retCode': 170140,
        'retMsg': 'Detailed error message'
    }
}
```

## Testnet vs Mainnet

### Key Differences

| Feature | Testnet | Mainnet |
|---------|---------|---------|
| Real Money | No (fake funds) | Yes |
| API Endpoint | api-testnet.bybit.com | api.bybit.com |
| Account Types | UNIFIED only | UNIFIED, FUND, SPOT |
| Market Orders | Often restricted | Fully supported |
| Minimum Orders | Higher minimums | Normal minimums |

### Testnet Limitations
- Market orders may not work (use limit orders)
- Only UNIFIED account type available
- Higher minimum order values
- Some features may be disabled

### Switching to Mainnet
```python
# Simply change testnet parameter
client = BybitSpotClient(
    api_key=MAINNET_API_KEY,
    api_secret=MAINNET_API_SECRET,
    testnet=False  # Switch to mainnet
)
```

## Complete Examples

### Example 1: Place and Cancel Order
```python
from bybit_spot_client import BybitSpotClient

client = BybitSpotClient(api_key, api_secret, testnet=True)

# Place limit order
order = client.place_spot_order(
    symbol="BTCUSDT",
    side="Buy",
    order_type="Limit",
    qty="0.001",
    price="50000"
)

if order['success']:
    order_id = order['order_id']
    print(f"Order placed: {order_id}")
    
    # Cancel the order
    cancel = client.cancel_spot_order("BTCUSDT", order_id)
    if cancel['success']:
        print("Order cancelled")
```

### Example 2: Monitor Orders with WebSocket
```python
import time
from client.bybit_spot_client import BybitSpotClient

client = BybitSpotClient(api_key, api_secret, testnet=True)

def handle_order_update(message):
    for order in message.get('data', []):
        status = order.get('orderStatus')
        if status == 'Filled':
            print(f"Order filled: {order.get('orderId')}")
        elif status == 'Cancelled':
            print(f"Order cancelled: {order.get('orderId')}")

# Subscribe and start
client.subscribe_orders(handle_order_update)
client.start_websocket()

# Place an order
client.place_spot_order(
    symbol="ETHUSDT",
    side="Buy",
    order_type="Limit",
    qty="0.1",
    price="3000"
)

# Keep running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    client.stop_websocket()
```

### Example 3: Check Balances Across Accounts
```python
client = BybitSpotClient(api_key, api_secret, testnet=False)  # Mainnet

# Check trading account
trading = client.get_spot_balance(account_type="UNIFIED")
print(f"Trading Balance: {trading['total_equity']}")

# Check funding account
funding = client.get_spot_balance(account_type="FUND")
print(f"Funding Balance: {funding['total_equity']}")

# Check specific coin
usdt = client.get_spot_balance(coin="USDT", account_type="UNIFIED")
for coin in usdt['coins']:
    if coin.get('coin') == 'USDT':
        print(f"USDT Available: {coin.get('walletBalance')}")
```

## Troubleshooting

### WebSocket Not Receiving Updates
```python
# Ensure you start the WebSocket after subscribing
client.subscribe_orders(callback)
client.start_websocket()  # Don't forget this!
```

### Orders Failing on Testnet
```python
# Use limit orders instead of market orders
# Market orders often don't work on testnet
response = client.place_spot_order(
    symbol="BTCUSDT",
    side="Buy",
    order_type="Limit",  # Not "Market"
    qty="0.001",
    price="60000"
)
```

### Can't Access FUND Account
```python
# FUND account only exists on mainnet
# On testnet, only use UNIFIED
if client.testnet:
    balance = client.get_spot_balance(account_type="UNIFIED")
else:
    balance = client.get_spot_balance(account_type="FUND")
```

## Best Practices

### 1. Always Check Responses
```python
response = client.place_spot_order(...)
if response['success']:
    # Handle success
    order_id = response['order_id']
else:
    # Handle error
    print(f"Error: {response['error']}")
```

### 2. Use Environment Variables
```python
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')
```

### 3. Implement Proper Error Handling
```python
try:
    response = client.place_spot_order(...)
    if not response['success']:
        logger.error(f"Order failed: {response['error']}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

### 4. Clean Shutdown
```python
try:
    # Your trading logic
    pass
finally:
    client.disconnect()  # Always disconnect cleanly
```

### 5. Rate Limiting
Bybit has rate limits. Avoid placing too many orders too quickly:
```python
import time

for order in orders:
    client.place_spot_order(**order)
    time.sleep(0.1)  # Small delay between orders
```

## Support and Resources

- **Bybit API Documentation**: https://bybit-exchange.github.io/docs/
- **Testnet**: https://testnet.bybit.com
- **Mainnet**: https://www.bybit.com
- **pybit Documentation**: https://github.com/bybit-exchange/pybit

## Limitations

- Spot trading only (no derivatives/futures)
- No built-in database functionality
- No batch order support (place orders one at a time)
- Testnet limitations:
  - Market orders may not work
  - Only UNIFIED account available
  - Higher minimum order values

## Version Information

- Client Version: 1.0.0
- Supported Bybit API: v5
- Python: 3.7+
- Dependencies: pybit==5.6.2

---

*This guide covers all features of the BybitSpotClient. For additional help, refer to the test scripts in the `/test` directory for working examples.*