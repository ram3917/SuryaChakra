"""
Agent 3: DC Charger Locator Agent

Goal: Map where public DC chargers are located and build infrastructure data.

This agent:
- Fetches public DC charger locations from sources.yaml
- Normalizes data into a dc_chargers_hyd table
- Stores charger properties (location, power, connector type)
- Answers questions about charging infrastructure coverage
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd

from .base_agent import BaseAgent
from .fetch_data import FetchData

class DCChargerLocatorAgent(BaseAgent):
    """
    Agent responsible for building and maintaining DC charger location and infrastructure data.
    Inherits from BaseAgent for common database and logging functionality.
    """

    # Connector types for DC charging
    CONNECTOR_TYPES = ['Bharat DC', 'CCS', 'CHAdeMO']

    # Location types
    LOCATION_TYPES = ['park', 'rto', 'petrol_pump', 'mall', 'roadside', 'railway_station']

    # Zones in Hyderabad
    ZONES = ['inside_orr', 'outside_orr']

    def __init__(self, db_path: str, config: Optional[Dict] = None):
        """
        Initialize the DC Charger Locator agent.

        Args:
            db_path: Path to SQLite database
            config: Optional configuration dictionary
        """
        super().__init__(db_path, config, agent_name="DCChargerLocatorAgent")
        self._create_tables()

    def _create_tables(self):
        """Create required tables if they don't exist."""
        cursor = self.conn.cursor()

        # Main DC chargers table - simplified
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dc_chargers_hyd (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                lat REAL,
                lon REAL,
                power_kw REAL,
                connector_type TEXT
            )
        """)

        self.conn.commit()
        self.logger.info("Database tables initialized successfully")

    def add_charger(
        self,
        name: str,
        lat: float,
        lon: float,
        power_kw: Optional[float] = None,
        connector_type: Optional[str] = None
    ) -> bool:
        """
        Add or update a DC charger record in the database.

        Args:
            name: Name of the charger location
            lat: Latitude coordinate
            lon: Longitude coordinate
            power_kw: Power capacity in kW
            connector_type: Type of connector (Bharat DC, CCS, CHAdeMO)

        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO dc_chargers_hyd
                (name, lat, lon, power_kw, connector_type)
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                lat,
                lon,
                power_kw,
                connector_type.lower() if connector_type else None
            ))
            self.commit()
            return True
        except sqlite3.Error as e:
            self.log_error(f"Error adding charger {name}: {e}")
            return False

    def bulk_add_chargers(self, chargers_data: List[Dict]) -> Tuple[int, int]:
        """
        Add multiple DC chargers from a list of dictionaries.

        Args:
            chargers_data: List of dictionaries with charger information

        Returns:
            Tuple of (successful_count, failed_count)
        """
        successful = 0
        failed = 0

        for charger in chargers_data:
            if self.add_charger(**charger):
                successful += 1
            else:
                failed += 1

        self.log_info(f"Bulk add completed: {successful} successful, {failed} failed")
        return successful, failed

    def load_from_csv(self, csv_path: str) -> Tuple[int, int]:
        """
        Load charger data from a CSV file.

        Args:
            csv_path: Path to CSV file with columns:
                     name, lat, lon, power_kw, connector_type, operator, location_type, location_zone, address

        Returns:
            Tuple of (successful_count, failed_count)
        """
        try:
            df = pd.read_csv(csv_path)
            chargers_data = df.to_dict('records')
            return self.bulk_add_chargers(chargers_data)
        except Exception as e:
            self.log_error(f"Error loading CSV {csv_path}: {e}")
            return 0, 0

    def get_charger_count(self) -> int:
        """
        Get total count of DC chargers.

        Returns:
            Count of chargers
        """
        cursor = self.conn.cursor()
        query = "SELECT COUNT(*) as count FROM dc_chargers_hyd"
        cursor.execute(query)
        result = cursor.fetchone()
        return result['count'] if result else 0

    def get_total_capacity_kw(self) -> float:
        """
        Get total charging capacity in kW.

        Returns:
            Total capacity in kW
        """
        cursor = self.conn.cursor()
        query = "SELECT SUM(power_kw) as total FROM dc_chargers_hyd WHERE power_kw IS NOT NULL"
        cursor.execute(query)
        result = cursor.fetchone()
        return result['total'] if result and result['total'] else 0.0

    def get_chargers_by_connector(self, connector_type: str) -> int:
        """
        Get count of chargers by connector type.

        Args:
            connector_type: Type of connector

        Returns:
            Count of chargers with the specified connector type
        """
        cursor = self.conn.cursor()
        query = "SELECT COUNT(*) as count FROM dc_chargers_hyd WHERE connector_type = ?"
        cursor.execute(query, [connector_type.lower()])
        result = cursor.fetchone()
        return result['count'] if result else 0

    def get_charger_distribution(self) -> Dict[str, int]:
        """
        Get distribution of chargers by connector type.

        Returns:
            Dictionary with connector type counts
        """
        cursor = self.conn.cursor()
        query = "SELECT connector_type, COUNT(*) as count FROM dc_chargers_hyd GROUP BY connector_type"
        cursor.execute(query)
        results = cursor.fetchall()
        return {row['connector_type']: row['count'] for row in results if row['connector_type']}

    def export_to_csv(self, output_path: str) -> bool:
        """
        Export charger data to CSV file.

        Args:
            output_path: Path to output CSV file

        Returns:
            True if successful, False otherwise
        """
        try:
            query = "SELECT * FROM dc_chargers_hyd"
            df = pd.read_sql_query(query, self.conn)
            df.to_csv(output_path, index=False)
            self.log_info(f"Exported {len(df)} chargers to {output_path}")
            return True
        except Exception as e:
            self.log_error(f"Error exporting to CSV: {e}")
            return False

    def get_summary_report(self) -> str:
        """
        Generate a text summary report.

        Returns:
            Formatted summary report string
        """
        total_count = self.get_charger_count()
        total_capacity = self.get_total_capacity_kw()
        connector_dist = self.get_charger_distribution()

        report = f"""
DC CHARGER LOCATOR AGENT - SUMMARY REPORT
{'='*70}

CHARGER COVERAGE:
  Total DC chargers:                        {total_count}

TOTAL CAPACITY:
  Total charging capacity:                  {total_capacity:.1f} kW

CHARGER DISTRIBUTION BY CONNECTOR TYPE:
"""
        for connector_type, count in sorted(connector_dist.items(), key=lambda x: x[1], reverse=True):
            report += f"  {connector_type:20}                    {count:,}\n"

        report += f"\nReport generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        return report


