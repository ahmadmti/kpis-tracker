import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from api_client import API_BASE, api_headers

st.set_page_config(page_title="My Achievements", layout="wide")

st.title("🏆 My Achievements")

# Get current user
user_resp = requests.get(f"{API_BASE}/users/me", headers=api_headers())
if user_resp.status_code != 200:
    st.error("Failed to load user data")
    st.stop()

current_user = user_resp.json()

# Tabs
tab1, tab2 = st.tabs(["View Achievements", "Submit New Achievement"])

with tab1:
    st.subheader("My Achievement History")
    
    # Status filter
    status_filter = st.selectbox(
        "Filter by Status",
        ["All", "PENDING", "VERIFIED", "REJECTED"],
        key="achievement_status_filter"
    )
    
    # Fetch achievements
    params = {}
    if status_filter != "All":
        params["status_filter"] = status_filter
    
    resp = requests.get(f"{API_BASE}/achievements/", params=params, headers=api_headers())
    
    if resp.status_code != 200:
        st.error("Failed to load achievements")
    else:
        achievements = resp.json()
        
        if achievements:
            # Get KPIs for reference
            kpis_resp = requests.get(f"{API_BASE}/kpis/", params={"role_id": current_user["role_id"]}, headers=api_headers())
            kpis = {k["id"]: k["name"] for k in kpis_resp.json()} if kpis_resp.status_code == 200 else {}
            
            df_data = []
            for ach in achievements:
                df_data.append({
                    "ID": ach["id"],
                    "KPI": kpis.get(ach["kpi_id"], f"KPI {ach['kpi_id']}"),
                    "Achieved Value": ach["achieved_value"],
                    "Status": ach["status"],
                    "Date": ach.get("achievement_date", ""),
                    "Description": ach.get("description", "")[:50] + "..." if ach.get("description") and len(ach.get("description", "")) > 50 else ach.get("description", "")
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
            
            # Status summary
            if df_data:
                status_counts = pd.Series([a["status"] for a in achievements]).value_counts()
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Pending", status_counts.get("PENDING", 0))
                with col2:
                    st.metric("Verified", status_counts.get("VERIFIED", 0))
                with col3:
                    st.metric("Rejected", status_counts.get("REJECTED", 0))
        else:
            st.info("No achievements found")

with tab2:
    st.subheader("Submit New Achievement")
    
    # Get user's KPIs
    kpis_resp = requests.get(f"{API_BASE}/kpis/", params={"role_id": current_user["role_id"]}, headers=api_headers())
    
    if kpis_resp.status_code != 200:
        st.error("Failed to load KPIs")
    else:
        kpis = kpis_resp.json()
        
        if not kpis:
            st.warning("No KPIs assigned to your role. Please contact your administrator.")
        else:
            with st.form("submit_achievement"):
                kpi_id = st.selectbox(
                    "Select KPI",
                    options=[k["id"] for k in kpis],
                    format_func=lambda x: next(k["name"] for k in kpis if k["id"] == x)
                )
                
                achieved_value = st.number_input("Achieved Value", min_value=0.0, step=0.01)
                description = st.text_area("Description", placeholder="Describe your achievement...")
                evidence_url = st.text_input("Evidence URL (optional)", placeholder="Link to proof/documentation")
                
                achievement_date = st.date_input("Achievement Date", value=datetime.now().date())
                
                submitted = st.form_submit_button("Submit for Approval")
                
                if submitted:
                    payload = {
                        "kpi_id": int(kpi_id),
                        "achieved_value": float(achieved_value),
                        "description": description,
                        "evidence_url": evidence_url if evidence_url else None,
                        "achievement_date": datetime.combine(achievement_date, datetime.min.time()).isoformat()
                    }
                    
                    resp = requests.post(
                        f"{API_BASE}/achievements/",
                        json=payload,
                        headers=api_headers()
                    )
                    
                    if resp.status_code == 200:
                        st.success("Achievement submitted successfully! Waiting for manager approval.")
                        st.rerun()
                    else:
                        try:
                            error = resp.json()
                            if isinstance(error, dict) and "detail" in error:
                                st.error(error["detail"])
                            else:
                                st.error(str(error))
                        except:
                            st.error(resp.text)

