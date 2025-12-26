import requests
import streamlit as st

# =========================
# Backend Configuration
# =========================
API_BASE = "http://13.61.15.68:8000"

# =========================
# Auth Header Helper
# =========================
def api_headers():
    """
    Returns Authorization header using JWT token
    stored in Streamlit session state.
    """
    token = st.session_state.get("access_token")
    if not token:
        return {}
    return {
        "Authorization": f"Bearer {token}"
    }

# =========================
# Generic API Helpers
# =========================
def get(endpoint, params=None):
    return requests.get(
        f"{API_BASE}{endpoint}",
        headers=api_headers(),
        params=params
    )

def post(endpoint, json=None, data=None):
    return requests.post(
        f"{API_BASE}{endpoint}",
        headers=api_headers(),
        json=json,
        data=data
    )

def put(endpoint, json=None):
    return requests.put(
        f"{API_BASE}{endpoint}",
        headers=api_headers(),
        json=json
    )

# =========================
# Error Handling
# =========================
def handle_error(response):
    try:
        detail = response.json()
        if isinstance(detail, dict) and "detail" in detail:
            return detail["detail"]
        return detail
    except Exception:
        return response.text
