import streamlit as st
import requests

API_BASE = "http://13.61.15.68:8000"

# -----------------------------
# Helpers
# -----------------------------
def api_headers():
    token = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def api_error(resp):
    try:
        return resp.json()
    except:
        return resp.text

# -----------------------------
# Auth
# -----------------------------
def login():
    st.title("Admin Login")

    username = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        resp = requests.post(
            f"{API_BASE}/token",
            data={
                "username": username,
                "password": password
            }
        )

        if resp.status_code == 200:
            data = resp.json()
            st.session_state.access_token = data["access_token"]
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

def require_admin():
    resp = requests.get(f"{API_BASE}/users/me", headers=api_headers())
    if resp.status_code != 200:
        st.error("Session expired")
        st.session_state.clear()
        st.rerun()

    user = resp.json()
    st.session_state.current_user = user
    return user

# -----------------------------
# Users Page
# -----------------------------
def users_page():
    st.header("User Management")

    # Fetch users
    resp = requests.get(f"{API_BASE}/users/", headers=api_headers())
    if resp.status_code != 200:
        st.error("Failed to load users")
        return

    users = resp.json()

    st.subheader("Existing Users")
    st.dataframe(users, use_container_width=True)

    st.divider()
    st.subheader("Create New User")

    with st.form("create_user"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role_id = st.number_input("Role ID", min_value=1, step=1)
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

# -----------------------------
# App Router
# -----------------------------
def main():
    if "access_token" not in st.session_state:
        login()
        return

    user = require_admin()

    st.sidebar.title("Admin Panel")
    st.sidebar.write(user["full_name"])
    st.sidebar.write(user["email"])

    page = st.sidebar.radio(
        "Navigation",
        ["Users"]
    )

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    if page == "Users":
        users_page()
    if page == "Roles":
        from pages import Roles

# -----------------------------
main()
