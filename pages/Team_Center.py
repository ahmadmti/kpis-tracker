import streamlit as st
import requests
import pandas as pd
from api_client import API_BASE, api_headers

st.set_page_config(page_title="Team Verification", layout="wide")

# Security Check
if "access_token" not in st.session_state:
    st.error("Please login to access this page.")
    st.stop()

# Get current user
user_resp = requests.get(f"{API_BASE}/users/me", headers=api_headers())
if user_resp.status_code != 200:
    st.error("Failed to load user data")
    st.stop()

user = user_resp.json()

# RBAC: Block if not Admin(1) or Manager(2)
if user.get('role_id') not in [1, 2]:
    st.error("⛔ Access Denied: This area is for Managers and Admins only.")
    st.stop()

st.title("👥 Team Verification Center")

tab1, tab2 = st.tabs(["✅ Pending Verifications", "📊 Team Overview"])

# --- TAB 1: VERIFICATIONS ---
with tab1:
    st.subheader("Achievements Awaiting Approval")
    
    # Fetch achievements
    resp = requests.get(f"{API_BASE}/achievements/", params={"status_filter": "PENDING"}, headers=api_headers())
    
    if resp.status_code != 200:
        st.error("Failed to load achievements")
    else:
        achievements = resp.json()
        
        # Filter for team members only (if manager)
        if user['role_id'] == 2:  # Manager
            # Get team members
            team_resp = requests.get(f"{API_BASE}/dashboard/manager", headers=api_headers())
            if team_resp.status_code == 200:
                team_data = team_resp.json()
                team_user_ids = [m["user_id"] for m in team_data.get("team", [])]
                achievements = [a for a in achievements if a['user_id'] in team_user_ids]
        
        pending = [a for a in achievements if a.get('status') == "PENDING"]
        
        if not pending:
            st.success("All caught up! No pending verifications.")
        else:
            # Get user names
            users_resp = requests.get(f"{API_BASE}/users/", headers=api_headers())
            users = {u["id"]: u["full_name"] for u in users_resp.json()} if users_resp.status_code == 200 else {}
            
            # Get KPI names
            kpis_resp = requests.get(f"{API_BASE}/kpis/", headers=api_headers())
            kpis = {k["id"]: k["name"] for k in kpis_resp.json()} if kpis_resp.status_code == 200 else {}
            
            for item in pending:
                user_name = users.get(item['user_id'], f"User {item['user_id']}")
                kpi_name = kpis.get(item['kpi_id'], f"KPI {item['kpi_id']}")
                
                with st.expander(f"Submission #{item['id']} | {user_name} | {kpi_name} | Value: {item.get('achieved_value', 0)}"):
                    st.write(f"**Employee:** {user_name} (ID: {item['user_id']})")
                    st.write(f"**KPI:** {kpi_name}")
                    st.write(f"**Achieved Value:** {item.get('achieved_value', 0)}")
                    st.write(f"**Description:** {item.get('description', 'N/A')}")
                    
                    if item.get('evidence_url'):
                        st.markdown(f"[View Evidence]({item['evidence_url']})")
                    
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        if st.button("✅ Approve", key=f"app_{item['id']}"):
                            verify_resp = requests.put(
                                f"{API_BASE}/achievements/{item['id']}/verify",
                                json={"status": "VERIFIED"},
                                headers=api_headers()
                            )
                            if verify_resp.status_code == 200:
                                st.success("Verified!")
                                st.rerun()
                            else:
                                st.error("Failed to verify")
                    
                    with col_b:
                        rejection_reason = st.text_input(
                            "Rejection Reason",
                            key=f"rej_reason_{item['id']}",
                            placeholder="Enter reason for rejection"
                        )
                        if st.button("❌ Reject", key=f"rej_{item['id']}"):
                            if not rejection_reason:
                                st.warning("Please provide a rejection reason")
                            else:
                                reject_resp = requests.put(
                                    f"{API_BASE}/achievements/{item['id']}/verify",
                                    json={
                                        "status": "REJECTED",
                                        "rejection_reason": rejection_reason
                                    },
                                    headers=api_headers()
                                )
                                if reject_resp.status_code == 200:
                                    st.success("Rejected")
                                    st.rerun()
                                else:
                                    st.error("Failed to reject")

# --- TAB 2: TEAM SCORES ---
with tab2:
    st.subheader("Team Performance Overview")
    
    if user['role_id'] == 1:
        st.info("Admin View: All Enterprise Users")
        resp = requests.get(f"{API_BASE}/dashboard/admin", headers=api_headers())
        if resp.status_code == 200:
            data = resp.json()
            if data.get('user_scores'):
                df = pd.DataFrame(data['user_scores'])
                if not df.empty:
                    chart_df = df[['full_name', 'total_weighted_score']].set_index('full_name')
                    st.bar_chart(chart_df)
                    st.dataframe(df[['user_id', 'full_name', 'email', 'total_weighted_score']])
    else:
        st.info("Manager View: Direct Reports")
        resp = requests.get(f"{API_BASE}/dashboard/manager", headers=api_headers())
        if resp.status_code == 200:
            data = resp.json()
            team_data = data.get('team', [])
            if team_data:
                df = pd.DataFrame(team_data)
                chart_df = df[['full_name', 'total_weighted_score']].set_index('full_name')
                st.bar_chart(chart_df)
                st.dataframe(df[['user_id', 'full_name', 'email', 'total_weighted_score']])
            else:
                st.info("No team members assigned yet")
