import streamlit as st
import pandas as pd
from datetime import datetime

# Streamlit UI
st.title("Dormant Account Transfer Agent")
st.subheader("Automated Transfer to the Central Bank of UAE")

# File Upload Section
uploaded_file = st.file_uploader("Upload Dormant Account CSV File", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Function to Clean Date (Handles Timestamp Issues)
    def clean_date(date_string):
        try:
            # Trim the timestamp if present
            clean_string = date_string.split("T")[0]
            return datetime.strptime(clean_string, "%Y-%m-%d")
        except ValueError:
            return None  # Handle errors gracefully

    # Apply Date Cleaning
    df["Last Transaction Date"] = df["Last Transaction Date"].apply(clean_date)

    # Function to Check Dormancy for Transfer
    def check_transfer_eligibility(last_transaction_date):
        cutoff_date = datetime.strptime("2020-04-24", "%Y-%m-%d")  # Adjusted 5-year cutoff
        return "Eligible for Transfer" if last_transaction_date and last_transaction_date <= cutoff_date else "Not Eligible"

    # Apply Transfer Check
    df["Transfer Status"] = df["Last Transaction Date"].apply(check_transfer_eligibility)

    # Display Eligible Accounts
    st.subheader("Eligible Dormant Accounts for Transfer")
    eligible_accounts = df[df["Transfer Status"] == "Eligible for Transfer"]
    st.dataframe(eligible_accounts)

    # Generate Transfer Report
    if st.button("Generate Transfer Report"):
        st.write("Dormant Account Transfer Report:")
        st.dataframe(df[["Account ID", "Account Type", "Branch", "Transfer Status"]])

    st.sidebar.title("Transfer Agent Dashboard")
    st.sidebar.button("View Dormant Accounts")
    st.sidebar.button("Export Transfer Report")

else:
    st.warning("Please upload a CSV file to proceed.")

