"""
Spot Order Manager - Orchestrator for Spot Trading

This combines TradingClient, DatabaseClient, and WebSocketClient
to provide a complete spot trading solution with modular, reusable components.
Focuses exclusively on spot trading (no leverage, no derivatives).
"""

import logging
from typing import Dict, Any, List, Optional
from .trading_client import TradingClient
from .database_client import DatabaseClient
from .websocket_client import WebSocketClient


class OrderManager:
    """
    An orchestrator that combines all clients for complete spot trading functionality.
    
    This provides a high-level interface for spot trading,
    built on top of modular, reusable components.
    
    Features:
    - Place spot orders with automatic database logging
    - Real-time spot order tracking with automatic status updates
    - Database setup and management
    - Complete spot order lifecycle management
    - No leverage (spot trading only)
    """
    
    def __init__(self,
                 api_key: str,
                 api_secret: str,
                 db_params: Dict[str, str],
                 testnet: bool = True,
                 auto_track: bool = True):
        """
        Initialize the Order Manager with all necessary clients.
        
        Args:
            api_key: Your Bybit API key
            api_secret: Your Bybit API secret
            db_params: Database connection parameters
            testnet: Whether to use testnet (default True)
            auto_track: Automatically start order tracking (default True)
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize individual clients
        self.trading = TradingClient(api_key, api_secret, testnet)
        self.database = DatabaseClient(**db_params)
        self.websocket = WebSocketClient(api_key, api_secret, testnet)
        
        # Configuration
        self.auto_track = auto_track
        self.table_name = None
        
        self.logger.info("Order Manager initialized with all clients")
    
    def setup_database(self, 
                      table_name: str,
                      columns: List[str]) -> bool:
        """
        Set up the database table for order tracking.
        
        Args:
            table_name: Name of the table to create
            columns: List of column definitions
            
        Returns:
            True if successful
        """
        self.table_name = table_name
        success = self.database.create_table(table_name, columns)
        
        if success:
            self.logger.info(f"Database table '{table_name}' ready")
        
        return success
    
    def start_order_tracking(self, 
                           custom_handler: Optional[callable] = None) -> bool:
        """
        Start real-time order tracking with automatic database updates.
        
        Args:
            custom_handler: Optional custom handler for order updates
            
        Returns:
            True if successful
        """
        if not self.table_name:
            self.logger.error("Database table not set up. Call setup_database first.")
            return False
        
        def order_update_handler(order_data: Dict):
            """Handle order updates and sync to database."""
            order_id = order_data.get('order_id')
            status = order_data.get('status')
            
            if order_id and status:
                # Update database
                self.logger.info(f"Updating order {order_id} to status '{status}'")
                self.database.update(
                    self.table_name,
                    {'status': status},
                    'order_id = %s',
                    (order_id,)
                )
                
                # Call custom handler if provided
                if custom_handler:
                    custom_handler(order_data)
        
        # Subscribe to order updates
        success = self.websocket.subscribe_orders(order_update_handler)
        
        if success:
            # Start WebSocket connection
            self.websocket.start()
            self.logger.info("Real-time order tracking started")
        
        return success
    
    def place_spot_order(self,
                        symbol: str,
                        side: str,
                        order_type: str,
                        qty: str,
                        price: Optional[str] = None,
                        save_to_db: bool = True,
                        **kwargs) -> Dict[str, Any]:
        """
        Place a spot order with optional database logging.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            side: 'Buy' or 'Sell'
            order_type: 'Limit' or 'Market'
            qty: Order quantity
            price: Order price (required for limit orders)
            save_to_db: Whether to save order to database (default True)
            **kwargs: Additional order parameters
            
        Returns:
            Result dictionary with order information
        """
        # Place the spot order
        result = self.trading.place_spot_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            qty=qty,
            price=price,
            **kwargs
        )
        
        # Save to database if requested and successful
        if save_to_db and result['success'] and self.table_name:
            order_id = result['order_id']
            
            db_record = {
                'order_id': order_id,
                'symbol': symbol,
                'side': side,
                'order_type': order_type,
                'quantity': qty,
                'price': price,
                'status': 'New',
                'category': 'spot'
            }
            
            self.database.insert(self.table_name, db_record)
            self.logger.info(f"Spot order {order_id} saved to database")
        
        return result
    
    def place_order_simple(self, order_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simplified spot order placement for convenience.
        
        Args:
            order_dict: Order details dictionary with keys:
                - symbol: Trading pair
                - side: Buy/Sell
                - order_type: Limit/Market
                - qty: Quantity
                - price: Price (for limit orders)
            
        Returns:
            Result dictionary
        """
        # If auto_track is enabled and not already tracking, start it
        if self.auto_track and not self.websocket.is_connected():
            self.start_order_tracking()
        
        return self.place_spot_order(
            symbol=order_dict['symbol'],
            side=order_dict['side'],
            order_type=order_dict['order_type'],
            qty=order_dict['qty'],
            price=order_dict.get('price'),
            save_to_db=True
        )
    
    def cancel_spot_order(self,
                         symbol: str,
                         order_id: str,
                         update_db: bool = True) -> Dict[str, Any]:
        """
        Cancel a spot order with optional database update.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID to cancel
            update_db: Whether to update database (default True)
            
        Returns:
            Result dictionary
        """
        result = self.trading.cancel_spot_order(symbol, order_id)
        
        # Update database if requested and successful
        if update_db and result['success'] and self.table_name:
            self.database.update(
                self.table_name,
                {'status': 'Cancelled'},
                'order_id = %s',
                (order_id,)
            )
            self.logger.info(f"Order {order_id} marked as cancelled in database")
        
        return result
    
    def get_order_history(self,
                         symbol: Optional[str] = None,
                         limit: int = 100) -> Optional[List]:
        """
        Get order history from database.
        
        Args:
            symbol: Filter by symbol (optional)
            limit: Maximum number of records
            
        Returns:
            List of order records or None
        """
        if not self.table_name:
            self.logger.error("Database table not set up")
            return None
        
        where_clause = None
        where_params = None
        
        if symbol:
            where_clause = "symbol = %s"
            where_params = (symbol,)
        
        return self.database.select(
            self.table_name,
            where_clause=where_clause,
            where_params=where_params,
            order_by="timestamp DESC",
            limit=limit
        )
    
    def get_active_orders(self) -> Optional[List]:
        """
        Get active orders from database.
        
        Returns:
            List of active order records or None
        """
        if not self.table_name:
            self.logger.error("Database table not set up")
            return None
        
        return self.database.select(
            self.table_name,
            where_clause="status IN ('New', 'PartiallyFilled')",
            order_by="timestamp DESC"
        )
    
    def sync_orders_with_exchange(self) -> int:
        """
        Sync database with current orders on exchange.
        
        Args:
            category: Product category
            
        Returns:
            Number of orders synced
        """
        # Get open orders from exchange
        result = self.trading.get_open_orders()
        
        if not result['success']:
            self.logger.error("Failed to get orders from exchange")
            return 0
        
        synced = 0
        for order in result['orders']:
            order_id = order.get('orderId')
            status = order.get('orderStatus')
            
            if order_id and status and self.table_name:
                rows_updated = self.database.update(
                    self.table_name,
                    {'status': status},
                    'order_id = %s',
                    (order_id,)
                )
                
                if rows_updated:
                    synced += 1
        
        self.logger.info(f"Synced {synced} orders with exchange")
        return synced
    
    def get_spot_balance(self, coin: Optional[str] = None) -> Dict[str, Any]:
        """
        Get spot wallet balance.
        
        Args:
            coin: Specific coin to check (optional)
            
        Returns:
            Balance information
        """
        return self.trading.get_spot_balance(coin)
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current price information for a symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Ticker information including current price
        """
        return self.trading.get_ticker(symbol)
    
    def disconnect(self):
        """Gracefully disconnect all clients."""
        # Stop WebSocket
        if self.websocket.is_connected():
            self.websocket.stop()
            self.logger.info("WebSocket disconnected")
        
        # Close database connections
        self.database.close()
        self.logger.info("Database connections closed")
        
        self.logger.info("Order Manager disconnected")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()