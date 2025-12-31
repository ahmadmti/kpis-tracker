import streamlit as st
from api_client import get, put

st.title("Roles & Permissions")

PROTECTED_ADMIN_PERMISSIONS = [
    "system:config",
    "user:read",
]

# Load roles with error handling
try:
    roles_resp = get("/roles")
    if roles_resp.status_code == 403:
        st.error("You do not have permission to view roles.")
        st.stop()
    elif roles_resp.status_code != 200:
        st.error(f"Failed to load roles: {roles_resp.status_code}")
        st.stop()
    
    raw_roles = roles_resp.json()
    if not isinstance(raw_roles, list):
        st.error("Invalid roles data format")
        st.stop()
    
    # Normalize roles to avoid KeyError
    roles = [
        {
            "id": r.get("id"),
            "name": r.get("name") or f"Role #{r.get('id')}"
        }
        for r in raw_roles
        if r.get("id") is not None
    ]
except Exception as e:
    st.error(f"Error loading roles: {str(e)}")
    st.stop()

if not roles:
    st.warning("No roles available. Please create roles first.")
    st.stop()

# Load permissions with error handling
try:
    perms_resp = get("/permissions")
    if perms_resp.status_code == 403:
        st.error("You do not have permission to view permissions.")
        st.stop()
    elif perms_resp.status_code != 200:
        st.error(f"Failed to load permissions: {perms_resp.status_code}")
        st.stop()
    
    permissions = perms_resp.json()
    if not isinstance(permissions, list):
        st.error("Invalid permissions data format")
        st.stop()
except Exception as e:
    st.error(f"Error loading permissions: {str(e)}")
    st.stop()

# Use index-based selection to avoid dict issues
role_options = [r["name"] for r in roles]
if not role_options:
    st.error("No role options available")
    st.stop()

try:
    selected_index = st.selectbox(
        "Select Role",
        range(len(role_options)),
        format_func=lambda i: role_options[i] if i < len(role_options) else "Unknown"
    )
    
    if selected_index is None or selected_index >= len(roles):
        st.error("Invalid role selection")
        st.stop()
    
    role = roles[selected_index]
    
    if not role or "id" not in role:
        st.error("Invalid role selected")
        st.stop()
except Exception as e:
    st.error(f"Error selecting role: {str(e)}")
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
