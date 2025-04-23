import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# === Configurations ===
st.set_page_config(page_title="CBUAE Safe Deposit Box Bot", page_icon="🔐", layout="wide")

st.markdown("""
    <div style='text-align: center; padding: 1rem;'>
        <h1>🔐 CBUAE Safe Deposit Box Compliance Bot</h1>
        <p style='font-size: 1.1rem;'>Detects Dormant Safe Deposit Box Accounts as per CBUAE Guidelines</p>
    </div>
""", unsafe_allow_html=True)

# === Upload ===
st.sidebar.title("📂 Upload Dataset")
uploaded_file = st.sidebar.file_uploader(r"C:\Users\Dell\Downloads\CBUAE_Compliance_Dormant_Dataset.csv", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['Last Transaction Date'] = pd.to_datetime(df['Last Transaction Date'], errors='coerce')
    threshold_date = datetime.now() - timedelta(days=3 * 365)

    # === Filtering ===
    safe_df = df[df['Account Type'].str.contains("Safe Deposit", case=False)]
    violations = safe_df[
        (safe_df['Last Transaction Date'] < threshold_date) &
        (safe_df['Email Contact Attempt'].str.lower() == 'no') &
        (safe_df['SMS Contact Attempt'].str.lower() == 'no') &
        (safe_df['Phone Call Attempt'].str.lower() == 'no')
    ]

    st.subheader("🚨 Dormant Safe Deposit Box Violations")
    st.dataframe(violations)

    st.subheader("📋 Executive Summary")
    st.markdown("""
    - **Total Violations Found:** {}
    - **Branches Affected:** {}
    - **Most Common Customer Types:** {}

    ### Recommendations:
    - Initiate audit trail for all listed accounts.
    - Escalate flagged entries to compliance for customer outreach.
    - Apply reminders for scheduled safe box renewals.
    - Create alerts for missing contact attempts moving forward.
    """.format(
        len(violations),
        ", ".join(violations['Branch'].value_counts().head(3).index),
        ", ".join(violations['Customer Type'].value_counts().head(3).index)
    ))

    st.subheader("💬 Ask a Question About This Data")
    question = st.text_input("Type a question (e.g., Which branch has the most violations?)")
    if question:
        st.markdown("⚠️ AI bot module has been removed. You can filter data manually below.")
else:
    st.info("Please upload a dataset to begin.")
