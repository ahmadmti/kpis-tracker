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
    user_me = requests.get(f"{API_URL}/users/me", headers=headers).json()
    role_id = user_me["role_id"]
    user_id = user_me["id"]
    full_name = user_me["full_name"]
except Exception as e:
    st.error(f"Could not fetch user profile: {e}")
    st.stop()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📌 Navigation")

# Define menu options based on Role ID (1=Admin, 2=Manager, 3=User)
menu_options = ["🏠 Dashboard", "🏆 Achievements"]

if role_id in [1, 2]:
    menu_options.append("👥 Team Performance")

if role_id == 1:
    menu_options.append("⚙️ KPI Administration")
    menu_options.append("📜 Audit Logs")

selection = st.sidebar.radio("Go to", menu_options)

# --- PAGE ROUTING ---
st.title(f"{selection}")
now = datetime.now()

# 1. DASHBOARD PAGE
if selection == "🏠 Dashboard":
    if role_id == 1:
        st.subheader("🏢 Enterprise Overview")
        res = requests.get(f"{API_URL}/reports/dashboard", headers=headers)
        if res.status_code == 200:
            data = res.json()
            col1, col2 = st.columns(2)
            col1.metric("Company Avg Score", f"{data['average_score']}%")
            col2.download_button("📥 Export Excel Report", 
                                data=requests.get(f"{API_URL}/reports/export?format=excel", headers=headers).content,
                                file_name="company_report.xlsx")
            
            df = pd.DataFrame(data['user_scores'])
            st.bar_chart(df.set_index("full_name")["total_weighted_score"])
            st.table(df)
    else:
        st.subheader(f"Personal Performance: {full_name}")
        res = requests.get(f"{API_URL}/users/{user_id}/score?month={now.month}&year={now.year}", headers=headers)
        if res.status_code == 200:
            score = res.json()["total_weighted_score"]
            st.metric("My Performance Score", f"{score}%")
            st.progress(score / 100 if score <= 100 else 1.0)
            if score >= 90: st.success("Keep up the great work!")

# 2. ACHIEVEMENTS PAGE (Placeholder for UI Module 2)
elif selection == "🏆 Achievements":
    st.subheader("My Submissions")
    st.info("Coming Soon: You will be able to log new achievements and upload evidence here.")

# 3. TEAM PERFORMANCE PAGE
elif selection == "👥 Team Performance":
    st.subheader("Team Progress Tracking")
    if role_id not in [1, 2]:
        st.error("Access Denied")
    else:
        st.write("List of direct reports and their monthly status will appear here.")

# 4. KPI ADMINISTRATION PAGE
elif selection == "⚙️ KPI Administration":
    st.subheader("Manage Global KPIs")
    if role_id != 1:
        st.error("Admin Only")
    else:
        st.write("Tools to create/edit KPIs and set weightages.")

# 5. AUDIT LOGS PAGE
elif selection == "📜 Audit Logs":
    st.subheader("System Activity Feed")
    if role_id != 1:
        st.error("Admin Only")
    else:
        st.write("View the immutable record of all system actions.")