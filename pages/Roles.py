import streamlit as st
from api_client import get, put

st.title("Roles & Permissions")

roles = get("/roles").json()
permissions = get("/permissions").json()

role = st.selectbox("Select Role", roles, format_func=lambda r: r["name"])

assigned = get(f"/roles/{role['id']}/permissions").json()

st.subheader("Permissions")

selected = []
for p in permissions:
    checked = p["key"] in assigned
    if st.checkbox(p["key"], value=checked):
        selected.append(p["key"])

if st.button("Save Permissions"):
    put(f"/roles/{role['id']}/permissions", json=selected)
    st.success("Permissions updated")
