import math
import pandas as pd
import plotly.express as px
import streamlit as st
from dataclasses import dataclass
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent / "scripts"))
from ev_model import EVModel


@dataclass
class SimpleAssumptions:
    petrol_price: float
    diesel_price: float
    electricity_price: float
    petrol_mileage: float
    diesel_mileage: float
    daily_km: int
    working_days_per_month: int
    ola_fare: float
    uber_fare: float
    rapido_fare: float


def build_assumptions() -> SimpleAssumptions:
    return SimpleAssumptions(
        petrol_price=115.69,
        diesel_price=103.82,
        electricity_price=10.0,
        petrol_mileage=40.0,
        diesel_mileage=40.0,
        daily_km=100,
        working_days_per_month=25,
        ola_fare=8.0,
        uber_fare=13.0,
        rapido_fare=10.0,
    )


def build_tables(assumptions: SimpleAssumptions) -> tuple[pd.DataFrame, pd.DataFrame]:
    daily_km = assumptions.daily_km
    monthly_km = assumptions.daily_km * assumptions.working_days_per_month
    ev_model = EVModel()

    petrol_cost_per_km = assumptions.petrol_price / assumptions.petrol_mileage
    diesel_cost_per_km = assumptions.diesel_price / assumptions.diesel_mileage
    ev_cost_per_km = assumptions.electricity_price / ev_model.efficiency_km_per_kwh

    platform_rows = [
        {
            "Platform": "Ola",
            "Price per km (₹)": round(assumptions.ola_fare, 2),
            "Daily cost for 100 km (₹)": round(assumptions.ola_fare * daily_km, 2),
            "Monthly cost for 25 days (₹)": round(assumptions.ola_fare * monthly_km, 2),
        },
        {
            "Platform": "Uber",
            "Price per km (₹)": round(assumptions.uber_fare, 2),
            "Daily cost for 100 km (₹)": round(assumptions.uber_fare * daily_km, 2),
            "Monthly cost for 25 days (₹)": round(assumptions.uber_fare * monthly_km, 2),
        },
        {
            "Platform": "Rapido",
            "Price per km (₹)": round(assumptions.rapido_fare, 2),
            "Daily cost for 100 km (₹)": round(assumptions.rapido_fare * daily_km, 2),
            "Monthly cost for 25 days (₹)": round(assumptions.rapido_fare * monthly_km, 2),
        },
    ]

    fuel_rows = [
        {
            "Fuel type": "Petrol",
            "Price": f"₹{assumptions.petrol_price:.2f}/L",
            "Range efficiency": f"~{assumptions.petrol_mileage:.1f} km/L",
            "Max distance with full tank (km)": round(8 * assumptions.petrol_mileage, 1),
            "Fuel cost for full tank (₹)": round(8 * assumptions.petrol_price, 2),
            "Cost per km (₹)": round(petrol_cost_per_km, 2),
            "Daily cost for 100 km (₹)": round(petrol_cost_per_km * daily_km, 2),
            "Monthly cost for 25 days (₹)": round(petrol_cost_per_km * monthly_km, 2),
        },
        {
            "Fuel type": "Diesel",
            "Price": f"₹{assumptions.diesel_price:.2f}/L",
            "Range efficiency": f"~{assumptions.diesel_mileage:.1f} km/L",
            "Max distance with full tank (km)": round(8 * assumptions.diesel_mileage, 1),
            "Fuel cost for full tank (₹)": round(8 * assumptions.diesel_price, 2),
            "Cost per km (₹)": round(diesel_cost_per_km, 2),
            "Daily cost for 100 km (₹)": round(diesel_cost_per_km * daily_km, 2),
            "Monthly cost for 25 days (₹)": round(diesel_cost_per_km * monthly_km, 2),
        },
        {
            "Fuel type": "EV",
            "Price": f"₹{assumptions.electricity_price:.2f}/kWh",
            "Range efficiency": f"~{ev_model.efficiency_km_per_kwh:.1f} km/kWh",
            "Max distance with full charge (km)": round(ev_model.range_practical(), 1),
            "Charging cost for full charge (₹)": round(ev_model.charging_cost(0, 100, assumptions.electricity_price), 2),
            "Cost per km (₹)": round(ev_cost_per_km, 2),
            "Daily cost for 100 km (₹)": round(ev_cost_per_km * daily_km, 2),
            "Monthly cost for 25 days (₹)": round(ev_cost_per_km * monthly_km, 2),
        },
    ]

    return pd.DataFrame(platform_rows), pd.DataFrame(fuel_rows)


