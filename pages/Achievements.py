import streamlit as st
import requests
from api_client import API_BASE, api_headers

st.set_page_config(page_title="Achievement Verification", layout="wide")

st.title("Achievement Verification")

st.info("Verify or reject submitted achievements. Only pending items are actionable.")

# -----------------------------------
# Fetch pending achievements
# -----------------------------------
resp = requests.get(
    f"{API_BASE}/achievements/",
    headers=api_headers()
)

if resp.status_code != 200:
    st.error("Failed to load achievements")
    st.stop()

achievements = resp.json()

pending = [a for a in achievements if a.get("status") == "PENDING"]

if not pending:
    st.success("No pending achievements 🎉")
    st.stop()

# Get user and KPI names
users_resp = requests.get(f"{API_BASE}/users/", headers=api_headers())
users_dict = {u.get('id'): u.get('full_name', 'Unknown') for u in users_resp.json()} if users_resp.status_code == 200 else {}

kpis_resp = requests.get(f"{API_BASE}/kpis/", headers=api_headers())
kpis_dict = {k.get('id'): k.get('name', 'Unknown') for k in kpis_resp.json()} if kpis_resp.status_code == 200 else {}

# -----------------------------------
# Display & actions
# -----------------------------------
for ach in pending:
    user_name = users_dict.get(ach.get('user_id'), f"User {ach.get('user_id')}")
    kpi_name = kpis_dict.get(ach.get('kpi_id'), f"KPI {ach.get('kpi_id')}")
    
    with st.expander(f"Achievement #{ach.get('id')} | {user_name} | {kpi_name}"):
        st.write(f"**User:** {user_name}")
        st.write(f"**KPI:** {kpi_name}")
        st.write(f"**Achieved Value:** {ach.get('achieved_value', 0)}")
        st.write(f"**Description:** {ach.get('description', 'N/A')}")

        if ach.get("evidence_url"):
            st.markdown(f"[Evidence Link]({ach['evidence_url']})")

        col1, col2 = st.columns(2)

        # VERIFY
        with col1:
            if st.button(f"✅ Verify", key=f"verify_{ach.get('id')}"):
                verify_payload = {"status": "VERIFIED"}
                vr = requests.put(
                    f"{API_BASE}/achievements/{ach.get('id')}/verify",
                    json=verify_payload,
                    headers=api_headers()
                )

                if vr.status_code == 200:
                    st.success("Achievement verified")
                    st.rerun()
                else:
                    try:
                        error = vr.json()
                        st.error(error.get("detail", str(error)))
                    except:
                        st.error(vr.text)

        # REJECT
        with col2:
            reason = st.text_input(
                "Rejection reason",
                key=f"reason_{ach.get('id')}"
            )

            if st.button(f"❌ Reject", key=f"reject_{ach.get('id')}"):
                if not reason:
                    st.warning("Rejection reason is required")
                else:
                    reject_payload = {
                        "status": "REJECTED",
                        "rejection_reason": reason
                    }

                    rr = requests.put(
                        f"{API_BASE}/achievements/{ach.get('id')}/verify",
                        json=reject_payload,
                        headers=api_headers()
                    )

                    if rr.status_code == 200:
                        st.success("Achievement rejected")
                        st.rerun()
                    else:
                        try:
                            error = rr.json()
                            st.error(error.get("detail", str(error)))
                        except:
                            st.error(rr.text)
