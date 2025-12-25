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

# --- 5. Logged-in Navigation Logic ---
headers = {"Authorization": f"Bearer {st.session_state.token}"}

try:
    # Fetch user profile - using the logic that worked in your screenshots
    user_me = requests.get(f"{API_URL}/users/me", headers=headers).json()
    
    # Senior Tip: We use .get() to prevent the "role_id" crash if data is missing
    role_id = user_me.get("role_id")
    user_id = user_me.get("id")
    full_name = user_me.get("full_name", "User")
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📌 Navigation")

# Define menu based on Role (1=Admin, 2=Manager, 3=User)
menu_options = ["🏠 Dashboard", "🏆 Achievements"]

if role_id in [1, 2]:
    menu_options.append("👥 Team Performance")

if role_id == 1:
    menu_options.append("⚙️ KPI Administration")
    menu_options.append("📜 Audit Logs")

selection = st.sidebar.radio("Go to", menu_options)

# --- PAGE ROUTING ---
# This changes the content based on sidebar selection
if selection == "🏠 Dashboard":
    st.title(f"📈 {full_name}'s Dashboard")
    
    if role_id == 1:
        st.subheader("🏢 Admin Enterprise Overview")
        # Fetching the dashboard report we built in Module 12
        res = requests.get(f"{API_URL}/reports/dashboard", headers=headers)
        if res.status_code == 200:
            data = res.json()
            st.metric("Company Avg Score", f"{data['average_score']}%")
            
            # Show the chart
            df = pd.DataFrame(data['user_scores'])
            if not df.empty:
                st.bar_chart(df.set_index("full_name")["total_weighted_score"])
            else:
                st.info("No data available for this month yet.")
    else:
        st.subheader("🎯 My Performance")
        # Individual score logic
        now = datetime.now()
        res = requests.get(f"{API_URL}/users/{user_id}/score?month={now.month}&year={now.year}", headers=headers)
        if res.status_code == 200:
            score = res.json().get("total_weighted_score", 0)
            st.metric("Current Score", f"{score}%")
            st.progress(min(score/100, 1.0))

elif selection == "🏆 Achievements":
    st.title("🏆 My Achievements")
    st.info("Module 2: Achievement Submission Form will be placed here.")

elif selection == "👥 Team Performance":
    st.title("👥 Team Tracking")
    st.write("Manager-only view of direct reports.")

elif selection == "⚙️ KPI Administration":
    st.title("⚙️ KPI Management")
    st.write("Admin-only tool to define KPI targets.")

elif selection == "📜 Audit Logs":
    st.title("📜 System Audit")
    st.write("View immutable activity logs.")