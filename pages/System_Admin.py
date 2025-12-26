import streamlit as st
import requests
import pandas as pd

API_URL = "http://13.61.15.68:8000"

if "token" not in st.session_state or st.session_state.user['role_id'] != 1:
    st.error("⛔ Admin Access Required")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}

st.title("⚙️ System Administration")
tab1, tab2, tab3 = st.tabs(["👥 User & Role Assignment", "🎯 KPI Definitions", "📜 System Roles"])

# --- TAB 1: USER & ROLE ASSIGNMENT ---
with tab1:
    st.header("User Management")
    
    # 1. Fetch current users to see their roles
    users_res = requests.get(f"{API_URL}/users/", headers=headers)
    if users_res.status_code == 200:
        df_users = pd.DataFrame(users_res.json())
        st.dataframe(df_users[['id', 'full_name', 'email', 'role_id']], use_container_width=True)
    
    st.divider()
    
    # 2. Assign/Change Role Logic
    st.subheader("🔄 Change User Role")
    with st.form("role_assignment_form"):
        target_user_id = st.number_input("User ID", min_value=1, step=1)
        new_role_id = st.selectbox("Select New Role", options=[1, 2, 3], 
                                  format_func=lambda x: {1: "Admin", 2: "Manager", 3: "Standard User"}[x])
        
        if st.form_submit_button("Update Role"):
            # This calls the PATCH/PUT endpoint we built in the User CRUD module
            res = requests.patch(f"{API_URL}/users/{target_user_id}", 
                                 json={"role_id": new_role_id}, headers=headers)
            if res.status_code == 200:
                st.success("Role updated successfully!")
                st.rerun()

# --- TAB 2: KPI DEFINITIONS (The "Brain" Setup) ---
with tab2:
    st.header("🎯 KPI Target Definition")
    st.info("Define the targets and weightages that will be used for performance scoring.")

    # 1. Create New KPI
    with st.expander("➕ Create New Global KPI"):
        with st.form("kpi_creation_form"):
            k_name = st.text_input("KPI Name (e.g., Sales Target, Code Reviews)")
            k_target = st.number_input("Target Value", min_value=0.0)
            k_weight = st.slider("Weightage (%)", 0, 100, 10)
            k_role = st.selectbox("Target Role", options=[1, 2, 3], 
                                 format_func=lambda x: {1: "Admin", 2: "Manager", 3: "Standard User"}[x])
            
            if st.form_submit_button("Establish KPI"):
                payload = {
                    "name": k_name,
                    "target_value": k_target,
                    "weightage": k_weight,
                    "role_id": k_role
                }
                res = requests.post(f"{API_URL}/kpis/", json=payload, headers=headers)
                if res.status_code == 200:
                    st.success(f"KPI '{k_name}' created!")
                    st.rerun()

    # 2. View Existing KPIs
    st.subheader("Current KPI Framework")
    kpi_res = requests.get(f"{API_URL}/kpis/", headers=headers)
    if kpi_res.status_code == 200:
        st.table(pd.DataFrame(kpi_res.json())[['id', 'name', 'target_value', 'weightage', 'role_id']])

# --- TAB 3: ROLES VIEW ---
with tab3:
    st.header("🛠️ Role Configuration")
    st.write("Current system roles and their permissions (Read-Only).")
    # Fetching roles from the backend
    role_res = requests.get(f"{API_URL}/roles/", headers=headers)
    if role_res.status_code == 200:
        st.json(role_res.json())