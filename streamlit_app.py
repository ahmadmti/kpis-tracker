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
# --- 1. DASHBOARD PAGE (Updated with KPI Breakdown) ---
if selection == "🏠 Dashboard":
    st.title(f"📈 {full_name}'s Dashboard")
    now = datetime.now()
    
    if role_id == 1:
        st.subheader("🏢 Admin Enterprise Overview")
        res = requests.get(f"{API_URL}/reports/dashboard", headers=headers)
        if res.status_code == 200:
            data = res.json()
            st.metric("Company Avg Score", f"{data['average_score']}%")
            df = pd.DataFrame(data['user_scores'])
            if not df.empty:
                st.bar_chart(df.set_index("full_name")["total_weighted_score"])
                st.table(df)
    
    # All users (including Admin) see their specific KPI progress here
    st.divider()
    st.subheader("🎯 My KPI Progress (Read-Only)")
    
    # Fetch detailed scores (We assume a backend endpoint that returns list of KPIs with current progress)
    # Using our Module 9 logic via the user's score endpoint
    res = requests.get(f"{API_URL}/users/{user_id}/score?month={now.month}&year={now.year}", headers=headers)
    
    if res.status_code == 200:
        score_data = res.json()
        total_score = score_data.get("total_weighted_score", 0)
        
        col1, col2 = st.columns(2)
        col1.metric("Current Monthly Total", f"{total_score}%")
        
        # Displaying a Progress Bar for the overall goal
        st.write("Overall Weightage Completion")
        st.progress(min(total_score/100, 1.0))
        
        # Senior Logic: Display a summary table for clarity
        st.info("Note: Below is a read-only view of your assigned KPIs and weightages.")
        
        # Fetching raw KPIs to show targets
        kpi_res = requests.get(f"{API_URL}/kpis/", headers=headers)
        if kpi_res.status_code == 200:
            kpis = kpi_res.json()
            # Filter KPIs relevant to the user's role (or all if admin)
            display_kpis = [k for k in kpis if k['role_id'] == role_id or role_id == 1]
            
            if display_kpis:
                kpi_df = pd.DataFrame(display_kpis)
                # Cleaning up columns for user view
                view_df = kpi_df[['name', 'target_value', 'weightage']]
                view_df.columns = ['KPI Name', 'Target Value', 'Weightage (%)']
                st.table(view_df)
            else:
                st.write("No KPIs assigned to your role yet.")

# --- 2. ACHIEVEMENTS PAGE (Entry Form & History) ---
elif selection == "🏆 Achievements":
    st.title("🏆 Achievement Center")
    
    # --- SECTION 1: Submission Form ---
    st.subheader("Submit New Progress")
    
    # Fetch KPIs so the user knows what they can submit against
    kpi_res = requests.get(f"{API_URL}/kpis/", headers=headers)
    
    if kpi_res.status_code == 200:
        kpis = kpi_res.json()
        # Filter KPIs for the user's role (or all for Admin)
        user_kpis = [k for k in kpis if k['role_id'] == role_id or role_id == 1]
        
        if not user_kpis:
            st.warning("No KPIs are currently assigned to your role. You cannot submit achievements yet.")
        else:
            # Map names to IDs for the dropdown
            kpi_map = {k['name']: k['id'] for k in user_kpis}
            
            with st.form("achievement_submission_form", clear_on_submit=True):
                selected_kpi = st.selectbox("Target KPI", options=list(kpi_map.keys()))
                achieved_value = st.number_input("Achieved Value", min_value=0.0, step=1.0)
                description = st.text_area("Description / Work Performed", placeholder="Describe how you achieved this...")
                evidence_url = st.text_input("Evidence URL (Optional)", placeholder="https://link-to-proof.com")
                
                submitted = st.form_submit_button("Submit Achievement")
                
                if submitted:
                    # Client-side Validation
                    if achieved_value <= 0:
                        st.error("Please enter a value greater than 0.")
                    elif not description:
                        st.error("Please provide a description of the work.")
                    else:
                        # Prepare Data for Backend
                        payload = {
                            "kpi_id": kpi_map[selected_kpi],
                            "value": achieved_value,
                            "description": description,
                            "evidence_url": evidence_url if evidence_url else None
                        }
                        
                        # API Call
                        post_res = requests.post(f"{API_URL}/achievements/", json=payload, headers=headers)
                        
                        if post_res.status_code == 200:
                            st.success("✅ Achievement submitted successfully! Pending manager verification.")
                            st.balloons() # Visual feedback
                        else:
                            # Show clear API error
                            error_detail = post_res.json().get('detail', 'Unknown error occurred.')
                            st.error(f"❌ Submission Failed: {error_detail}")

    st.divider()

    # --- SECTION 2: History (The Read-only view from Module 2) ---
    st.subheader("Your Submission History")
    ach_res = requests.get(f"{API_URL}/achievements/", headers=headers)
    if ach_res.status_code == 200:
        ach_data = ach_res.json()
        my_ach = [a for a in ach_data if a['user_id'] == user_id]
        if my_ach:
            df_ach = pd.DataFrame(my_ach)
            st.dataframe(df_ach[['id', 'value', 'status', 'description', 'created_at']], use_container_width=True)
        else:
            st.info("No historical data to display.")

elif selection == "👥 Team Performance":
    st.title("👥 Team Tracking")
    st.write("Manager-only view of direct reports.")

elif selection == "⚙️ KPI Administration":
    st.title("⚙️ KPI Management")
    st.write("Admin-only tool to define KPI targets.")

elif selection == "📜 Audit Logs":
    st.title("📜 System Audit")
    st.write("View immutable activity logs.")