import streamlit as st
import requests

# --- CONFIGURATION ---
API_URL = "http://13.61.15.68:8000"
st.set_page_config(page_title="KPI Portal", layout="wide")

# --- SESSION INITIALIZATION ---
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.rerun()

# --- LOGIN GUARD ---
if not st.session_state.token:
    st.title("🔑 Corporate Login")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            try:
                # API Call to get JWT
                res = requests.post(f"{API_URL}/token", data={"username": email, "password": password})
                
                if res.status_code == 200:
                    st.session_state.token = res.json()["access_token"]
                    
                    # Fetch Profile to verify Role
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    user_res = requests.get(f"{API_URL}/users/me", headers=headers)
                    
                    if user_res.status_code == 200:
                        st.session_state.user = user_res.json()
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Could not retrieve user profile.")
                else:
                    st.error("Invalid email or password.")
            except Exception as e:
                st.error(f"System Error: Connection to backend failed.")
    st.stop()

# --- LOGGED IN HEADER ---
u = st.session_state.user
with st.sidebar:
    st.markdown(f"### 👤 {u.get('full_name', 'User')}")
    st.caption(f"📧 {u.get('email')}")
    st.divider()
    if st.button("Logout", use_container_width=True):
        logout()

st.title("🏠 Dashboard")
st.write(f"Welcome back, **{u.get('full_name')}**. Use the sidebar to navigate.")