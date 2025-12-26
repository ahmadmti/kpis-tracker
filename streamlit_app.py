import streamlit as st
import requests, pandas as pd

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
        email = st.text_input("Email", placeholder="admin@example.comm",value="ahmad_fraz@abark.tech")
        password = st.text_input("Password", type="password",value="Admin@786")
        
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
    
    # DEFENSIVE CHECK: Only show user info if 'u' is not None
    u = st.session_state.get("user") 
    
    if u is not None:
        st.info(f"👤 **{u.get('full_name')}**\n\n{u.get('email')}")
    else:
        st.warning("👤 Session initializing...")
    
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
    st.title("📊 Enterprise Performance Overview")
    
    # 1. API Fetching Logic
    try:
        # We use the token from session state to authorize the request
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.get(f"{API_URL}/admin/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # 2. Key Performance Metrics (Metric Cards)
            # We create 5 columns to spread the data horizontally
            m1, m2, m3, m4, m5 = st.columns(5)
            
            # Using .get() ensures the app doesn't crash if a value is missing from the JSON
            m1.metric("Total Users", data.get("total_users", 0))
            m2.metric("Active Users", data.get("active_users", 0))
            m3.metric("Total KPIs", data.get("total_kpis", 0))
            m4.metric("Avg. Completion", f"{data.get('avg_completion', 0)}%")
            m5.metric("Underperforming", data.get("underperforming_count", 0), delta_color="inverse")
            
            st.divider()

            # 3. Data Visualization (Charts)
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("Departmental Distribution")
                # Assume backend returns a list of dictionaries for 'dept_scores'
                dept_data = data.get("dept_scores", [])
                if dept_data:
                    df_dept = pd.DataFrame(dept_data)
                    st.bar_chart(data=df_dept, x="department", y="average_score")
                else:
                    st.info("No departmental data available to chart.")

            with col_right:
                st.subheader("Monthly Progress")
                # Assume backend returns 'monthly_trends'
                trend_data = data.get("monthly_trends", [])
                if trend_data:
                    df_trend = pd.DataFrame(trend_data)
                    st.line_chart(data=df_trend, x="month", y="completion_rate")
                else:
                    st.info("No trend data available to chart.")

        elif response.status_code == 401:
            st.error("🔒 Session expired. Please log out and log back in.")
        else:
            st.warning(f"⚠️ Dashboard data partially unavailable (Status: {response.status_code})")

    except Exception as e:
        st.error(f"🚫 Connection Error: Could not reach the Admin API. ({str(e)})")
        st.info("Ensure the FastAPI server is running and accessible.")
    
elif st.session_state.current_page == "Users":
    st.subheader("User Directory")
    # This is where the next Module code will go
    st.info("Module 3 (User Management) is ready for integration.")

elif st.session_state.current_page == "KPIs":
    st.subheader("KPI Definitions")
    st.info("Module 5 (KPI Config) is ready for integration.")

else:
    st.write(f"The {st.session_state.current_page} view is active.")