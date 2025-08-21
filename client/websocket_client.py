"""
WebSocket Client for Real-time Updates

This client handles ONLY WebSocket connections for real-time data.
No database dependencies, no order placement - just clean WebSocket functionality.
"""

import logging
import threading
from typing import Callable, Dict, Any, List, Optional
from pybit.unified_trading import WebSocket


class WebSocketClient:
    """
    A focused client for Bybit WebSocket connections.
    
    Features:
    - Subscribe to real-time order updates
    - Subscribe to position updates
    - Subscribe to execution updates
    - Custom callback handlers
    - Multiple subscription management
    """
    
    def __init__(self, 
                 api_key: str,
                 api_secret: str,
                 testnet: bool = True):
        """
        Initialize the WebSocket Client.
        
        Args:
            api_key: Your Bybit API key
            api_secret: Your Bybit API secret
            testnet: Whether to use testnet (default True for safety)
        """
        self.logger = logging.getLogger(__name__)
        self.testnet = testnet
        
        # Initialize WebSocket for private channel (authenticated)
        self.ws = WebSocket(
            testnet=self.testnet,
            channel_type="private",
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Store active subscriptions
        self.subscriptions = {}
        self.ws_thread = None
        self.is_running = False
        
        self.logger.info(f"WebSocket Client initialized ({'testnet' if testnet else 'mainnet'})")
    
    def subscribe_orders(self, callback: Callable[[Dict], None]) -> bool:
        """
        Subscribe to real-time order updates.
        
        Args:
            callback: Function to call when order update is received
            
        Returns:
            True if subscription successful
        """
        try:
            def order_handler(message):
                """Internal handler that processes and forwards order messages."""
                self.logger.debug(f"Order update received: {message}")
                
                # Extract order data from message
                for order in message.get("data", []):
                    processed_order = {
                        'order_id': order.get('orderId'),
                        'symbol': order.get('symbol'),
                        'side': order.get('side'),
                        'price': order.get('price'),
                        'qty': order.get('qty'),
                        'status': order.get('orderStatus'),
                        'type': order.get('orderType'),
                        'time': order.get('updatedTime'),
                        'raw': order  # Include raw data for advanced users
                    }
                    
                    # Call user's callback with processed data
                    callback(processed_order)
            
            # Subscribe to order topic
            self.ws.subscribe(topic="order", callback=order_handler)
            self.subscriptions['order'] = callback
            
            self.logger.info("Subscribed to order updates")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe to orders: {e}")
            return False
    
    def subscribe_positions(self, callback: Callable[[Dict], None]) -> bool:
        """
        Subscribe to real-time position updates.
        
        Args:
            callback: Function to call when position update is received
            
        Returns:
            True if subscription successful
        """
        try:
            def position_handler(message):
                """Internal handler that processes and forwards position messages."""
                self.logger.debug(f"Position update received: {message}")
                
                # Extract position data from message
                for position in message.get("data", []):
                    processed_position = {
                        'symbol': position.get('symbol'),
                        'side': position.get('side'),
                        'size': position.get('size'),
                        'entry_price': position.get('avgPrice'),
                        'mark_price': position.get('markPrice'),
                        'pnl': position.get('unrealisedPnl'),
                        'margin': position.get('positionIM'),
                        'leverage': position.get('leverage'),
                        'raw': position
                    }
                    
                    # Call user's callback with processed data
                    callback(processed_position)
            
            # Subscribe to position topic
            self.ws.subscribe(topic="position", callback=position_handler)
            self.subscriptions['position'] = callback
            
            self.logger.info("Subscribed to position updates")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe to positions: {e}")
            return False
    
    def subscribe_executions(self, callback: Callable[[Dict], None]) -> bool:
        """
        Subscribe to real-time execution (trade) updates.
        
        Args:
            callback: Function to call when execution update is received
            
        Returns:
            True if subscription successful
        """
        try:
            def execution_handler(message):
                """Internal handler that processes and forwards execution messages."""
                self.logger.debug(f"Execution update received: {message}")
                
                # Extract execution data from message
                for execution in message.get("data", []):
                    processed_execution = {
                        'order_id': execution.get('orderId'),
                        'symbol': execution.get('symbol'),
                        'side': execution.get('side'),
                        'price': execution.get('execPrice'),
                        'qty': execution.get('execQty'),
                        'fee': execution.get('execFee'),
                        'time': execution.get('execTime'),
                        'type': execution.get('execType'),
                        'raw': execution
                    }
                    
                    # Call user's callback with processed data
                    callback(processed_execution)
            
            # Subscribe to execution topic
            self.ws.subscribe(topic="execution", callback=execution_handler)
            self.subscriptions['execution'] = callback
            
            self.logger.info("Subscribed to execution updates")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe to executions: {e}")
            return False
    
    def subscribe_wallet(self, callback: Callable[[Dict], None]) -> bool:
        """
        Subscribe to real-time wallet updates.
        
        Args:
            callback: Function to call when wallet update is received
            
        Returns:
            True if subscription successful
        """
        try:
            def wallet_handler(message):
                """Internal handler that processes and forwards wallet messages."""
                self.logger.debug(f"Wallet update received: {message}")
                
                # Extract wallet data from message
                for wallet_data in message.get("data", []):
                    processed_wallet = {
                        'account_type': wallet_data.get('accountType'),
                        'coins': wallet_data.get('coin', []),
                        'time': wallet_data.get('creationTime'),
                        'raw': wallet_data
                    }
                    
                    # Call user's callback with processed data
                    callback(processed_wallet)
            
            # Subscribe to wallet topic
            self.ws.subscribe(topic="wallet", callback=wallet_handler)
            self.subscriptions['wallet'] = callback
            
            self.logger.info("Subscribed to wallet updates")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe to wallet: {e}")
            return False
    
    def subscribe_custom(self, 
                        topic: str,
                        callback: Callable[[Dict], None]) -> bool:
        """
        Subscribe to a custom topic with raw message handling.
        
        Args:
            topic: WebSocket topic to subscribe to
            callback: Function to call when message is received
            
        Returns:
            True if subscription successful
        """
        try:
            self.ws.subscribe(topic=topic, callback=callback)
            self.subscriptions[topic] = callback
            
            self.logger.info(f"Subscribed to custom topic: {topic}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe to {topic}: {e}")
            return False
    
    def unsubscribe(self, topic: str) -> bool:
        """
        Unsubscribe from a topic.
        
        Args:
            topic: Topic to unsubscribe from
            
        Returns:
            True if unsubscription successful
        """
        try:
            if topic in self.subscriptions:
                self.ws.unsubscribe(topic=topic)
                del self.subscriptions[topic]
                self.logger.info(f"Unsubscribed from {topic}")
                return True
            else:
                self.logger.warning(f"Not subscribed to {topic}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to unsubscribe from {topic}: {e}")
            return False
    
    def start(self):
        """
        Start the WebSocket connection.
        
        The pybit WebSocket manages its own thread internally,
        so we just need to track the state.
        """
        if not self.is_running:
            # pybit WebSocket runs in its own thread automatically
            self.is_running = True
            self.logger.info("WebSocket connection started")
        else:
            self.logger.warning("WebSocket is already running")
    
    def stop(self):
        """Stop the WebSocket connection."""
        if self.is_running:
            self.ws.exit()
            self.is_running = False
            self.logger.info("WebSocket connection stopped")
        else:
            self.logger.warning("WebSocket is not running")
    
    def get_subscriptions(self) -> List[str]:
        """
        Get list of active subscriptions.
        
        Returns:
            List of subscribed topics
        """
        return list(self.subscriptions.keys())
    
    def is_connected(self) -> bool:
        """
        Check if WebSocket is connected and running.
        
        Returns:
            True if connected and running
        """
        return self.is_running
    
    def __enter__(self):
        """Context manager entry - starts WebSocket."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stops WebSocket."""
        self.stop()