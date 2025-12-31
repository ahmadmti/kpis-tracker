import streamlit as st
import requests
import sys
import os
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

API_BASE = "http://13.61.15.68:8000"

# -----------------------------
# Helpers
# -----------------------------
def api_headers():
    token = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def api_error(resp):
    try:
        error = resp.json()
        if isinstance(error, dict) and "detail" in error:
            return error["detail"]
        return error
    except:
        return resp.text

# -----------------------------
# Auth Pages
# -----------------------------
def login_page():
    st.title("🔐 Login")
    
    tab1, tab2 = st.tabs(["Login", "Forgot Password"])
    
    with tab1:
        username = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Login"):
                resp = requests.post(
                    f"{API_BASE}/token",
                    data={"username": username, "password": password}
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.access_token = data["access_token"]
                    
                    # Get user info
                    user_resp = requests.get(f"{API_BASE}/users/me", headers=api_headers())
                    if user_resp.status_code == 200:
                        st.session_state.current_user = user_resp.json()
                    
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(api_error(resp))
    
    with tab2:
        st.subheader("Forgot Password")
        email = st.text_input("Enter your email")
        if st.button("Send Reset Link"):
            resp = requests.post(
                f"{API_BASE}/auth/forgot-password",
                json={"email": email}
            )
            if resp.status_code == 200:
                data = resp.json()
                st.success("Password reset token generated")
                st.info(f"Token: {data.get('token', 'Check your email')}")
                st.info("In production, this would be sent via email")
            else:
                st.error(api_error(resp))

def change_password_page():
    st.header("Change Password")
    
    with st.form("change_password"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        submitted = st.form_submit_button("Change Password")
        
        if submitted:
            if new_password != confirm_password:
                st.error("New passwords do not match")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters")
            else:
                resp = requests.post(
                    f"{API_BASE}/auth/change-password",
                    json={
                        "current_password": current_password,
                        "new_password": new_password
                    },
                    headers=api_headers()
                )
                
                if resp.status_code == 200:
                    st.success("Password changed successfully")
                else:
                    st.error(api_error(resp))

# -----------------------------
# User Management
# -----------------------------
def require_auth():
    """Check if user is authenticated"""
    if "access_token" not in st.session_state:
        return None
    
    resp = requests.get(f"{API_BASE}/users/me", headers=api_headers())
    if resp.status_code != 200:
        st.session_state.clear()
        st.error("Session expired. Please login again.")
        st.rerun()
    
    user = resp.json()
    st.session_state.current_user = user
    return user

def users_page():
    st.header("👥 User Management")
    
    # Fetch users
    resp = requests.get(f"{API_BASE}/users/", headers=api_headers())
    if resp.status_code != 200:
        st.error("Failed to load users")
        return
    
    users = resp.json()
    
    st.subheader("Existing Users")
    if users:
        import pandas as pd
        df = pd.DataFrame(users)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No users found")
    
    st.divider()
    st.subheader("Create New User")
    
    with st.form("create_user"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
        with col2:
            password = st.text_input("Password", type="password")
            role_id = st.number_input("Role ID", min_value=1, step=1, value=1)
        
        is_active = st.checkbox("Active", value=True)
        submitted = st.form_submit_button("Create User")
        
        if submitted:
            payload = {
                "email": email,
                "full_name": full_name,
                "password": password,
                "role_id": int(role_id),
                "is_active": is_active
            }
            
            resp = requests.post(
                f"{API_BASE}/users/",
                json=payload,
                headers=api_headers()
            )
            
            if resp.status_code == 200:
                st.success("User created successfully")
                st.rerun()
            else:
                st.error(api_error(resp))
    
    st.divider()
    st.subheader("Assign Users to Manager")
    
    with st.form("assign_manager"):
        user_id = st.number_input("User ID", min_value=1, step=1, key="assign_user_id")
        manager_id = st.number_input("Manager ID", min_value=1, step=1, key="assign_manager_id")
        
        if st.form_submit_button("Assign Manager"):
            resp = requests.put(
                f"{API_BASE}/users/{user_id}/manager?manager_id={manager_id}",
                headers=api_headers()
            )
            
            if resp.status_code == 200:
                st.success("Manager assigned successfully")
                st.rerun()
            else:
                st.error(api_error(resp))

# -----------------------------
# Admin Dashboard
# -----------------------------
def admin_dashboard_page():
    st.header("📊 Admin Dashboard")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        year = st.number_input("Year", min_value=2020, max_value=2100, value=datetime.now().year)
    with col2:
        month = st.number_input("Month", min_value=1, max_value=12, value=datetime.now().month)
    with col3:
        all_users = requests.get(f"{API_BASE}/users/", headers=api_headers()).json()
        user_options = ["All Users"] + [f"{u['id']} - {u['full_name']}" for u in all_users]
        selected_user = st.selectbox("Filter by User", user_options)
        user_id = None if selected_user == "All Users" else int(selected_user.split(" - ")[0])
    
    # Fetch dashboard data
    params = {"month": month, "year": year}
    if user_id:
        params["user_id"] = user_id
    
    resp = requests.get(f"{API_BASE}/dashboard/admin", params=params, headers=api_headers())
    
    if resp.status_code != 200:
        st.error("Failed to load dashboard data")
        return
    
    data = resp.json()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", data["total_users"])
    with col2:
        avg_score = sum(u["total_weighted_score"] for u in data["user_scores"]) / len(data["user_scores"]) if data["user_scores"] else 0
        st.metric("Average Score", f"{avg_score:.2f}")
    with col3:
        st.metric("Period", data["period"])
    with col4:
        high_performers = sum(1 for u in data["user_scores"] if u["total_weighted_score"] >= 95)
        st.metric("High Performers (≥95)", high_performers)
    
    st.divider()
    
    # User scores table
    if data["user_scores"]:
        import pandas as pd
        df_data = []
        for user_data in data["user_scores"]:
            df_data.append({
                "User ID": user_data["user_id"],
                "Name": user_data["full_name"],
                "Email": user_data["email"],
                "Score": user_data["total_weighted_score"],
                "Achievements Count": len(user_data["achievements"])
            })
        df = pd.DataFrame(df_data)
        st.subheader("User Performance")
        st.dataframe(df, use_container_width=True)
        
        # Drill-down details
        st.divider()
        st.subheader("📋 Achievement Details")
        
        selected_user_detail = st.selectbox(
            "Select User to View Details",
            [f"{u['user_id']} - {u['full_name']}" for u in data["user_scores"]]
        )
        
        if selected_user_detail:
            user_id_detail = int(selected_user_detail.split(" - ")[0])
            user_detail = next(u for u in data["user_scores"] if u["user_id"] == user_id_detail)
            
            st.write(f"**User:** {user_detail['full_name']} ({user_detail['email']})")
            st.write(f"**Total Score:** {user_detail['total_weighted_score']}")
            
            if user_detail["achievements"]:
                achievements_df = pd.DataFrame(user_detail["achievements"])
                st.dataframe(achievements_df, use_container_width=True)
            else:
                st.info("No achievements for this period")
    else:
        st.info("No data available for the selected period")

# -----------------------------
# Decision Setup (Automation Rules)
# -----------------------------
def decision_setup_page():
    st.header("⚙️ Decision Setup Based on KPI Achievement")
    
    st.info("Configure automated decisions based on KPI achievement weightage scores")
    
    # View existing recommendations
    st.subheader("Current Recommendations")
    resp = requests.get(f"{API_BASE}/admin/recommendations", headers=api_headers())
    if resp.status_code == 200:
        recommendations = resp.json()
        if recommendations:
            import pandas as pd
            df_data = []
            for rec in recommendations:
                df_data.append({
                    "User ID": rec.get("user_id"),
                    "Score": rec.get("score_achieved"),
                    "Recommendation": rec.get("recommendation"),
                    "Period": rec.get("period"),
                    "Created": rec.get("created_at", "")
                })
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No recommendations generated yet")
    
    st.divider()
    st.subheader("Run Evaluation")
    st.write("Evaluate a user's performance and generate recommendations based on thresholds:")
    st.write("- **≥95%**: Bonus/Promotion")
    st.write("- **70-94%**: Satisfactory (No action)")
    st.write("- **50-69%**: Warning")
    st.write("- **<50%**: Final Warning / Termination")
    
    with st.form("evaluate_user"):
        user_id = st.number_input("User ID to Evaluate", min_value=1, step=1)
        if st.form_submit_button("Run Evaluation"):
            resp = requests.post(
                f"{API_BASE}/admin/evaluate/{user_id}",
                headers=api_headers()
            )
            
            if resp.status_code == 200:
                result = resp.json()
                if "message" in result:
                    st.success(result["message"])
                else:
                    st.success(f"Recommendation generated: {result.get('recommendation')}")
                st.rerun()
            else:
                st.error(api_error(resp))

# -----------------------------
# App Router
# -----------------------------
def main():
    st.set_page_config(page_title="KPIs Tracker", layout="wide")
    
    # Check authentication
    if "access_token" not in st.session_state:
        login_page()
        return
    
    user = require_auth()
    if not user:
        return
    
    role_id = user.get("role_id", 0)
    role_name = "Admin" if role_id == 1 else ("Manager" if role_id == 2 else "SDR")
    
    # Sidebar
    st.sidebar.title(f"👤 {role_name} Panel")
    st.sidebar.write(f"**Name:** {user.get('full_name')}")
    st.sidebar.write(f"**Email:** {user.get('email')}")
    
    # Role-based navigation
    if role_id == 1:  # Admin
        pages = [
            "Dashboard",
            "Users",
            "Roles",
            "KPIs",
            "Achievements",
            "Team Assignment",
            "Decision Setup",
            "Reports",
            "Change Password"
        ]
    elif role_id == 2:  # Manager
        pages = [
            "Dashboard",
            "My KPIs",
            "My Achievements",
            "Team Verification",
            "Change Password"
        ]
    else:  # SDR
        pages = [
            "Dashboard",
            "My KPIs",
            "My Achievements",
            "Change Password"
        ]
    
    page = st.sidebar.radio("Navigation", pages)
    
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
    
    # Route to pages
    if page == "Dashboard":
        if role_id == 1:
            admin_dashboard_page()
        elif role_id == 2:
            import pages.Manager_Dashboard
        else:
            import pages.SDR_Dashboard
    
    elif page == "Users" and role_id == 1:
        users_page()
    
    elif page == "Roles" and role_id == 1:
        import pages.Roles
    
    elif page == "KPIs" and role_id == 1:
        import pages.KPIs
    
    elif page == "Achievements" and role_id == 1:
        import pages.Achievements
    
    elif page == "Team Assignment" and role_id == 1:
        users_page()  # Reuse users page with manager assignment
    
    elif page == "Decision Setup" and role_id == 1:
        decision_setup_page()
    
    elif page == "Reports" and role_id == 1:
        import pages.Audit_Reports
    
    elif page == "My KPIs":
        import pages.My_KPIs
    
    elif page == "My Achievements":
        import pages.My_Achievements
    
    elif page == "Team Verification" and role_id == 2:
        import pages.Team_Center
    
    elif page == "Change Password":
        change_password_page()

if __name__ == "__main__":
    main()
