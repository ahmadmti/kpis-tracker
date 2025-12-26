import streamlit as st
import requests
from utils.api_client import API_BASE, api_headers

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
st.dataframe(kpis, use_container_width=True)

# -------------------------
# Create KPI
# -------------------------
st.divider()
st.subheader("Create New KPI")

with st.form("create_kpi"):
    name = st.text_input("KPI Name")
    description = st.text_area("Description (optional)")
    category = st.text_input("Category")
    target_value = st.number_input("Target Value", min_value=0.01)
    weightage = st.number_input("Weightage (%)", min_value=0.0, max_value=100.0)
    measurement_type = st.selectbox(
        "Measurement Type",
        ["COUNT", "AMOUNT", "PERCENTAGE"]
    )
    role_id = st.number_input("Role ID", min_value=1, step=1)

    submitted = st.form_submit_button("Create KPI")

    if submitted:
        payload = {
            "name": name,
            "description": description or None,
            "category": category,
            "target_value": target_value,
            "weightage": weightage,
            "measurement_type": measurement_type,
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
            st.error(create_resp.json())

# -------------------------
# KPI Overrides
# -------------------------
st.divider()
st.subheader("User KPI Override")

with st.form("kpi_override"):
    user_id = st.number_input("User ID", min_value=1, step=1)
    kpi_id = st.number_input("KPI ID", min_value=1, step=1)
    custom_target_value = st.number_input("Custom Target Value", min_value=0.01)

    override_submit = st.form_submit_button("Apply Override")

    if override_submit:
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
        else:
            st.error(override_resp.json())
