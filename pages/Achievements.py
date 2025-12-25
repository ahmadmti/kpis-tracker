import streamlit as st
import requests
import pandas as pd

API_URL = "http://13.61.15.68:8000"
if "token" not in st.session_state:
    st.error("Please login first")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}
user = st.session_state.user

st.title("🏆 My Achievements")

# Submission Form
with st.expander("Submit New Achievement", expanded=True):
    kpis = requests.get(f"{API_URL}/kpis/", headers=headers).json()
    my_kpis = [k for k in kpis if k['role_id'] == user['role_id'] or user['role_id'] == 1]
    
    with st.form("sub_form"):
        kpi_map = {k['name']: k['id'] for k in my_kpis}
        selected = st.selectbox("KPI Target", options=list(kpi_map.keys()))
        val = st.number_input("Value Achieved")
        desc = st.text_area("Details")
        if st.form_submit_button("Submit"):
            payload = {"kpi_id": kpi_map[selected], "value": val, "description": desc}
            requests.post(f"{API_URL}/achievements/", json=payload, headers=headers)
            st.success("Submitted for verification!")

# Personal History
st.subheader("Your Submission History")
history = requests.get(f"{API_URL}/achievements/", headers=headers).json()
my_data = [h for h in history if h['user_id'] == user['id']]
if my_data:
    st.dataframe(pd.DataFrame(my_data)[['id', 'value', 'status', 'created_at']], use_container_width=True)