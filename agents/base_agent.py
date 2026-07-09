"""
Base Agent class for SuryaChakra project.
Provides common functionality for all agents including database management, logging, and configuration access.
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any


class BaseAgent:
    """
    Base class for all SuryaChakra agents.
    Provides common functionality for database management, logging, and configuration handling.
    """

    def __init__(self, db_path: str, config: Optional[Dict] = None, agent_name: str = "BaseAgent"):
        """
        Initialize the base agent.

        Args:
            db_path: Path to SQLite database
            config: Optional configuration dictionary from YAML
            agent_name: Name of the agent for logging
        """
        self.db_path = db_path
        self.config = config or {}
        self.agent_name = agent_name
        self.conn = None
        self.logger = self._setup_logging()
        self._initialize_database()

    def _setup_logging(self) -> logging.Logger:
        """
        Set up logging for the agent.

        Returns:
            Logger instance configured for this agent
        """
        logger = logging.getLogger(self.__class__.__name__)

        # Only add handler if logger doesn't already have one
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    def _initialize_database(self):
        """Initialize or connect to the SQLite database."""
        try:
            # Create data directory if it doesn't exist
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            # Get database timeout from config if available
            db_timeout = 30  # default
            if 'database' in self.config and 'timeout' in self.config['database']:
                db_timeout = self.config['database']['timeout']

            self.conn = sqlite3.connect(self.db_path, timeout=db_timeout)
            self.conn.row_factory = sqlite3.Row

            self.logger.info(f"{self.agent_name} connected to database: {self.db_path}")
        except sqlite3.Error as e:
            self.logger.error(f"Database connection error: {e}")
            raise

    def get_config(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key_path: Dot-separated path to the value (e.g., 'agent_auto_stock.min_age_years')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def get_agent_config(self) -> Dict:
        """
        Get this agent's specific configuration.

        Returns:
            Dictionary with agent configuration
        """
        # Extract agent name from class name (e.g., AutoStockRetrofitAgent -> auto_stock)
        agent_key = f"agent_{self.agent_name.replace('Agent', '').lower()}"
        return self.get_config(agent_key, {})

    def execute_query(self, query: str, params: tuple = None, fetch_one: bool = False):
        """
        Execute a SQL query.

        Args:
            query: SQL query string
            params: Query parameters
            fetch_one: If True, return single row; if False, return all rows

        Returns:
            Query result or None
        """
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch_one:
                return cursor.fetchone()
            else:
                return cursor.fetchall()
        except sqlite3.Error as e:
            self.logger.error(f"Query execution error: {e}")
            raise

    def commit(self):
        """Commit database changes."""
        if self.conn:
            try:
                self.conn.commit()
            except sqlite3.Error as e:
                self.logger.error(f"Commit error: {e}")
                raise

    def get_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.

        Returns:
            ISO format timestamp string
        """
        return datetime.now().isoformat()

    def log_info(self, message: str):
        """Log info message."""
        self.logger.info(message)

    def log_warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)

    def log_error(self, message: str):
        """Log error message."""
        self.logger.error(message)

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            self.logger.error(f"Error checking table existence: {e}")
            return False

    def get_table_count(self, table_name: str) -> int:
        """
        Get the number of rows in a table.

        Args:
            table_name: Name of the table

        Returns:
            Number of rows in the table
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            result = cursor.fetchone()
            return result['count'] if result else 0
        except sqlite3.Error as e:
            self.logger.error(f"Error counting table rows: {e}")
            return 0

    def close(self):
        """Close database connection."""
        if self.conn:
            try:
                self.conn.close()
                self.logger.info(f"{self.agent_name} database connection closed")
            except sqlite3.Error as e:
                self.logger.error(f"Error closing database: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
