import streamlit as st

st.set_page_config(page_title="SuryaChakra Pricing Dashboard", page_icon="⚡", layout="wide")

st.title("SuryaChakra Pricing Dashboard")
st.write("Estimate a price point for the retrofit and charging ecosystem based on hardware cost, service margin, and target monthly savings.")

st.sidebar.header("Assumptions")

retrofit_cost = st.sidebar.number_input("Retrofit hardware cost (₹)", min_value=0.0, value=180000.0, step=1000.0)
charger_cost = st.sidebar.number_input("Portable charger cost (₹)", min_value=0.0, value=95000.0, step=1000.0)
solar_cost = st.sidebar.number_input("Solar range extender cost (₹)", min_value=0.0, value=50000.0, step=1000.0)
markup_percent = st.sidebar.slider("Target markup (%)", min_value=0.0, max_value=100.0, value=25.0, step=1.0)
service_margin_percent = st.sidebar.slider("Service margin (%)", min_value=0.0, max_value=100.0, value=15.0, step=1.0)
monthly_savings = st.sidebar.number_input("Estimated monthly savings for customer (₹)", min_value=0.0, value=6000.0, step=500.0)
target_payback_months = st.sidebar.number_input("Target payback period (months)", min_value=1, value=18, step=1)

# Build total system cost and price targets
system_cost = retrofit_cost + charger_cost + solar_cost
markup = system_cost * (markup_percent / 100.0)
service_margin = system_cost * (service_margin_percent / 100.0)
price_with_markup = system_cost + markup
price_with_service_margin = system_cost + service_margin
price_for_payback = monthly_savings * target_payback_months

# Give a recommended price point that satisfies both markup and payback
recommended_price = max(price_with_markup, price_with_service_margin, price_for_payback)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("System cost", f"₹{system_cost:,.0f}")
with col2:
    st.metric("Price with markup", f"₹{price_with_markup:,.0f}")
with col3:
    st.metric("Payback-based target", f"₹{price_for_payback:,.0f}")

st.subheader("Recommended price point")
st.info(f"A practical price point target is around ₹{recommended_price:,.0f}.")

st.markdown("### How the calculation works")
st.markdown("- The dashboard sums the retrofit kit, portable charger, and solar extender costs.")
st.markdown("- It applies the selected markup and service margin to set a commercial price ceiling/floor.")
st.markdown("- It also estimates a payback-based target using the monthly savings and the targeted payback period.")
st.markdown("- The recommended price is the highest of the three values so it stays commercially viable and financially attractive.")
