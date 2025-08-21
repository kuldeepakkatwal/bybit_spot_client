"""
Modular Bybit Trading Client Library

This library provides separate, reusable clients for different aspects of trading:
- TradingClient: Pure trading operations with Bybit
- DatabaseClient: Database operations with connection pooling
- WebSocketClient: Real-time order updates via WebSocket
- OrderManager: Orchestrates all clients for complete functionality
"""

from .trading_client import TradingClient
from .database_client import DatabaseClient
from .websocket_client import WebSocketClient
from .order_manager import OrderManager

__all__ = [
    'TradingClient',
    'DatabaseClient',
    'WebSocketClient',
    'OrderManager'
]

__version__ = '1.0.0'