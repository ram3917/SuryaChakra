# agents/auto_stock_agent.py
from typing import Dict, Any
import os
import sqlite3

import pandas as pd
import requests


class AutoStockAgent:
    """
    Builds/refreshes autos_stock_hyderabad from Telangana RTA open data.

    Output table:
      - autos_stock_hyderabad(year, region, vehicle_class, count)
    """

    def __init__(self, db_path: str, config: Dict[str, Any]):
        self.db_path = db_path
        self.config = config

    def run(self) -> None:
        # 1. Ensure raw data folder exists
        raw_dir = "data/raw"
        os.makedirs(raw_dir, exist_ok=True)

        # 2. Download latest RTA dataset CSV (or reuse cached)
        csv_path = self._download_rta_csv(raw_dir)

        # 3. Load CSV into DataFrame
        df = pd.read_csv(csv_path)

        # 4. Filter to Hyderabad RTOs and 3W auto-rickshaws
        df_hyd = self._filter_hyderabad_autos(df)

        # 5. Aggregate by year and region
        stock_df = self._aggregate_by_year_region(df_hyd)

        # 6. Write/refresh table in SQLite
        self._write_to_db(stock_df)

    def _download_rta_csv(self, raw_dir: str) -> str:
        """
        Download the latest Telangana RTA vehicle registrations dataset.

        For stability, save to a fixed filename so downstream code doesn't change:
          data/raw/telangana_rta_vehicle_registrations_latest.csv

        If you prefer, you can also include a date suffix.
        """
        url = self.config["auto_stock"]["rta_csv_url"]
        csv_path = os.path.join(raw_dir, "telangana_rta_vehicle_registrations_latest.csv")

        resp = requests.get(url, timeout=60)
        resp.raise_for_status()

        with open(csv_path, "wb") as f:
            f.write(resp.content)

        return csv_path

    def _filter_hyderabad_autos(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter RTA dataset to Hyderabad RTO codes and auto-rickshaw vehicle classes.

        You MUST adapt 'rto_code', 'vehicle_class', and class values
        once you inspect the actual dataset columns and values.
        """
        # Example column names; adjust to reality
        rto_col = "RTA_OFFICE_CODE"      # or similar
        class_col = "VEHICLE_CLASS"      # or similar

        # Hyderabad RTO codes (example set; confirm from dataset/docs)
        hyd_rtos = [
            "TS07",  # Hyderabad
            "TS08",
            "TS09",
            "TS10",  # Hyderabad North
            "TS11",  # Hyderabad South
            "TS13",  # Hyderabad Central
            "TS14",  # Hyderabad
        ]

        df_hyd = df[df[rto_col].isin(hyd_rtos)].copy()

        # Filter to 3W passenger autos (inspect dataset to confirm exact values)
        auto_classes = [
            "3W-PASSENGER",
            "LMV-3W-PASSENGER",
            "AUTO RICKSHAW",
            # add/adjust based on actual values
        ]
        df_hyd = df_hyd[df_hyd[class_col].isin(auto_classes)].copy()

        return df_hyd

    def _aggregate_by_year_region(self, df_hyd: pd.DataFrame) -> pd.DataFrame:
        """
        Parse registration date to year and group counts by year and region.
        """
        # Example column name; adjust to dataset
        date_col = "REGISTRATION_DATE"

        df_hyd[date_col] = pd.to_datetime(df_hyd[date_col], errors="coerce")
        df_hyd = df_hyd.dropna(subset=[date_col])

        df_hyd["year"] = df_hyd[date_col].dt.year

        # Treat all Hyderabad RTOs as a single region for now
        df_hyd["region"] = "Hyderabad_total"
        df_hyd["vehicle_class_norm"] = "3W_auto_passenger"

        stock_df = (
            df_hyd
            .groupby(["year", "region", "vehicle_class_norm"], as_index=False)
            .size()
            .rename(columns={"size": "count"})
        )

        stock_df.rename(columns={"vehicle_class_norm": "vehicle_class"}, inplace=True)
        return stock_df

    def _write_to_db(self, stock_df: pd.DataFrame) -> None:
        """
        Create/replace autos_stock_hyderabad table in the SQLite DB.
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS autos_stock_hyderabad (
                year INTEGER,
                region TEXT,
                vehicle_class TEXT,
                count INTEGER
            )
            """
        )

        # Idempotent: clear and insert fresh data each run
        cur.execute("DELETE FROM autos_stock_hyderabad")

        stock_df.to_sql(
            "autos_stock_hyderabad",
            conn,
            if_exists="append",
            index=False,
        )

        conn.commit()
        conn.close()