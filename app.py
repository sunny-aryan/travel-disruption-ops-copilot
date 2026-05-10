import streamlit as st


st.set_page_config(
    page_title="Travel Disruption Ops Copilot",
    page_icon="🚆",
    layout="wide",
)

st.title("Travel Disruption Operations Copilot")

st.markdown(
    """
    A product-grade operations console for managing disrupted travel bookings.

    This project explores how AI-assisted workflows, deterministic policy controls,
    external dependency handling, and human feedback loops can support travel
    operations teams during delays, cancellations, and rebooking scenarios.
    """
)

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Open disruption cases", "0")

with col2:
    st.metric("SLA risk cases", "0")

with col3:
    st.metric("Provider status", "Not connected")

st.info(
    "Project foundation is ready. Next step: add synthetic disruption cases and a prioritized operations queue."
)