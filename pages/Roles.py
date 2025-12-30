import streamlit as st
from api_client import get, put

st.title("Roles & Permissions")

PROTECTED_ADMIN_PERMISSIONS = [
    "system:config",
    "user:read",
]

roles_resp = get("/roles")
if roles_resp.status_code == 403:
    st.error("You do not have permission to view roles.")
    st.stop()
elif roles_resp.status_code != 200:
    st.error("Failed to load roles")
    st.stop()

raw_roles = roles_resp.json()

# Normalize roles to avoid KeyError
roles = [
    {
        "id": r.get("id"),
        "name": r.get("name") or f"Role #{r.get('id')}"
    }
    for r in raw_roles
    if r.get("id") is not None
]

perms_resp = get("/permissions")
if perms_resp.status_code == 403:
    st.error("You do not have permission to view permissions.")
    st.stop()
elif perms_resp.status_code != 200:
    st.error("Failed to load permissions")
    st.stop()

permissions = perms_resp.json()

role = st.selectbox(
    "Select Role",
    roles,
    format_func=lambda r: r["name"]
)
if not role or "id" not in role:
    st.error("Invalid role selected")
    st.stop()


if role["id"] == 1:
    st.warning(
        "Admin role has protected permissions. "
        "Critical permissions cannot be removed."
    )

assigned_resp = get(f"/roles/{role['id']}/permissions")
if assigned_resp.status_code == 403:
    st.error("You do not have permission to view role permissions.")
    st.stop()
elif assigned_resp.status_code != 200:
    st.error("Failed to load role permissions")
    st.stop()

assigned = assigned_resp.json()

st.subheader("Permissions")

selected = []
for p in permissions:
    checked = p["key"] in assigned
    disabled = role["id"] == 1 and p["key"] in PROTECTED_ADMIN_PERMISSIONS

    if st.checkbox(
        p["key"],
        value=checked,
        disabled=disabled
    ):
        selected.append(p["key"])

if st.button("Save Permissions"):
    put(f"/roles/{role['id']}/permissions", json=selected)
    st.success("Permissions updated")
