import streamlit as st
import requests

# --- Configuration ---
API_URL = "https://13.61.15.68:8000"

st.set_page_config(page_title="KPI Tracker | Secure Login", layout="centered")

# --- Initialize Session State ---
# This keeps the user logged in across page refreshes
if "token" not in st.session_state:
    st.session_state.token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

def logout():
    st.session_state.token = None
    st.session_state.user_email = None
    st.rerun()

# --- Sidebar Status ---
st.sidebar.title("Infrastructure")
try:
    # Check if backend is alive
    health = requests.get(f"{API_URL}/health", timeout=2)
    if health.status_code == 200:
        st.sidebar.success("Backend: Online 🟢")
except:
    st.sidebar.error("Backend: Offline 🔴")

if st.session_state.token:
    st.sidebar.info(f"Logged in as: {st.session_state.user_email}")
    if st.sidebar.button("Logout"):
        logout()

# --- Main Login Interface ---
if not st.session_state.token:
    st.title("🔐 KPI Tracker")
    st.subheader("Private Access Only")

    with st.container(border=True):
        email = st.text_input("Corporate Email")
        password = st.text_input("Password", type="password")
        login_btn = st.button("Secure Login", use_container_width=True)

        if login_btn:
            if not email or not password:
                st.warning("Please enter both email and password.")
            else:
                # We send data as a form for OAuth2 compatibility
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
                    st.error("System Error: Could not reach authentication server.")

else:
    # --- This is the "Secret" Dashboard ---
    st.title("📈 KPI Dashboard")
    st.write(f"Welcome back, **{st.session_state.user_email}**.")
    st.info("The system is now authenticated. You can proceed to Module 4.")
    
    # Simple Admin tool to verify Module 3 RBAC
    if st.button("Run System Bootstrap (Admin Only)"):
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        res = requests.get(f"{API_URL}/bootstrap", headers=headers)
        st.write(res.json())