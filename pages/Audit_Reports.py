import streamlit as st
import requests

API_URL = "http://13.61.15.68:8000"

# Security Check
if "token" not in st.session_state or not st.session_state.token:
    st.stop()

if st.session_state.user.get('role_id') != 1:
    st.error("⛔ Admin Access Required")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}
st.title("📜 Reports & Audits")

col1, col2 = st.columns(2)

# --- EXCEL EXPORT ---
with col1:
    st.info("📄 **Excel Report**")
    st.write("Detailed breakdown of all user scores, achievements, and weighted averages.")
    if st.button("Generate Excel Report"):
        res = requests.get(f"{API_URL}/reports/export?format=excel", headers=headers)
        if res.status_code == 200:
            st.download_button(
                label="📥 Download Excel File",
                data=res.content,
                file_name="performance_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Failed to generate Excel report.")

# --- PDF EXPORT ---
with col2:
    st.info("📕 **PDF Summary**")
    st.write("Executive summary suitable for management review and printing.")
    if st.button("Generate PDF Report"):
        res = requests.get(f"{API_URL}/reports/export?format=pdf", headers=headers)
        if res.status_code == 200:
            st.download_button(
                label="📥 Download PDF File",
                data=res.content,
                file_name="performance_summary.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Failed to generate PDF report.")

st.divider()
st.subheader("System Audit Log")
st.write("Access logs and write-operations history (Coming in Module 15).")