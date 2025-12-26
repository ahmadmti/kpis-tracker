import streamlit as st
import requests
from utils.api_client import API_BASE, api_headers

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

pending = [a for a in achievements if a["status"] == "PENDING"]

if not pending:
    st.success("No pending achievements 🎉")
    st.stop()

# -----------------------------------
# Display & actions
# -----------------------------------
for ach in pending:
    with st.expander(f"Achievement #{ach['id']} | User {ach['user_id']} | KPI {ach['kpi_id']}"):
        st.write(f"**Achieved Value:** {ach['achieved_value']}")
        st.write(f"**Description:** {ach['description']}")

        if ach.get("evidence_url"):
            st.markdown(f"[Evidence Link]({ach['evidence_url']})")

        col1, col2 = st.columns(2)

        # VERIFY
        with col1:
            if st.button(f"✅ Verify #{ach['id']}"):
                verify_payload = {"status": "VERIFIED"}
                vr = requests.put(
                    f"{API_BASE}/achievements/{ach['id']}/verify",
                    json=verify_payload,
                    headers=api_headers()
                )

                if vr.status_code == 200:
                    st.success("Achievement verified")
                    st.rerun()
                else:
                    st.error(vr.json())

        # REJECT
        with col2:
            reason = st.text_input(
                f"Rejection reason #{ach['id']}",
                key=f"reason_{ach['id']}"
            )

            if st.button(f"❌ Reject #{ach['id']}"):
                if not reason:
                    st.warning("Rejection reason is required")
                else:
                    reject_payload = {
                        "status": "REJECTED",
                        "rejection_reason": reason
                    }

                    rr = requests.put(
                        f"{API_BASE}/achievements/{ach['id']}/verify",
                        json=reject_payload,
                        headers=api_headers()
                    )

                    if rr.status_code == 200:
                        st.success("Achievement rejected")
                        st.rerun()
                    else:
                        st.error(rr.json())
