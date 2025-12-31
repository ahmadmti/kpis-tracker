import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from api_client import API_BASE, api_headers

st.set_page_config(page_title="SDR Dashboard", layout="wide")

st.title("📊 My Performance Dashboard")

# Get current user
user_resp = requests.get(f"{API_BASE}/users/me", headers=api_headers())
if user_resp.status_code != 200:
    st.error("Failed to load user data")
    st.stop()

current_user = user_resp.json()

# Filters
col1, col2 = st.columns(2)
with col1:
    year = st.number_input("Year", min_value=2020, max_value=2100, value=datetime.now().year, key="sdr_year")
with col2:
    month = st.number_input("Month", min_value=1, max_value=12, value=datetime.now().month, key="sdr_month")

# Fetch dashboard data
params = {"month": month, "year": year}
resp = requests.get(f"{API_BASE}/dashboard/sdr", params=params, headers=api_headers())

if resp.status_code != 200:
    st.error("Failed to load dashboard data")
    st.stop()

data = resp.json()

# Performance summary
st.header("📈 Performance Summary")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Score", f"{data['total_weighted_score']:.2f}")
with col2:
    status = "Excellent" if data['total_weighted_score'] >= 95 else \
             "Good" if data['total_weighted_score'] >= 70 else \
             "Needs Improvement"
    st.metric("Status", status)
with col3:
    st.metric("Period", data["period"])
with col4:
    st.metric("KPIs Assigned", len(data.get("kpis", [])))

st.divider()

# KPI Details
st.header("🎯 My KPIs")

if data.get("kpis"):
    kpi_df_data = []
    for kpi in data["kpis"]:
        progress = (kpi["achieved_value"] / kpi["target_value"] * 100) if kpi["target_value"] > 0 else 0
        kpi_df_data.append({
            "KPI ID": kpi["kpi_id"],
            "Name": kpi["name"],
            "Target": kpi["target_value"],
            "Achieved": kpi["achieved_value"],
            "Progress %": f"{progress:.1f}%",
            "Weightage": kpi["weightage"],
            "Status": kpi["status"]
        })
    
    kpi_df = pd.DataFrame(kpi_df_data)
    st.dataframe(kpi_df, use_container_width=True)
    
    # Progress bars
    st.subheader("Progress Visualization")
    for kpi in data["kpis"]:
        progress = (kpi["achieved_value"] / kpi["target_value"] * 100) if kpi["target_value"] > 0 else 0
        st.write(f"**{kpi['name']}**")
        st.progress(min(progress / 100, 1.0))
        st.write(f"{kpi['achieved_value']:.2f} / {kpi['target_value']:.2f} ({progress:.1f}%)")
        st.divider()
else:
    st.info("No KPIs assigned to your role yet")

st.divider()

# Achievements
st.header("🏆 My Achievements")

if data.get("achievements"):
    achievements_df = pd.DataFrame(data["achievements"])
    st.dataframe(achievements_df, use_container_width=True)
    
    # Status summary
    status_counts = achievements_df["status"].value_counts()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pending", status_counts.get("PENDING", 0))
    with col2:
        st.metric("Verified", status_counts.get("VERIFIED", 0))
    with col3:
        st.metric("Rejected", status_counts.get("REJECTED", 0))
else:
    st.info("No achievements logged for this period")