def build_compared_chart(assumptions: SimpleAssumptions, period: str) -> px.bar:
    daily_km = assumptions.daily_km
    monthly_km = assumptions.daily_km * assumptions.working_days_per_month
    ev_model = EVModel()

    petrol_cost_per_km = assumptions.petrol_price / assumptions.petrol_mileage
    diesel_cost_per_km = assumptions.diesel_price / assumptions.diesel_mileage
    ev_cost_per_km = assumptions.electricity_price / ev_model.efficiency_km_per_kwh

    if period == "daily":
        income_values = {
            "Ola": assumptions.ola_fare * daily_km,
            "Uber": assumptions.uber_fare * daily_km,
            "Rapido": assumptions.rapido_fare * daily_km,
        }
        fuel_values = {
            "Petrol": petrol_cost_per_km * daily_km,
            "Diesel": diesel_cost_per_km * daily_km,
            "EV": ev_cost_per_km * daily_km,
        }
        title = "Daily profit by platform"
        y_axis = "Daily amount (₹)"
    else:
        income_values = {
            "Ola": assumptions.ola_fare * monthly_km,
            "Uber": assumptions.uber_fare * monthly_km,
            "Rapido": assumptions.rapido_fare * monthly_km,
        }
        fuel_values = {
            "Petrol": petrol_cost_per_km * monthly_km,
            "Diesel": diesel_cost_per_km * monthly_km,
            "EV": ev_cost_per_km * monthly_km,
        }
        title = "Monthly profit by platform"
        y_axis = "Monthly amount (₹)"

    rows = []
    for platform in ["Ola", "Uber", "Rapido"]:
        profit_petrol = income_values[platform] - fuel_values["Petrol"]
        profit_diesel = income_values[platform] - fuel_values["Diesel"]
        profit_ev = income_values[platform] - fuel_values["EV"]
        rows.append({"Platform": platform, "Metric": "Petrol Engine", y_axis: profit_petrol})
        rows.append({"Platform": platform, "Metric": "Diesel Engine", y_axis: profit_diesel})
        rows.append({"Platform": platform, "Metric": "Electric Vehicle", y_axis: profit_ev})

    chart_df = pd.DataFrame(rows)
    fig = px.bar(
        chart_df,
        x="Platform",
        y=y_axis,
        color="Metric",
        barmode="group",
        color_discrete_map={
            "Petrol Engine": "#e74c3c",
            "Diesel Engine": "#f39c12",
            "Electric Vehicle": "#2ecc71",
        },
    )
    fig.update_layout(title=title, xaxis_title="Platform", yaxis_title=y_axis, template="plotly_white")
    return fig


def main() -> None:
    st.set_page_config(page_title="EV Retrofit Economics", page_icon="⚡", layout="wide")
    st.title("EV Retrofit Economics")
    st.caption("Simple comparison of platform prices, fuel cost, range efficiency, and daily/monthly running cost for a 100 km daily drive.")

    assumptions = build_assumptions()
    platform_df, fuel_df = build_tables(assumptions)

    st.subheader("Platform price comparison")
    st.dataframe(platform_df, width="stretch", hide_index=True)

    st.subheader("Fuel price and range efficiency")
    st.dataframe(fuel_df, width="stretch", hide_index=True)

    ev_model = EVModel()
    distance_km = assumptions.daily_km
    energy_needed_kwh = ev_model.energy_needed_for_distance(distance_km)
    charge_cost = assumptions.electricity_price * energy_needed_kwh
    charges_needed = math.ceil(distance_km / ev_model.range_practical())

    with st.container():
        st.subheader("EV model summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Battery capacity", f"{ev_model.battery_capacity_kwh:.1f} kWh")
        with col2:
            st.metric("Practical range", f"{ev_model.range_practical():.1f} km")
        with col3:
            st.metric("Energy for {distance_km} km".format(distance_km=distance_km), f"{energy_needed_kwh:.2f} kWh")
        with col4:
            st.metric("Charges needed", f"{charges_needed}")
        st.caption(f"Cost to drive {distance_km} km: ₹{charge_cost:.2f} | Full-charge cost: ₹{ev_model.charging_cost(0, 100, assumptions.electricity_price):.2f}")

    st.subheader("Daily expenditure vs platform income")
    st.plotly_chart(build_compared_chart(assumptions, "daily"))

    st.subheader("Monthly expenditure vs platform income")
    st.plotly_chart(build_compared_chart(assumptions, "monthly"))

    st.info("Petrol and diesel both use 40 km/L efficiency with an 8 L tank. EV range efficiency is assumed at 7 km per kWh. Daily and monthly costs use the fixed 100 km/day and 25 working days/month inputs.")


if __name__ == "__main__":
    main()
