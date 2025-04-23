import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# === Configurations ===
st.set_page_config(page_title="CBUAE Investment Account Bot", page_icon="💼", layout="wide")

st.markdown("""
    <div style='text-align: center; padding: 1rem;'>
        <h1>💼 CBUAE Investment Account Inactivity Bot</h1>
        <p style='font-size: 1.1rem;'>Detects Investment Accounts with No Redemption/Contact for 3 Years</p>
    </div>
""", unsafe_allow_html=True)

# === Upload ===
st.sidebar.title(r"C:\Users\Dell\Downloads\CBUAE_Compliance_Dormant_Dataset.csv")
uploaded_file = st.sidebar.file_uploader("Upload Investment Account CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['Last Transaction Date'] = pd.to_datetime(df['Last Transaction Date'], errors='coerce')
    threshold_date = datetime.now() - timedelta(days=3 * 365)

    # === Filtering ===
    investment_df = df[df['Account Type'].str.contains("Investment", case=False)]
    violations = investment_df[
        (investment_df['Last Transaction Date'] < threshold_date) &
        (investment_df['Email Contact Attempt'].str.lower() == 'no') &
        (investment_df['SMS Contact Attempt'].str.lower() == 'no') &
        (investment_df['Phone Call Attempt'].str.lower() == 'no')
    ]

    st.subheader("🚨 Inactive Investment Account Violations")
    st.dataframe(violations)

    st.subheader("📋 Executive Summary")
    st.markdown("""
    - **Total Violations Found:** {}
    - **Branches Affected:** {}
    - **Most Common Customer Types:** {}

    ### Recommendations:
    - Flag these accounts for compliance audit.
    - Notify customers with missing redemptions or contact attempts.
    - Automate inactivity monitoring post-investment.
    - Escalate high-balance dormant investments to risk review.
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
