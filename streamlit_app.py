import streamlit as st
import requests

# --- 1. CONFIGURATION & SESSION STATE ---
API_URL = "http://13.61.15.68:8000"
st.set_page_config(page_title="Admin Enterprise Portal", layout="wide")

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.current_page = "Dashboard"
    st.rerun()

# --- 2. AUTHENTICATION GUARD ---
# If no token is found, we ONLY show the login form.
if not st.session_state.token:
    st.title("🔐 Admin Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login", use_container_width=True):
            try:
                res = requests.post(f"{API_URL}/token", data={"username": email, "password": password})
                if res.status_code == 200:
                    st.session_state.token = res.json()["access_token"]
                    # Fetch Profile to verify Admin Role
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    u_res = requests.get(f"{API_URL}/users/me", headers=headers)
                    if u_res.status_code == 200:
                        user_data = u_res.json()
                        if user_data.get("role_id") == 1: # Admin Check
                            st.session_state.user = user_data
                            st.success("Welcome, Admin!")
                            st.rerun()
                        else:
                            st.session_state.token = None
                            st.error("⛔ Access Denied: You are not an Admin.")
                else:
                    st.error("Invalid credentials.")
            except:
                st.error("Backend Server is Offline.")
    st.stop() # Stop here so the rest of the app doesn't run for logged-out users

# --- 3. ADMIN LAYOUT & NAVIGATION (Module 2) ---
# This part ONLY runs if the login above was successful.
u = st.session_state.user

with st.sidebar:
    st.title("🛡️ Admin Portal")
    st.info(f"👤 **{u.get('full_name')}**\n\n{u.get('email')}")
    
    menu_items = [
        "Dashboard", "Users", "Roles", "Permissions", "KPIs", 
        "Achievements (Verification)", "Team Performance", 
        "Automation Results", "Audit Logs", "Reports"
    ]
    
    selection = st.radio("Management Menu", menu_items)
    st.session_state.current_page = selection
    
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        logout()

# --- 4. PAGE ROUTING LOGIC ---
st.title(f"📍 {st.session_state.current_page}")

if st.session_state.current_page == "Dashboard":
    st.write("Welcome to the Admin Command Center.")
    # Add dashboard summary metrics here

elif st.session_state.current_page == "Users":
    st.info("User Management Module: API Integration Pending.")

elif st.session_state.current_page == "KPIs":
    st.info("KPI Target Settings: API Integration Pending.")

else:
    st.write(f"The {st.session_state.current_page} module is ready for content.")