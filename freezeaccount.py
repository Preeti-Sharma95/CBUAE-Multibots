import streamlit as st
import pandas as pd

# Streamlit UI
st.title("Freeze Account Agent")
st.subheader("Automated Dormant Account Locking & Charge Blocking")

# File Upload Section
uploaded_file = st.file_uploader("Upload Dormant Account CSV File", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Freeze Conditions
    def freeze_account(account_status, transaction_date, kyc_status):
        if account_status == "Dormant" and transaction_date < "2022-01-01" and kyc_status == "Expired":
            return "Frozen"
        else:
            return "Active"

    # Apply Freeze Command
    df["Freeze Status"] = df.apply(lambda row: freeze_account(row["Account Status"], row["Last Transaction Date"], row["KYC Status"]), axis=1)

    # Display Frozen Accounts
    st.subheader("Frozen Account List")
    frozen_accounts = df[df["Freeze Status"] == "Frozen"]
    st.dataframe(frozen_accounts)

    # Generate Freeze Report
    if st.button("Generate Freeze Report"):
        st.write("Frozen Account Report:")
        st.dataframe(df[["Account ID", "Account Type", "Branch", "Freeze Status"]])

    st.sidebar.title("Freeze Command Dashboard")
    st.sidebar.button("View All Dormant Accounts")
    st.sidebar.button("Export Freeze Report")

else:
    st.warning("Please upload a CSV file to proceed.")

