import streamlit as st
import requests

# 1. Configuration
API_URL = "https://kpis-tracker-bg.onrender.com"

st.set_page_config(page_title="Enterprise Portal", layout="centered")

# 2. Session State for Login (Keeps you logged in while clicking buttons)
if "access_token" not in st.session_state:
    st.session_state.access_token = None

# 3. Sidebar Health & Login Status
st.sidebar.title("System Status")
try:
    health = requests.get(f"{API_URL}/health", timeout=3)
    if health.status_code == 200:
        st.sidebar.success("Backend: Online 🟢")
except:
    st.sidebar.error("Backend: Offline 🔴")

if st.session_state.access_token:
    st.sidebar.info("Logged In ✅")
    if st.sidebar.button("Log Out"):
        st.session_state.access_token = None
        st.rerun()

# 4. Main UI
st.title("Enterprise Management System")

tab1, tab2 = st.tabs(["Sign Up", "Login"])

with tab1:
    st.subheader("Create a New Account")
    with st.form("signup"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        # For the first user, leave role_id empty or use 1 after bootstrapping
        role = st.number_input("Role ID (Optional)", value=1)
        btn = st.form_submit_button("Register")
        
        if btn:
            data = {"full_name": name, "email": email, "password": pw, "role_id": role}
            res = requests.post(f"{API_URL}/users/", json=data)
            if res.status_code == 200:
                st.success("Registration successful!")
            else:
                st.error(f"Failed: {res.json().get('detail')}")

with tab2:
    st.subheader("Secure Login")
    login_email = st.text_input("Email", key="login_email")
    login_pw = st.text_input("Password", type="password", key="login_pw")
    if st.button("Login"):
        login_data = {"username": login_email, "password": login_pw}
        # FastAPI uses 'form data' for login, so we use 'data=' instead of 'json='
        res = requests.post(f"{API_URL}/token", data=login_data)
        
        if res.status_code == 200:
            st.session_state.access_token = res.json()["access_token"]
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid email or password")

# 5. Protected Content (Only shows if logged in)
if st.session_state.access_token:
    st.divider()
    st.subheader("Admin Dashboard")
    st.write("You are now authenticated. Your token is active.")
    
    if st.button("Run System Bootstrap"):
        # This calls that special 'Setup' route we added to app.py
        res = requests.get(f"{API_URL}/bootstrap")
        st.write(res.json().get("message"))