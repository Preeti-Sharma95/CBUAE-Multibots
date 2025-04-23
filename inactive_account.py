import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# === Configurations ===
st.set_page_config(page_title="CBUAE Inactive Account Bot", page_icon="📋", layout="wide")

st.markdown("""
    <div style='text-align: center; padding: 1rem;'>
        <h1>📋 CBUAE Inactive Account Bot</h1>
        <p style='font-size: 1.1rem;'>Detects dormant investments and unreachable customers with no active products</p>
    </div>
""", unsafe_allow_html=True)

# === Upload ===
st.sidebar.title(r"C:\Users\Dell\PycharmProjects\migrate_task\inactive_account.csv")
uploaded_file = st.sidebar.file_uploader("Upload Dormant Account CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['Last Transaction Date'] = pd.to_datetime(df['Last Transaction Date'], errors='coerce')
    threshold_date = datetime.now() - timedelta(days=3 * 365)

    # === Investment Inactivity Detection ===
    st.subheader("💼 Investment Account Inactivity")
    investment_df = df[df['Account Type'].str.contains("Investment", case=False)]
    inactive_investments = investment_df[
        (investment_df['Last Transaction Date'] < threshold_date) &
        (investment_df['Email Contact Attempt'].str.lower() == 'no') &
        (investment_df['SMS Contact Attempt'].str.lower() == 'no') &
        (investment_df['Phone Call Attempt'].str.lower() == 'no')
    ]

    st.markdown("### 🚨 Detected Inactive Investment Accounts")
    st.dataframe(inactive_investments)

    # === Unreachable + No Active Account Detection ===
    st.subheader("📵 Unreachable + No Active Accounts")
    df['Email Contact Attempt'] = df['Email Contact Attempt'].str.lower()
    df['SMS Contact Attempt'] = df['SMS Contact Attempt'].str.lower()
    df['Phone Call Attempt'] = df['Phone Call Attempt'].str.lower()
    unreachable = df[
        (df['Email Contact Attempt'] == 'no') &
        (df['SMS Contact Attempt'] == 'no') &
        (df['Phone Call Attempt'] == 'no')
    ]
    unreachable_dormant = unreachable[unreachable['Account Status'].str.lower() == 'dormant']

    st.markdown("### 🚫 Detected Unreachable Customers with No Active Products")
    st.dataframe(unreachable_dormant)

    # === Summary ===
    st.subheader("📋 Executive Summary")
    st.markdown(f"""
    - **Inactive Investment Accounts:** {len(inactive_investments)}
    - **Unreachable + No Active Accounts:** {len(unreachable_dormant)}
    - **Top Impacted Branches:** {', '.join(df['Branch'].value_counts().head(3).index)}
    - **Most Common Customer Types:** {', '.join(df['Customer Type'].value_counts().head(3).index)}

    ### Recommendations:
    - Audit unreachable accounts for next of kin or estate handling.
    - Initiate outreach for investment accounts dormant for 3+ years.
    - Use predictive risk scores to prioritize reactivation efforts.
    - Implement automated reminders post investment maturity.
    """)
else:
    st.info("Please upload a dataset to begin.")
