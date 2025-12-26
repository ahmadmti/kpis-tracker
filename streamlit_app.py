import streamlit as st
import requests
from datetime import datetime

# --- CONFIGURATION ---
API_URL = "http://13.61.15.68:8000"
st.set_page_config(page_title="KPI Enterprise Portal", layout="wide")

# --- SESSION STATE ---
if "token" not in st.session_state: st.session_state.token = None
if "user" not in st.session_state: st.session_state.user = None

def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.rerun()

# --- LOGIN SCREEN ---
if not st.session_state.token:
    st.title("🔐 Enterprise Login")
    with st.container(border=True):
        email = st.text_input("Corporate Email")
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            try:
                res = requests.post(f"{API_URL}/token", data={"username": email, "password": password})
                if res.status_code == 200:
                    st.session_state.token = res.json()["access_token"]
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    u_res = requests.get(f"{API_URL}/users/me", headers=headers)
                    if u_res.status_code == 200:
                        st.session_state.user = u_res.json()
                        st.rerun()
                else:
                    st.error("Invalid Credentials.")
            except Exception as e:
                st.error(f"Backend Offline: {e}")
    st.stop()

# --- LOGGED IN SIDEBAR ---
# Streamlit will automatically show files from /pages/ here.
u = st.session_state.user
role_map = {1: "Admin", 2: "Manager", 3: "Staff"}

with st.sidebar:
    st.title("🚀 KPI Portal")
    st.info(f"👤 **{u.get('full_name')}**\n\nRole: {role_map.get(u.get('role_id'), 'User')}")
    if st.button("Logout"): logout()

# --- MAIN DASHBOARD CONTENT ---
st.title(f"👋 Welcome, {u.get('full_name')}")
st.write("### Personal Performance Summary")

# Metric Fetching
headers = {"Authorization": f"Bearer {st.session_state.token}"}
now = datetime.now()
try:
    res = requests.get(f"{API_URL}/users/{u['id']}/score?month={now.month}&year={now.year}", headers=headers)
    if res.status_code == 200:
        score = res.json().get("total_weighted_score", 0)
        st.metric("My Current Score", f"{score}%")
        st.progress(min(score/100, 1.0))
except:
    st.info("Performance metrics will appear here once achievements are verified.")

st.success("Please use the sidebar to navigate to other modules.")