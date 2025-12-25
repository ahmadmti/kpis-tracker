import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 1. Configuration (Kept from your old code) ---
API_URL = "http://13.61.15.68:8000"

st.set_page_config(page_title="KPI Tracker | Performance Portal", layout="wide")

# --- 2. Session State Management ---
if "token" not in st.session_state:
    st.session_state.token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

def logout():
    st.session_state.token = None
    st.session_state.user_email = None
    st.rerun()

# --- 3. Sidebar Infrastructure Status (Your previous feature) ---
st.sidebar.title("Infrastructure")
try:
    health = requests.get(f"{API_URL}/health", timeout=2)
    if health.status_code == 200:
        st.sidebar.success("Backend: Online 🟢")
except:
    st.sidebar.error("Backend: Offline 🔴")

if st.session_state.token:
    st.sidebar.info(f"Logged in as: {st.session_state.user_email}")
    if st.sidebar.button("Logout"):
        logout()

# --- 4. Authentication Logic ---
if not st.session_state.token:
    st.title("🔐 KPI Tracker")
    st.subheader("Private Access Only")

    with st.container(border=True):
        email = st.text_input("Corporate Email")
        password = st.text_input("Password", type="password")
        login_btn = st.button("Secure Login", use_container_width=True)

        if login_btn:
            payload = {"username": email, "password": password}
            try:
                response = requests.post(f"{API_URL}/token", data=payload)
                if response.status_code == 200:
                    st.session_state.token = response.json()["access_token"]
                    st.session_state.user_email = email
                    st.success("Authentication successful!")
                    st.rerun()
                else:
                    st.error("Access Denied: Invalid credentials.")
            except Exception as e:
                st.error("System Error: Could not reach server.")
    st.stop()

# --- 5. Logged-in Dashboard Logic (Module 13) ---
headers = {"Authorization": f"Bearer {st.session_state.token}"}

# Fetch Role and User ID from /users/me
try:
    user_me = requests.get(f"{API_URL}/users/me", headers=headers).json()
    role_id = user_me["role_id"]
    user_id = user_me["id"]
    full_name = user_me["full_name"]
except:
    st.error("Could not fetch user profile.")
    st.stop()

st.title(f"📈 {full_name}'s Dashboard")
now = datetime.now()

# --- ROLE-BASED VIEWS ---

# VIEW A: ADMIN (Role 1)
if role_id == 1:
    st.header("Admin Enterprise Overview")
    res = requests.get(f"{API_URL}/reports/dashboard", headers=headers)
    if res.status_code == 200:
        data = res.json()
        col1, col2 = st.columns(2)
        col1.metric("Company Avg Score", f"{data['average_score']}%")
        col2.metric("Period", data['period'])
        
        df = pd.DataFrame(data['user_scores'])
        st.subheader("Employee Performance Ranking")
        st.bar_chart(df.set_index("full_name")["total_weighted_score"])
        st.table(df)

# VIEW B: USER (Role 3) & Others
else:
    st.header("My Performance Progress")
    res = requests.get(f"{API_URL}/users/{user_id}/score?month={now.month}&year={now.year}", headers=headers)
    if res.status_code == 200:
        score = res.json()["total_weighted_score"]
        
        # Display score as a progress bar
        st.write(f"Your weighted score for **{now.strftime('%B %Y')}**")
        st.progress(score / 100 if score <= 100 else 1.0)
        st.metric("Performance Score", f"{score}%")
        
        if score >= 90:
            st.success("Excellent! You are on track for a Bonus.")
        elif score < 50:
            st.warning("Performance is below target. Please review your KPIs.")