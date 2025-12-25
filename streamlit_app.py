import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_URL = "http://13.61.15.68:8000"
st.set_page_config(page_title="KPI Enterprise", layout="wide")

# --- Authentication Session ---
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.rerun()

# --- Login Logic ---
if not st.session_state.token:
    st.title("🔐 KPI Portal Login")
    with st.container(border=True):
        email = st.text_input("Corporate Email")
        pw = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            res = requests.post(f"{API_URL}/token", data={"username": email, "password": pw})
            if res.status_code == 200:
                st.session_state.token = res.json()["access_token"]
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                st.session_state.user = requests.get(f"{API_URL}/users/me", headers=headers).json()
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.stop()

# --- Main Dashboard (All Roles) ---
headers = {"Authorization": f"Bearer {st.session_state.token}"}
u = st.session_state.user

with st.sidebar:
    st.title("KPI Portal")
    st.info(f"👤 {u['full_name']}\n\nRole ID: {u['role_id']}")
    if st.button("Logout"): logout()

st.title(f"👋 Welcome, {u['full_name']}")
now = datetime.now()

# Fetch Score Logic
score_res = requests.get(f"{API_URL}/users/{u['id']}/score?month={now.month}&year={now.year}", headers=headers)
if score_res.status_code == 200:
    data = score_res.json()
    col1, col2 = st.columns(2)
    col1.metric("Your Performance Score", f"{data['total_weighted_score']}%")
    st.progress(min(data['total_weighted_score']/100, 1.0))