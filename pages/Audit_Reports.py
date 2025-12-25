import streamlit as st
import requests
import pandas as pd

API_URL = "http://13.61.15.68:8000"

if "token" not in st.session_state or st.session_state.user['role_id'] != 1:
    st.error("⛔ Admin Access Required")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}
st.title("📜 Audit & Governance")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Data Exports")
    if st.button("生成 Excel Report"):
        report_res = requests.get(f"{API_URL}/reports/export?format=excel", headers=headers)
        if report_res.status_code == 200:
            st.download_button(
                label="📥 Download Excel File",
                data=report_res.content,
                file_name="performance_audit.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

with col2:
    st.subheader("PDF Summaries")
    if st.button("生成 PDF Report"):
        pdf_res = requests.get(f"{API_URL}/reports/export?format=pdf", headers=headers)
        if pdf_res.status_code == 200:
            st.download_button(
                label="📥 Download PDF File",
                data=pdf_res.content,
                file_name="performance_summary.pdf",
                mime="application/pdf"
            )

st.divider()
st.subheader("System Audit Logs")
# Implementation depends on your /audit endpoint from previous modules
st.info("This section displays all write-actions (Create/Update/Delete) performed by users.")