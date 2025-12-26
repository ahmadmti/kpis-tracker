import streamlit as st
import requests
from utils.api_client import API_BASE, api_headers

st.set_page_config(page_title="Roles Overview", layout="wide")

st.title("Roles Overview (Read-Only)")

st.info(
    "Roles are currently system-defined (role_id based). "
    "This page shows how roles are being used across users and KPIs."
)

# -------------------------
# Fetch users
# -------------------------
users_resp = requests.get(f"{API_BASE}/users/", headers=api_headers())
if users_resp.status_code != 200:
    st.error("Failed to load users")
    st.stop()

users = users_resp.json()

# -------------------------
# Build role → users map
# -------------------------
role_map = {}
for u in users:
    rid = u.get("role_id")
    role_map.setdefault(rid, []).append(u)

st.subheader("Role → Users Mapping")

for role_id, role_users in role_map.items():
    with st.expander(f"Role ID: {role_id} ({len(role_users)} users)"):
        st.table([
            {
                "User ID": u["id"],
                "Name": u["full_name"],
                "Email": u["email"],
                "Active": u["is_active"]
            }
            for u in role_users
        ])

# -------------------------
# Fetch KPIs
# -------------------------
st.divider()
st.subheader("Role → KPIs Mapping")

kpi_resp = requests.get(f"{API_BASE}/kpis/", headers=api_headers())
if kpi_resp.status_code != 200:
    st.warning("KPIs endpoint not available or restricted")
    st.stop()

kpis = kpi_resp.json()

kpi_role_map = {}
for k in kpis:
    kpi_role_map.setdefault(k["role_id"], []).append(k)

for role_id, role_kpis in kpi_role_map.items():
    with st.expander(f"Role ID: {role_id} ({len(role_kpis)} KPIs)"):
        st.table([
            {
                "KPI ID": k["id"],
                "Name": k["name"],
                "Target": k["target_value"],
                "Weightage": k["weightage"],
                "Type": k["measurement_type"]
            }
            for k in role_kpis
        ])
