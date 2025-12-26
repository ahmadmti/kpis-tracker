import streamlit as st
import requests

# --- CONFIGURATION ---
API_URL = "http://13.61.15.68:8000"

# --- SESSION GUARD ---
# 1. Check if token exists
if "token" not in st.session_state or st.session_state.token is None:
    st.warning("Please login to access this page.")
    st.stop()

# 2. Check if user data exists and verify Admin Role (ID: 1)
user = st.session_state.user
if not user or user.get("role_id") != 1:
    st.error("⛔ **Access Denied**: You do not have Administrative privileges.")
    if st.button("Return to Home"):
        st.switch_page("streamlit_app.py")
    st.stop()

# --- ADMIN HEADER ---
st.set_page_config(page_title="System Administration", layout="wide")

# Top Bar Admin Info
col1, col2 = st.columns([4, 1])
with col1:
    st.title("⚙️ System Administration")
    st.markdown(f"**Admin:** {user.get('full_name')} | **Email:** {user.get('email')}")
with col2:
    if st.button("Logout", key="admin_logout"):
        st.session_state.token = None
        st.session_state.user = None
        st.switch_page("streamlit_app.py")

st.divider()

# --- ADMIN UI CONTENT ---
st.info("Authentication Verified. Admin session is active.")

# Example layout for Admin Tasks
tab1, tab2 = st.tabs(["User Management", "System Logs"])

with tab1:
    st.subheader("Manage Users")
    st.write("Fetching user directory from API...")
    # Your GET /users/ logic goes here using headers={"Authorization": f"Bearer {st.session_state.token}"}

with tab2:
    st.subheader("Recent System Activity")
    st.write("Viewing audit logs...")