def run(db_path: str, config: Optional[Dict] = None):
    """
    Main entry point for the DC Charger Locator Agent.

    Args:
        db_path: Path to SQLite database
        config: Optional configuration dictionary
    """
    with DCChargerLocatorAgent(db_path, config) as agent:
        agent.log_info("Starting DC Charger Locator Agent")

        # Fetch data from sources.yaml with LLM extraction
        agent.log_info("Fetching and extracting charger data from sources...")
        try:
            fetcher = FetchData()
            raw_chargers = fetcher.fetch_and_extract_chargers()
            
            if raw_chargers:
                # Validate and parse
                sample_chargers = fetcher.parse_charger_data(raw_chargers)
                agent.log_info(f"Extracted {len(raw_chargers)} records, validated {len(sample_chargers)}")
            else:
                agent.log_info("No charger data extracted from sources")
                sample_chargers = []
        except Exception as e:
            agent.log_info(f"Error fetching charger data: {e}")
            sample_chargers = []

        if sample_chargers:
            success_count, fail_count = agent.bulk_add_chargers(sample_chargers)
            agent.log_info(f"Data loaded: {success_count} chargers added, {fail_count} failed")
        else:
            agent.log_info("No charger data to load")

        # Generate and log summary report
        report = agent.get_summary_report()
        agent.log_info(f"\n{report}")

        agent.log_info("DC Charger Locator Agent completed successfully")


if __name__ == "__main__":
    # For direct execution (testing)
    run("data/processed/surya.db")
