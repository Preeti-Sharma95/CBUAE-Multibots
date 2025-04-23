import streamlit as st
import pandas as pd

# Streamlit UI
st.title("Dormant Ledger Agent")
st.subheader("Automated Dormant Account Segregation & Classification")

# File Upload Section
uploaded_file = st.file_uploader("Upload Dormant Account CSV File", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Ledger Classification Rules
    def classify_ledger(account_balance, transaction_date):
        if account_balance > 100000 and transaction_date < "2021-12-31":
            return "High-Value Dormant Ledger"
        elif account_balance <= 100000 and transaction_date < "2021-12-31":
            return "Low-Value Dormant Ledger"
        else:
            return "Standard Dormant Ledger"

    # Apply Ledger Classification
    df["Dormant Ledger Category"] = df.apply(lambda row: classify_ledger(row["Account Balance"], row["Last Transaction Date"]), axis=1)

    # Display Segregated Dormant Accounts
    st.subheader("Dormant Account Classification")
    ledger_category = st.selectbox("Select Ledger Type", df["Dormant Ledger Category"].unique())
    filtered_df = df[df["Dormant Ledger Category"] == ledger_category]
    st.dataframe(filtered_df)

    # Generate Reclassification Report
    if st.button("Generate Ledger Report"):
        st.write("Dormant Ledger Reclassification Report:")
        st.dataframe(df[["Account ID", "Account Type", "Branch", "Dormant Ledger Category"]])

    st.sidebar.title("Dormant Ledger Dashboard")
    st.sidebar.button("View Full Dormant Accounts List")
    st.sidebar.button("Export Ledger Report")

else:
    st.warning("Please upload a CSV file to proceed.")

