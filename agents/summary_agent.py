"""
Agent 4: Summary/Analysis Agent

Goal: Provide executive summary combining data from all other agents.

This agent:
- Queries data from all tables (autos_hyd, dc_chargers_hyd)
- Combines metrics from multiple agents
- Provides high-level insights and statistics
- Generates comprehensive summary reports
"""

import sqlite3
from datetime import datetime
from typing import Dict, Optional

from .base_agent import BaseAgent


class SummaryAgent(BaseAgent):
    """
    Agent responsible for aggregating and summarizing data from all other agents.
    Inherits from BaseAgent for common database and logging functionality.
    """

    def __init__(self, db_path: str, config: Optional[Dict] = None):
        """
        Initialize the Summary Agent.

        Args:
            db_path: Path to SQLite database
            config: Optional configuration dictionary
        """
        super().__init__(db_path, config, agent_name="SummaryAgent")

    def get_auto_statistics(self) -> Dict:
        """
        Get statistics about autos in the system.

        Returns:
            Dictionary with auto statistics
        """
        cursor = self.conn.cursor()

        # Total autos
        cursor.execute("SELECT COUNT(*) as count FROM autos_hyd")
        total_autos = cursor.fetchone()['count']

        # Retrofitted autos
        cursor.execute(
            "SELECT COUNT(*) as count FROM autos_hyd WHERE retrofit_status = 'retrofitted'"
        )
        retrofitted_autos = cursor.fetchone()['count']

        # Eligible autos (retrofittable)
        cursor.execute("SELECT COUNT(*) as count FROM autos_hyd WHERE is_retrofittable = 1")
        eligible_autos = cursor.fetchone()['count']

        return {
            'total_autos': total_autos,
            'retrofitted_autos': retrofitted_autos,
            'eligible_autos': eligible_autos,
        }

    def get_charger_statistics(self) -> Dict:
        """
        Get statistics about chargers in the system.

        Returns:
            Dictionary with charger statistics
        """
        cursor = self.conn.cursor()

        # Total chargers
        cursor.execute("SELECT COUNT(*) as count FROM dc_chargers_hyd")
        total_chargers = cursor.fetchone()['count']

        # Total capacity
        cursor.execute(
            "SELECT SUM(power_kw) as total FROM dc_chargers_hyd WHERE power_kw IS NOT NULL"
        )
        result = cursor.fetchone()
        total_capacity_kw = result['total'] if result and result['total'] else 0.0

        return {
            'total_chargers': total_chargers,
            'total_capacity_kw': total_capacity_kw,
        }

    def get_summary_report(self) -> str:
        """
        Generate comprehensive summary report.

        Returns:
            Formatted summary report string
        """
        auto_stats = self.get_auto_statistics()
        charger_stats = self.get_charger_statistics()

        report = f"""
SUMMARY REPORT - SURYA CHAKRA PROJECT
{'='*70}

AUTO STOCK OVERVIEW:
  Total autos in system:                    {auto_stats['total_autos']:,}
  Eligible autos (10+ years old):           {auto_stats['eligible_autos']:,}
  Already retrofitted autos:                {auto_stats['retrofitted_autos']:,}

CHARGING INFRASTRUCTURE:
  Total DC chargers available:              {charger_stats['total_chargers']:,}
  Total charging capacity:                  {charger_stats['total_capacity_kw']:.1f} kW

KEY METRICS:
  Retrofit eligible autos vs capacity:      {auto_stats['eligible_autos']} autos / 120,000 capacity
  Current retrofit rate:                    {(auto_stats['retrofitted_autos'] / max(auto_stats['eligible_autos'], 1) * 100):.1f}% (if eligible autos exist)

Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return report


def run(db_path: str, config: Optional[Dict] = None):
    """
    Main entry point for the Summary Agent.

    Args:
        db_path: Path to SQLite database
        config: Optional configuration dictionary
    """
    with SummaryAgent(db_path, config) as agent:
        agent.log_info("Starting Summary Agent")

        # Generate and log summary report
        report = agent.get_summary_report()
        agent.log_info(f"\n{report}")

        agent.log_info("Summary Agent completed successfully")


if __name__ == "__main__":
    # For direct execution (testing)
    run("data/processed/surya.db")
