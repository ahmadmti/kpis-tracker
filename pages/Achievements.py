import streamlit as st
import requests
import pandas as pd

API_URL = "http://13.61.15.68:8000"

# Security Check
if "token" not in st.session_state or not st.session_state.token:
    st.warning("Please login on the main page first.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}
user = st.session_state.user

st.title("🏆 My Achievements")
tab1, tab2 = st.tabs(["➕ Submit New", "📜 My History"])

# --- TAB 1: SUBMISSION FORM ---
with tab1:
    st.subheader("Log a New Achievement")
    try:
        # Fetch all KPIs
        kpis = requests.get(f"{API_URL}/kpis/", headers=headers).json()
        # Filter KPIs relevant to this user
        my_kpis = [k for k in kpis if k['role_id'] == user['role_id'] or user['role_id'] == 1]
        
        if not my_kpis:
            st.warning("No KPIs found for your role. Please contact Admin.")
        else:
            with st.form("achievement_form", clear_on_submit=True):
                # Create a dropdown map: "Name (Target: 100)" -> ID
                kpi_map = {f"{k['name']} (Target: {k['target_value']})": k['id'] for k in my_kpis}
                selected_label = st.selectbox("Select Target KPI", list(kpi_map.keys()))
                
                val = st.number_input("Value Achieved", min_value=0.0, step=1.0)
                desc = st.text_area("Description / Evidence", placeholder="Describe your work...")
                evidence = st.text_input("Evidence Link (Optional)")
                
                if st.form_submit_button("Submit for Verification"):
                    payload = {
                        "kpi_id": kpi_map[selected_label], 
                        "value": val, 
                        "description": desc,
                        "evidence_url": evidence
                    }
                    res = requests.post(f"{API_URL}/achievements/", json=payload, headers=headers)
                    if res.status_code == 200:
                        st.balloons()
                        st.success("Achievement submitted successfully!")
                    else:
                        st.error(f"Submission failed: {res.text}")
    except Exception as e:
        st.error(f"Error loading KPIs: {e}")

# --- TAB 2: HISTORY VIEW ---
with tab2:
    st.subheader("Submission History")
    try:
        ach_res = requests.get(f"{API_URL}/achievements/", headers=headers)
        if ach_res.status_code == 200:
            all_ach = ach_res.json()
            # Filter only my achievements
            my_ach = [a for a in all_ach if a['user_id'] == user['id']]
            
            if my_ach:
                df = pd.DataFrame(my_ach)
                # Select clean columns
                display_df = df[['created_at', 'value', 'status', 'description']]
                st.dataframe(display_df, use_container_width=True)
            else:
                st.info("No past submissions found.")
    except Exception as e:
        st.error(f"Could not load history: {e}")