"""
Spot Trading Client for Bybit Exchange

This client handles ONLY spot trading operations with Bybit.
No database dependencies, no WebSocket - just clean spot trading functionality.
"""

import logging
from pybit.unified_trading import HTTP
from typing import Dict, Any, Optional


class TradingClient:
    """
    A focused client for Bybit spot trading operations.
    
    Features:
    - Place spot orders (limit, market)
    - Cancel spot orders
    - Get order status
    - Get spot balances
    - No leverage (spot trading only)
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        Initialize the Spot Trading Client.
        
        Args:
            api_key: Your Bybit API key
            api_secret: Your Bybit API secret
            testnet: Whether to use testnet (default True for safety)
        """
        self.logger = logging.getLogger(__name__)
        self.testnet = testnet
        self.category = "spot"  # Fixed to spot trading
        
        # Initialize Bybit HTTP Client
        self.session = HTTP(
            testnet=self.testnet,
            api_key=api_key,
            api_secret=api_secret
        )
        
        self.logger.info(f"Spot Trading Client initialized ({'testnet' if testnet else 'mainnet'})")
    
    def place_spot_order(self, 
                        symbol: str,
                        side: str,
                        order_type: str,
                        qty: str,
                        price: Optional[str] = None,
                        **kwargs) -> Dict[str, Any]:
        """
        Place a spot order on Bybit.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            side: Buy or Sell
            order_type: Limit or Market
            qty: Order quantity (in base currency)
            price: Order price (required for limit orders)
            **kwargs: Additional order parameters
            
        Returns:
            Response from Bybit API including order_id if successful
        """
        try:
            order_params = {
                'category': self.category,
                'symbol': symbol,
                'side': side,
                'orderType': order_type,
                'qty': qty
            }
            
            if order_type.upper() == "LIMIT" and price:
                order_params['price'] = price
            elif order_type.upper() == "LIMIT" and not price:
                self.logger.error("Price is required for limit orders")
                return {
                    'success': False,
                    'error': 'Price is required for limit orders'
                }
            
            # Add any additional parameters
            order_params.update(kwargs)
            
            self.logger.info(f"Placing spot order: {order_params}")
            response = self.session.place_order(**order_params)
            
            if response.get('retCode') == 0:
                order_id = response['result']['orderId']
                self.logger.info(f"Spot order placed successfully. Order ID: {order_id}")
                return {
                    'success': True,
                    'order_id': order_id,
                    'response': response
                }
            else:
                self.logger.error(f"Failed to place spot order. Response: {response}")
                return {
                    'success': False,
                    'error': response.get('retMsg', 'Unknown error'),
                    'response': response
                }
                
        except Exception as e:
            self.logger.error(f"Exception placing spot order: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_spot_order(self, 
                         symbol: str,
                         order_id: str) -> Dict[str, Any]:
        """
        Cancel an open spot order.
        
        Args:
            symbol: Trading pair symbol
            order_id: The order ID to cancel
            
        Returns:
            Response from Bybit API
        """
        try:
            self.logger.info(f"Cancelling spot order {order_id} for {symbol}")
            
            response = self.session.cancel_order(
                category=self.category,
                symbol=symbol,
                orderId=order_id
            )
            
            if response.get('retCode') == 0:
                self.logger.info(f"Spot order {order_id} cancelled successfully")
                return {
                    'success': True,
                    'order_id': order_id,
                    'response': response
                }
            else:
                self.logger.error(f"Failed to cancel spot order. Response: {response}")
                return {
                    'success': False,
                    'error': response.get('retMsg', 'Unknown error'),
                    'response': response
                }
                
        except Exception as e:
            self.logger.error(f"Exception cancelling spot order: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_open_orders(self, 
                       symbol: Optional[str] = None,
                       order_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get open spot orders.
        
        Args:
            symbol: Symbol to filter orders (optional)
            order_id: Specific order ID to query (optional)
            
        Returns:
            Order information from Bybit
        """
        try:
            params = {'category': self.category}
            
            if order_id:
                params['orderId'] = order_id
            if symbol:
                params['symbol'] = symbol
                
            self.logger.info(f"Getting open spot orders with params: {params}")
            
            response = self.session.get_open_orders(**params)
            
            if response.get('retCode') == 0:
                orders = response['result']['list']
                self.logger.info(f"Retrieved {len(orders)} open spot orders")
                return {
                    'success': True,
                    'orders': orders,
                    'response': response
                }
            else:
                self.logger.error(f"Failed to get open orders. Response: {response}")
                return {
                    'success': False,
                    'error': response.get('retMsg', 'Unknown error'),
                    'response': response
                }
                
        except Exception as e:
            self.logger.error(f"Exception getting open orders: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_order_history(self, 
                         symbol: Optional[str] = None,
                         limit: int = 50) -> Dict[str, Any]:
        """
        Get spot order history.
        
        Args:
            symbol: Symbol to filter orders (optional)
            limit: Number of orders to retrieve (default 50)
            
        Returns:
            Historical order information from Bybit
        """
        try:
            params = {
                'category': self.category,
                'limit': limit
            }
            
            if symbol:
                params['symbol'] = symbol
                
            self.logger.info(f"Getting spot order history with params: {params}")
            
            response = self.session.get_order_history(**params)
            
            if response.get('retCode') == 0:
                orders = response['result']['list']
                self.logger.info(f"Retrieved {len(orders)} historical spot orders")
                return {
                    'success': True,
                    'orders': orders,
                    'response': response
                }
            else:
                self.logger.error(f"Failed to get order history. Response: {response}")
                return {
                    'success': False,
                    'error': response.get('retMsg', 'Unknown error'),
                    'response': response
                }
                
        except Exception as e:
            self.logger.error(f"Exception getting order history: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_spot_balance(self, coin: Optional[str] = None) -> Dict[str, Any]:
        """
        Get spot wallet balance.
        
        Args:
            coin: Specific coin to check balance (optional, e.g., 'BTC', 'USDT')
            
        Returns:
            Spot wallet balance information
        """
        try:
            # Testnet uses UNIFIED account type
            params = {'accountType': 'UNIFIED' if self.testnet else 'SPOT'}
            
            if coin:
                params['coin'] = coin
                
            self.logger.info(f"Getting spot balance for {coin if coin else 'all coins'}")
            
            response = self.session.get_wallet_balance(**params)
            
            if response.get('retCode') == 0:
                balance_data = response['result']['list'][0] if response['result']['list'] else {}
                
                # Extract coin balances
                coins = balance_data.get('coin', [])
                
                self.logger.info(f"Retrieved balance for {len(coins)} coins")
                return {
                    'success': True,
                    'coins': coins,
                    'total_equity': balance_data.get('totalEquity', '0'),
                    'response': response
                }
            else:
                self.logger.error(f"Failed to get spot balance. Response: {response}")
                return {
                    'success': False,
                    'error': response.get('retMsg', 'Unknown error'),
                    'response': response
                }
                
        except Exception as e:
            self.logger.error(f"Exception getting spot balance: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current ticker/price information for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            Ticker information including current price
        """
        try:
            self.logger.info(f"Getting ticker for {symbol}")
            
            response = self.session.get_tickers(
                category=self.category,
                symbol=symbol
            )
            
            if response.get('retCode') == 0:
                tickers = response['result']['list']
                if tickers:
                    ticker = tickers[0]
                    self.logger.info(f"Ticker for {symbol}: Price={ticker.get('lastPrice')}")
                    return {
                        'success': True,
                        'symbol': symbol,
                        'last_price': ticker.get('lastPrice'),
                        'bid': ticker.get('bid1Price'),
                        'ask': ticker.get('ask1Price'),
                        'volume_24h': ticker.get('volume24h'),
                        'response': response
                    }
                else:
                    return {
                        'success': False,
                        'error': f'No ticker data for {symbol}'
                    }
            else:
                self.logger.error(f"Failed to get ticker. Response: {response}")
                return {
                    'success': False,
                    'error': response.get('retMsg', 'Unknown error'),
                    'response': response
                }
                
        except Exception as e:
            self.logger.error(f"Exception getting ticker: {e}")
            return {
                'success': False,
                'error': str(e)
            }