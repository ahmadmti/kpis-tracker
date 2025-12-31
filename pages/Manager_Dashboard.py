import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from api_client import API_BASE, api_headers

st.set_page_config(page_title="Manager Dashboard", layout="wide")

st.title("📊 Manager Dashboard")

# Get current user
user_resp = requests.get(f"{API_BASE}/users/me", headers=api_headers())
if user_resp.status_code != 200:
    st.error("Failed to load user data")
    st.stop()

current_user = user_resp.json()

# Filters
col1, col2 = st.columns(2)
with col1:
    year = st.number_input("Year", min_value=2020, max_value=2100, value=datetime.now().year, key="mgr_year")
with col2:
    month = st.number_input("Month", min_value=1, max_value=12, value=datetime.now().month, key="mgr_month")

# Fetch dashboard data
params = {"month": month, "year": year}
resp = requests.get(f"{API_BASE}/dashboard/manager", params=params, headers=api_headers())

if resp.status_code != 200:
    st.error("Failed to load dashboard data")
    st.stop()

data = resp.json()

# Manager's own performance
st.header("👤 My Performance")
manager_data = data["manager"]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("My Score", f"{manager_data['total_weighted_score']:.2f}")
with col2:
    st.metric("Period", manager_data["period"])
with col3:
    status = "Excellent" if manager_data['total_weighted_score'] >= 95 else \
             "Good" if manager_data['total_weighted_score'] >= 70 else \
             "Needs Improvement"
    st.metric("Status", status)

st.divider()

# Team performance
st.header("👥 Team Performance")
team_data = data["team"]

if team_data:
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Team Size", len(team_data))
    with col2:
        avg_team_score = sum(m["total_weighted_score"] for m in team_data) / len(team_data) if team_data else 0
        st.metric("Average Team Score", f"{avg_team_score:.2f}")
    with col3:
        high_performers = sum(1 for m in team_data if m["total_weighted_score"] >= 95)
        st.metric("High Performers", high_performers)
    
    # Team table
    df_data = []
    for member in team_data:
        df_data.append({
            "ID": member["user_id"],
            "Name": member["full_name"],
            "Email": member["email"],
            "Score": member["total_weighted_score"],
            "Status": "Excellent" if member["total_weighted_score"] >= 95 else \
                     "Good" if member["total_weighted_score"] >= 70 else \
                     "Needs Improvement"
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True)
    
    # Visual chart
    if len(team_data) > 0:
        chart_data = pd.DataFrame({
            "Name": [m["full_name"] for m in team_data],
            "Score": [m["total_weighted_score"] for m in team_data]
        })
        st.bar_chart(chart_data.set_index("Name"))
else:
    st.info("No team members assigned yet")

