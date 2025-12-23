import streamlit as st
import requests

# Constants
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="System Dashboard",
    layout="wide"
)

def render_header():
    """Renders the main application header."""
    st.title("Enterprise System Dashboard")
    st.caption("Module 1: Minimal Bootstrap")
    st.divider()

def check_backend_status():
    """Checks connectivity to the FastAPI backend."""
    st.sidebar.header("System Status")
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            st.sidebar.success("Backend: Online 🟢")
        else:
            st.sidebar.error(f"Backend: Error {response.status_code} 🔴")
    except requests.exceptions.ConnectionError:
        st.sidebar.error("Backend: Offline 🔴")

if __name__ == "__main__":
    render_header()
    check_backend_status()
    st.info("System initialized. Awaiting business logic modules.")