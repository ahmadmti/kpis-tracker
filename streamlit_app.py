import streamlit as st
import requests

# --- 1. CONFIGURATION ---
API_URL = "http://13.61.15.68:8000"
st.set_page_config(page_title="Admin Enterprise Portal", layout="wide")

# --- 2. SESSION STATE (The Memory) ---
# We initialize these only if they don't exist
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

def logout():
    # Clear memory and force a rerun to the login screen
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# --- 3. THE GATEKEEPER LOGIC ---
# If the token is missing, we show the login form and STOP the rest of the script.
if st.session_state.token is None:
    st.title("🔐 Admin Login")
    
    with st.container(border=True):
        email = st.text_input("Email", placeholder="admin@example.com")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", use_container_width=True):
            try:
                res = requests.post(f"{API_URL}/token", data={"username": email, "password": password})
                if res.status_code == 200:
                    token = res.json()["access_token"]
                    
                    # Verify Role immediately
                    headers = {"Authorization": f"Bearer {token}"}
                    u_res = requests.get(f"{API_URL}/users/me", headers=headers)
                    
                    if u_res.status_code == 200:
                        user_data = u_res.json()
                        if user_data.get("role_id") == 1:
                            # Save to memory
                            st.session_state.token = token
                            st.session_state.user = user_data
                            st.success("Authenticated. Loading Dashboard...")
                            st.rerun() # Refresh to show the Admin UI
                        else:
                            st.error("⛔ Access Denied: Admin privileges required.")
                    else:
                        st.error("Failed to fetch user profile.")
                else:
                    st.error("Invalid credentials.")
            except Exception as e:
                st.error("Backend Server Unreachable. Check if FastAPI is running.")
    
    # This prevents the navigation from showing if you aren't logged in
    st.stop()

# --- 4. ADMIN UI (Only runs if st.session_state.token exists) ---
u = st.session_state.user

# Sidebar Navigation
with st.sidebar:
    st.title("🛡️ Admin Portal")
    st.info(f"👤 **{u.get('full_name')}**\n\n{u.get('email')}")
    st.divider()
    
    menu_items = [
        "Dashboard", "Users", "Roles", "Permissions", "KPIs", 
        "Achievements (Verification)", "Team Performance", 
        "Automation Results", "Audit Logs", "Reports"
    ]
    
    # We use the 'key' parameter to help Streamlit remember the radio selection
    selection = st.radio("Management Menu", menu_items, key="nav_menu")
    st.session_state.current_page = selection
    
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        logout()

# --- 5. CONTENT AREA ---
st.title(f"📍 {st.session_state.current_page}")

# Logic to handle sub-modules
if st.session_state.current_page == "Dashboard":
    st.write("Command Center Overview")
    
elif st.session_state.current_page == "Users":
    st.subheader("User Directory")
    # This is where the next Module code will go
    st.info("Module 3 (User Management) is ready for integration.")

elif st.session_state.current_page == "KPIs":
    st.subheader("KPI Definitions")
    st.info("Module 5 (KPI Config) is ready for integration.")

else:
    st.write(f"The {st.session_state.current_page} view is active.")