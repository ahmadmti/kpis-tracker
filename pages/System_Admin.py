import streamlit as st
import requests
import pandas as pd

API_URL = "http://13.61.15.68:8000"

# Security Check
if "token" not in st.session_state or not st.session_state.token:
    st.stop()

if st.session_state.user.get('role_id') != 1:
    st.error("⛔ Admin Access Required")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}
st.title("⚙️ System Administration")

tab_users, tab_kpis = st.tabs(["👥 User Management", "🎯 KPI Configuration"])

# --- TAB 1: USER MANAGEMENT ---
with tab_users:
    st.subheader("Manage Enterprise Users")
    
    # User Creation Form
    with st.expander("➕ Register New User"):
        with st.form("new_user_form"):
            col1, col2 = st.columns(2)
            new_email = col1.text_input("Email")
            new_name = col2.text_input("Full Name")
            new_pass = col1.text_input("Password", type="password")
            new_role = col2.selectbox("Role", [1, 2, 3], format_func=lambda x: {1:"Admin", 2:"Manager", 3:"Staff"}[x])
            
            if st.form_submit_button("Create User"):
                payload = {"email": new_email, "full_name": new_name, "password": new_pass, "role_id": new_role}
                res = requests.post(f"{API_URL}/users/", json=payload, headers=headers)
                if res.status_code in [200, 201]:
                    st.success(f"User {new_name} created successfully!")
                    st.rerun()
                else:
                    st.error(f"Error: {res.text}")

    st.divider()
    
    # User List Table
    st.write("### Existing Users Directory")
    users_res = requests.get(f"{API_URL}/users/", headers=headers)
    if users_res.status_code == 200:
        df_users = pd.DataFrame(users_res.json())
        # Display clean table
        st.dataframe(df_users[['id', 'full_name', 'email', 'role_id', 'is_active']], use_container_width=True)
        
        # Role Update Section
        st.subheader("🔄 Update User Role")
        c1, c2, c3 = st.columns([1, 2, 1])
        u_id = c1.number_input("User ID", min_value=1)
        r_id = c2.selectbox("New Role", [1, 2, 3], format_func=lambda x: {1:"Admin", 2:"Manager", 3:"Staff"}[x])
        if c3.button("Update Role"):
            requests.patch(f"{API_URL}/users/{u_id}", json={"role_id": r_id}, headers=headers)
            st.success("Role Updated!")
            st.rerun()

# --- TAB 2: KPI CONFIGURATION ---
with tab_kpis:
    st.subheader("Global KPI Definitions")
    
    # KPI Creation Form
    with st.form("new_kpi"):
        col1, col2, col3 = st.columns([2, 1, 1])
        k_name = col1.text_input("KPI Name (e.g., Code Review)")
        k_target = col2.number_input("Target Value", min_value=1.0, value=100.0)
        k_weight = col3.slider("Weightage (%)", 1, 100, 20)
        k_role = st.selectbox("Assign to Role", [1, 2, 3], format_func=lambda x: {1:"Admin", 2:"Manager", 3:"Staff"}[x])
        
        if st.form_submit_button("Add KPI"):
            payload = {"name": k_name, "target_value": k_target, "weightage": k_weight, "role_id": k_role}
            requests.post(f"{API_URL}/kpis/", json=payload, headers=headers)
            st.success("KPI Added!")
            st.rerun()

    # KPI List Table
    kpis_res = requests.get(f"{API_URL}/kpis/", headers=headers)
    if kpis_res.status_code == 200:
        st.table(pd.DataFrame(kpis_res.json())[['id', 'name', 'target_value', 'weightage', 'role_id']])
    
    # Delete KPI
    st.divider()
    del_col1, del_col2 = st.columns([1, 3])
    del_id = del_col1.number_input("KPI ID to Delete", min_value=1)
    if del_col2.button("🗑️ Delete KPI"):
        requests.delete(f"{API_URL}/kpis/{del_id}", headers=headers)
        st.warning(f"KPI {del_id} Deleted.")
        st.rerun()