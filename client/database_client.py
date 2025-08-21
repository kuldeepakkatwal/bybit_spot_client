"""
Database Client with Connection Pooling

This client handles ONLY database operations.
It's database-agnostic in design but currently implements PostgreSQL.
"""

import logging
import psycopg2
from psycopg2 import pool
from typing import Any, Dict, List, Optional, Tuple


class DatabaseClient:
    """
    A focused client for database operations with connection pooling.
    
    Features:
    - Connection pooling for efficiency
    - Execute queries (SELECT, INSERT, UPDATE, DELETE)
    - Create tables
    - Transaction support
    - Prepared statements
    """
    
    def __init__(self, 
                 dbname: str,
                 user: str,
                 password: str,
                 host: str = "localhost",
                 port: str = "5432",
                 min_connections: int = 1,
                 max_connections: int = 10):
        """
        Initialize the Database Client with connection pooling.
        
        Args:
            dbname: Database name
            user: Database user
            password: Database password
            host: Database host (default: localhost)
            port: Database port (default: 5432)
            min_connections: Minimum connections in pool
            max_connections: Maximum connections in pool
        """
        self.logger = logging.getLogger(__name__)
        
        self.db_params = {
            'dbname': dbname,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }
        
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.db_pool = None
        
        # Initialize connection pool
        self._init_pool()
    
    def _init_pool(self):
        """Initialize the database connection pool."""
        try:
            self.db_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.min_connections,
                maxconn=self.max_connections,
                **self.db_params
            )
            self.logger.info(f"Database connection pool established (min: {self.min_connections}, max: {self.max_connections})")
        except psycopg2.DatabaseError as e:
            self.logger.error(f"Failed to establish database connection pool: {e}")
            raise
    
    def execute_query(self, 
                     query: str,
                     params: Optional[Tuple] = None,
                     fetch: Optional[str] = None) -> Any:
        """
        Execute a SQL query using a connection from the pool.
        
        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)
            fetch: 'one' for fetchone, 'all' for fetchall, None for execute only
            
        Returns:
            Query results or None
        """
        conn = None
        try:
            # Get connection from pool
            conn = self.db_pool.getconn()
            
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                
                if fetch == 'one':
                    return cursor.fetchone()
                elif fetch == 'all':
                    return cursor.fetchall()
                else:
                    # For INSERT, UPDATE, DELETE
                    conn.commit()
                    return cursor.rowcount
                    
        except psycopg2.DatabaseError as e:
            self.logger.error(f"Database query failed: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            # Return connection to pool
            if conn:
                self.db_pool.putconn(conn)
    
    def create_table(self, 
                    table_name: str,
                    columns: List[str],
                    if_not_exists: bool = True) -> bool:
        """
        Create a database table.
        
        Args:
            table_name: Name of the table
            columns: List of column definitions
            if_not_exists: Add IF NOT EXISTS clause
            
        Returns:
            True if successful
        """
        try:
            exists_clause = "IF NOT EXISTS " if if_not_exists else ""
            columns_sql = ", ".join(columns)
            query = f"CREATE TABLE {exists_clause}{table_name} ({columns_sql});"
            
            self.execute_query(query)
            self.logger.info(f"Table '{table_name}' created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create table '{table_name}': {e}")
            return False
    
    def insert(self, 
              table_name: str,
              data: Dict[str, Any]) -> Optional[Any]:
        """
        Insert a record into a table.
        
        Args:
            table_name: Target table
            data: Dictionary of column:value pairs
            
        Returns:
            Number of rows affected or None if failed
        """
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["%s"] * len(data))
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders});"
            
            result = self.execute_query(query, tuple(data.values()))
            self.logger.info(f"Inserted record into '{table_name}'")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to insert into '{table_name}': {e}")
            return None
    
    def update(self, 
              table_name: str,
              data: Dict[str, Any],
              where_clause: str,
              where_params: Optional[Tuple] = None) -> Optional[int]:
        """
        Update records in a table.
        
        Args:
            table_name: Target table
            data: Dictionary of column:value pairs to update
            where_clause: WHERE clause (without 'WHERE' keyword)
            where_params: Parameters for WHERE clause
            
        Returns:
            Number of rows affected or None if failed
        """
        try:
            set_clause = ", ".join([f"{col} = %s" for col in data.keys()])
            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause};"
            
            params = tuple(data.values())
            if where_params:
                params += where_params
                
            result = self.execute_query(query, params)
            self.logger.info(f"Updated {result} rows in '{table_name}'")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to update '{table_name}': {e}")
            return None
    
    def select(self, 
              table_name: str,
              columns: Optional[List[str]] = None,
              where_clause: Optional[str] = None,
              where_params: Optional[Tuple] = None,
              order_by: Optional[str] = None,
              limit: Optional[int] = None) -> Optional[List[Tuple]]:
        """
        Select records from a table.
        
        Args:
            table_name: Target table
            columns: List of columns to select (default: all)
            where_clause: WHERE clause (without 'WHERE' keyword)
            where_params: Parameters for WHERE clause
            order_by: ORDER BY clause
            limit: LIMIT value
            
        Returns:
            List of tuples or None if failed
        """
        try:
            # Build SELECT clause
            select_cols = ", ".join(columns) if columns else "*"
            query = f"SELECT {select_cols} FROM {table_name}"
            
            # Add WHERE clause
            if where_clause:
                query += f" WHERE {where_clause}"
            
            # Add ORDER BY
            if order_by:
                query += f" ORDER BY {order_by}"
            
            # Add LIMIT
            if limit:
                query += f" LIMIT {limit}"
                
            query += ";"
            
            result = self.execute_query(query, where_params, fetch='all')
            self.logger.info(f"Selected {len(result) if result else 0} rows from '{table_name}'")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to select from '{table_name}': {e}")
            return None
    
    def delete(self, 
              table_name: str,
              where_clause: str,
              where_params: Optional[Tuple] = None) -> Optional[int]:
        """
        Delete records from a table.
        
        Args:
            table_name: Target table
            where_clause: WHERE clause (without 'WHERE' keyword)
            where_params: Parameters for WHERE clause
            
        Returns:
            Number of rows affected or None if failed
        """
        try:
            query = f"DELETE FROM {table_name} WHERE {where_clause};"
            
            result = self.execute_query(query, where_params)
            self.logger.info(f"Deleted {result} rows from '{table_name}'")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to delete from '{table_name}': {e}")
            return None
    
    def execute_transaction(self, queries: List[Tuple[str, Optional[Tuple]]]) -> bool:
        """
        Execute multiple queries in a transaction.
        
        Args:
            queries: List of (query, params) tuples
            
        Returns:
            True if all queries succeeded, False otherwise
        """
        conn = None
        try:
            conn = self.db_pool.getconn()
            
            with conn.cursor() as cursor:
                for query, params in queries:
                    cursor.execute(query, params)
                    
                conn.commit()
                self.logger.info(f"Transaction completed successfully ({len(queries)} queries)")
                return True
                
        except psycopg2.DatabaseError as e:
            self.logger.error(f"Transaction failed: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.db_pool.putconn(conn)
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists.
        
        Args:
            table_name: Table name to check
            
        Returns:
            True if table exists, False otherwise
        """
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """
        result = self.execute_query(query, (table_name,), fetch='one')
        return result[0] if result else False
    
    def get_connection_pool_status(self) -> Dict[str, Any]:
        """
        Get the status of the connection pool.
        
        Returns:
            Dictionary with pool statistics
        """
        if self.db_pool:
            return {
                'min_connections': self.min_connections,
                'max_connections': self.max_connections,
                'closed': self.db_pool.closed
            }
        return {'status': 'Pool not initialized'}
    
    def close(self):
        """Close all connections in the pool."""
        if self.db_pool:
            self.db_pool.closeall()
            self.logger.info("Database connection pool closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()