import streamlit as st
import requests
from api_client import API_BASE, api_headers

st.set_page_config(page_title="KPI Management", layout="wide")

st.title("KPI Management")

# -------------------------
# Fetch KPIs
# -------------------------
resp = requests.get(f"{API_BASE}/kpis/", headers=api_headers())
if resp.status_code != 200:
    st.error("Failed to load KPIs")
    st.stop()

kpis = resp.json()

st.subheader("Existing KPIs")

# Get roles and users for display
roles_resp = requests.get(f"{API_BASE}/roles", headers=api_headers())
roles_dict = {r.get('id'): r.get('name', 'Unknown') for r in roles_resp.json()} if roles_resp.status_code == 200 else {}

users_resp = requests.get(f"{API_BASE}/users/", headers=api_headers())
users_dict = {u.get('id'): u.get('full_name', 'Unknown') for u in users_resp.json()} if users_resp.status_code == 200 else {}

# Enhance KPI display with names
import pandas as pd
if kpis:
    kpi_display = []
    for kpi in kpis:
        kpi_display.append({
            "ID": kpi.get("id"),
            "Name": kpi.get("name"),
            "Category": kpi.get("category"),
            "Target": kpi.get("target_value"),
            "Weightage": kpi.get("weightage"),
            "Frequency": kpi.get("period", "MONTHLY"),
            "Role": roles_dict.get(kpi.get("role_id"), f"Role {kpi.get('role_id')}")
        })
    df = pd.DataFrame(kpi_display)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No KPIs found")

# -------------------------
# Create KPI
# -------------------------
st.divider()
st.subheader("Create New KPI")

with st.form("create_kpi"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("KPI Name")
        description = st.text_area("Description (optional)")
        category = st.text_input("Category")
        target_value = st.number_input("Target Value", min_value=0.01)
    with col2:
        weightage = st.number_input("Weightage (%)", min_value=0.0, max_value=100.0)
        measurement_type = st.selectbox(
            "Measurement Type",
            ["COUNT", "AMOUNT", "PERCENTAGE"]
        )
        period = st.selectbox(
            "Frequency",
            ["DAILY", "WEEKLY", "MONTHLY", "QUARTERLY"],
            index=2  # Default to MONTHLY
        )
        # Get roles for dropdown
        roles_resp = requests.get(f"{API_BASE}/roles", headers=api_headers())
        if roles_resp.status_code == 200:
            roles_list = roles_resp.json()
            role_options = {f"{r.get('name', 'Unknown')}": r.get('id') for r in roles_list}
            selected_role = st.selectbox("Role", list(role_options.keys()))
            role_id = role_options[selected_role] if selected_role else None
        else:
            role_id = st.number_input("Role ID", min_value=1, step=1)

    submitted = st.form_submit_button("Create KPI")

    if submitted:
        if not role_id:
            st.error("Please select a role")
        else:
            payload = {
                "name": name,
                "description": description or None,
                "category": category,
                "target_value": target_value,
                "weightage": weightage,
                "measurement_type": measurement_type,
                "period": period,
                "role_id": int(role_id)
            }

            create_resp = requests.post(
                f"{API_BASE}/kpis/",
                json=payload,
                headers=api_headers()
            )

            if create_resp.status_code == 200:
                st.success("KPI created successfully")
                st.rerun()
            else:
                try:
                    error = create_resp.json()
                    st.error(error.get("detail", str(error)))
                except:
                    st.error(create_resp.text)

# -------------------------
# KPI Overrides
# -------------------------
st.divider()
st.subheader("User KPI Override")

with st.form("kpi_override"):
    # Get users and KPIs for dropdowns
    users_resp = requests.get(f"{API_BASE}/users/", headers=api_headers())
    kpis_resp = requests.get(f"{API_BASE}/kpis/", headers=api_headers())
    
    if users_resp.status_code == 200 and kpis_resp.status_code == 200:
        users_list = users_resp.json()
        kpis_list = kpis_resp.json()
        
        user_options = {f"{u['full_name']} ({u['email']})": u['id'] for u in users_list}
        kpi_options = {f"{k['name']} (Role: {roles_dict.get(k.get('role_id'), 'Unknown')})": k['id'] for k in kpis_list}
        
        selected_user = st.selectbox("Select User", list(user_options.keys()))
        selected_kpi = st.selectbox("Select KPI", list(kpi_options.keys()))
        custom_target_value = st.number_input("Custom Target Value", min_value=0.01)
        
        override_submit = st.form_submit_button("Apply Override")
        
        if override_submit:
            user_id = user_options[selected_user] if selected_user else None
            kpi_id = kpi_options[selected_kpi] if selected_kpi else None
            
            if user_id and kpi_id:
                payload = {
                    "user_id": int(user_id),
                    "kpi_id": int(kpi_id),
                    "custom_target_value": custom_target_value
                }

                override_resp = requests.post(
                    f"{API_BASE}/kpis/overrides/",
                    json=payload,
                    headers=api_headers()
                )

                if override_resp.status_code == 200:
                    st.success("KPI override applied successfully")
                    st.rerun()
                else:
                    try:
                        error = override_resp.json()
                        st.error(error.get("detail", str(error)))
                    except:
                        st.error(override_resp.text)
            else:
                st.error("Please select both user and KPI")
    else:
        st.error("Failed to load users or KPIs")
