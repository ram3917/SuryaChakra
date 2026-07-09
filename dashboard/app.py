# app.py
import os
import sqlite3

import pandas as pd
import streamlit as st

DB_PATH = "data/processed/surya.db"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_connection(db_path: str) -> sqlite3.Connection:
	"""Return a cached SQLite connection.

	The connection is cached by Streamlit so that the database is opened only
	once per session. ``check_same_thread=False`` allows the connection to be
	reused across Streamlit's reruns.
	"""
	return sqlite3.connect(db_path, check_same_thread=False)


def load_table(table_name: str) -> pd.DataFrame:
	"""Load a table from the SQLite database into a pandas DataFrame."""
	conn = get_connection(DB_PATH)
	df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
	conn.close()
	return df


def table_summary(df: pd.DataFrame) -> pd.DataFrame:
	"""Return a simple summary (count, unique, missing) for each column."""
	summary = pd.DataFrame({
		"count": df.count(),
		"unique": df.nunique(),
		"missing": df.isna().sum(),
	})
	return summary


# ---------------------------------------------------------------------------
# Streamlit layout
# ---------------------------------------------------------------------------
st.set_page_config(page_title="SuryaChakra Data Dashboard", layout="wide")
st.title("SuryaChakra – SQLite Data Overview")

# List of tables we want to explore
tables = [
	"autos_hyd",
	"retrofit_capacity_tracking",
	"retrofit_subsidies",
	"dc_chargers_hyd",
	"charger_availability",
]

selected_table = st.selectbox("Select a table to explore", tables)

df = load_table(selected_table)
st.subheader(f"{selected_table} – raw data (first 200 rows)")
st.dataframe(df.head(200))

st.subheader("Column summary")
st.dataframe(table_summary(df))

# ---------------------------------------------------------------------------
# Simple visualisations for key tables
# ---------------------------------------------------------------------------
if selected_table == "autos_hyd":
	st.subheader("Distribution of fuel types")
	fuel_counts = df["fuel_type"].value_counts().reset_index()
	fuel_counts.columns = ["fuel_type", "count"]
	st.bar_chart(fuel_counts.set_index("fuel_type"))

	st.subheader("Retrofit status")
	retrofit_counts = df["retrofit_status"].value_counts().reset_index()
	retrofit_counts.columns = ["status", "count"]
	st.bar_chart(retrofit_counts.set_index("status"))

elif selected_table == "dc_chargers_hyd":
	st.subheader("Charger power (kW) distribution")
	# Show distribution of charger power using value counts
	power_counts = df["power_kw"].dropna().value_counts().reset_index()
	power_counts.columns = ["power_kw", "count"]
	st.bar_chart(power_counts.set_index("power_kw"))

	st.subheader("Geographic locations (map)")
	if "lat" in df.columns and "lon" in df.columns:
		st.map(df[["lat", "lon"]].dropna())

elif selected_table == "charger_availability":
	st.subheader("Availability of chargers")
	availability = df.groupby("charger_id")["available_slots"].sum().reset_index()
	st.bar_chart(availability.set_index("charger_id"))

elif selected_table == "retrofit_subsidies":
	st.subheader("Subsidy amounts")
	st.bar_chart(df["subsidy_amount"].dropna())

elif selected_table == "retrofit_capacity_tracking":
	st.subheader("Retrofit capacity by region and auto type")
	pivot = df.pivot_table(
		index="region",
		columns="auto_type",
		values="capacity",
		aggfunc="sum",
		fill_value=0,
	)
	st.dataframe(pivot)


