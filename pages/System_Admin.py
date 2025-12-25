import streamlit as st
import requests
import pandas as pd

API_URL = "http://13.61.15.68:8000"
headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}

# Strict RBAC Check
if st.session_state.user['role_id'] != 1:
    st.error("Access Denied: Admins Only")
    st.stop()

st.title("⚙️ System Administration")
t1, t2 = st.tabs(["👤 Users Management", "🎯 KPI Setup"])

with t1:
    st.subheader("Add New User")
    with st.form("new_user"):
        e = st.text_input("Email")
        n = st.text_input("Full Name")
        p = st.text_input("Password", type="password")
        r = st.selectbox("Role", options=[1, 2, 3], help="1: Admin, 2: Manager, 3: User")
        if st.form_submit_button("Create User"):
            # Logic: requests.post(f"{API_URL}/users/", json={...})
            st.success(f"User {n} created successfully!")

with t2:
    st.subheader("Define Global KPIs")
    with st.form("new_kpi"):
        kn = st.text_input("KPI Name")
        kt = st.number_input("Target Value")
        kw = st.number_input("Weightage (%)", max_value=100)
        kr = st.number_input("Role ID target", min_value=1)
        if st.form_submit_button("Save KPI"):
            # Logic: requests.post(f"{API_URL}/kpis/", json={...})
            st.success(f"KPI {kn} established.")