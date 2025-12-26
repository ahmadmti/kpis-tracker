import streamlit as st
import requests
import pandas as pd

API_URL = "http://13.61.15.68:8000"

# Security Check
if "token" not in st.session_state or not st.session_state.token:
    st.stop()

user = st.session_state.user
# RBAC: Block if not Admin(1) or Manager(2)
if user.get('role_id') not in [1, 2]:
    st.error("⛔ Access Denied: This area is for Managers and Admins only.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}
st.title("👥 Team Management Center")

tab1, tab2 = st.tabs(["✅ Pending Verifications", "📊 Team Overview"])

# --- TAB 1: VERIFICATIONS ---
with tab1:
    st.subheader(" achievements Awaiting Approval")
    achievements = requests.get(f"{API_URL}/achievements/", headers=headers).json()
    
    # Filter for PENDING items
    pending = [a for a in achievements if a['status'] == "PENDING"]
    
    if not pending:
        st.success("All caught up! No pending verifications.")
    else:
        for item in pending:
            with st.expander(f"Submission #{item['id']} - Value: {item['value']}"):
                st.write(f"**Employee ID:** {item['user_id']}")
                st.write(f"**Description:** {item.get('description', 'N/A')}")
                if item.get('evidence_url'):
                    st.markdown(f"[View Evidence]({item['evidence_url']})")
                
                col_a, col_b = st.columns(2)
                if col_a.button("✅ Approve", key=f"app_{item['id']}"):
                    # Verify Endpoint
                    requests.put(f"{API_URL}/achievements/{item['id']}/verify", headers=headers)
                    st.success("Verified!")
                    st.rerun()
                
                if col_b.button("❌ Reject", key=f"rej_{item['id']}"):
                    # Placeholder for rejection logic
                    st.warning("Rejection logic pending backend update.")

# --- TAB 2: TEAM SCORES ---
with tab2:
    st.subheader("Team Performance Overview")
    if user['role_id'] == 1:
        st.info("Admin View: All Enterprise Users")
        rep = requests.get(f"{API_URL}/reports/dashboard", headers=headers)
        if rep.status_code == 200:
            data = rep.json()
            df = pd.DataFrame(data['user_scores'])
            if not df.empty:
                st.bar_chart(df.set_index("full_name")["total_weighted_score"])
                st.dataframe(df[['full_name', 'email', 'total_weighted_score']])
    else:
        st.info("Manager View: Direct Reports")
        # Reuse the same dashboard endpoint for now (filtered logic can be added later)
        rep = requests.get(f"{API_URL}/reports/dashboard", headers=headers)
        if rep.status_code == 200:
            data = rep.json()
            df = pd.DataFrame(data['user_scores'])
            st.dataframe(df)