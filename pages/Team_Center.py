import streamlit as st
import requests
import pandas as pd

API_URL = "http://13.61.15.68:8000"

if "token" not in st.session_state:
    st.error("Please login on the home page.")
    st.stop()

# Strict RBAC: Only Managers and Admins
if st.session_state.user['role_id'] not in [1, 2]:
    st.error("⛔ Access Denied: Managerial privileges required.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}
st.title("👥 Team Performance & Verification")

tab1, tab2 = st.tabs(["✅ Pending Verifications", "📊 Team Analytics"])

with tab1:
    st.subheader("Achievements Awaiting Approval")
    # Fetch all achievements
    res = requests.get(f"{API_URL}/achievements/", headers=headers)
    if res.status_code == 200:
        all_ach = res.json()
        # Filter for PENDING status
        pending = [a for a in all_ach if a['status'] == "PENDING"] # Adjust string if using Enum
        
        if not pending:
            st.info("Everything is caught up! No pending verifications.")
        else:
            for ach in pending:
                with st.expander(f"Submission ID: {ach['id']} | User ID: {ach['user_id']}"):
                    st.write(f"**Value:** {ach['value']}")
                    st.write(f"**Description:** {ach.get('description', 'N/A')}")
                    if st.button("Verify & Approve", key=f"verify_{ach['id']}"):
                        # Call PUT /achievements/{id}/verify
                        verify_res = requests.put(f"{API_URL}/achievements/{ach['id']}/verify", headers=headers)
                        if verify_res.status_code == 200:
                            st.success("Achievement Verified!")
                            st.rerun()

with tab2:
    st.subheader("Team Scoring Overview")
    # Admin View: Show Enterprise Dashboard
    if st.session_state.user['role_id'] == 1:
        report_res = requests.get(f"{API_URL}/reports/dashboard", headers=headers)
        if report_res.status_code == 200:
            data = report_res.json()
            df = pd.DataFrame(data['user_scores'])
            st.bar_chart(df.set_index("full_name")["total_weighted_score"])
    else:
        st.info("Individual team member breakdowns will appear here.")