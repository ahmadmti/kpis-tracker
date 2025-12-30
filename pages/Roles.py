import streamlit as st
from api_client import get, put
import models

st.title("Roles & Permissions")

roles = get("/roles").json()
permissions = get("/permissions").json()

role = st.selectbox("Select Role", roles, format_func=lambda r: r["name"])
if role["id"] == 1:
    st.warning(
        "Admin role has protected permissions. "
        "Critical permissions cannot be removed."
    )

assigned = get(f"/roles/{role['id']}/permissions").json()

st.subheader("Permissions")

selected = []
for p in permissions:
    checked = p["key"] in assigned
    disabled = role["id"] == 1 and p["key"] in [
        models.PermissionType.SYSTEM_CONFIG.value,
        models.PermissionType.USER_READ.value,
    ]

    if st.checkbox(
        p["key"],
        value=checked,
        disabled=disabled
    ):
        selected.append(p["key"])


if st.button("Save Permissions"):
    put(f"/roles/{role['id']}/permissions", json=selected)
    st.success("Permissions updated")
