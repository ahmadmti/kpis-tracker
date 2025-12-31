import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from api_client import API_BASE, api_headers

st.set_page_config(page_title="My KPIs", layout="wide")

st.title("🎯 My KPIs")

# Get current user
user_resp = requests.get(f"{API_BASE}/users/me", headers=api_headers())
if user_resp.status_code != 200:
    st.error("Failed to load user data")
    st.stop()

current_user = user_resp.json()

# Fetch KPIs for user's role
resp = requests.get(f"{API_BASE}/kpis/", params={"role_id": current_user["role_id"]}, headers=api_headers())

if resp.status_code != 200:
    st.error("Failed to load KPIs")
    st.stop()

kpis = resp.json()

if not kpis:
    st.info("No KPIs assigned to your role yet")
    st.stop()

st.subheader("Assigned KPIs")

# Display KPIs
for kpi in kpis:
    with st.expander(f"📊 {kpi['name']} - Weightage: {kpi['weightage']}%"):
        st.write(f"**Description:** {kpi.get('description', 'N/A')}")
        st.write(f"**Category:** {kpi.get('category', 'N/A')}")
        st.write(f"**Target Value:** {kpi.get('target_value', 0)}")
        st.write(f"**Measurement Type:** {kpi.get('measurement_type', 'N/A')}")
        st.write(f"**Frequency:** {kpi.get('period', 'N/A')}")
        
        # Check for override
        override_resp = requests.get(
            f"{API_BASE}/kpis/overrides/",
            params={"user_id": current_user["id"], "kpi_id": kpi["id"]},
            headers=api_headers()
        )
        if override_resp.status_code == 200:
            override = override_resp.json()
            if override:
                st.info(f"⚠️ Custom Target: {override.get('custom_target_value')} (Override applied)")

