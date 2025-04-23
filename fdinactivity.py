import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import io
import base64
import numpy as np

# Set page configuration
st.set_page_config(
    page_title="FD Inactivity Tracker",
    page_icon="💰",
    layout="wide"
)

# App title and description
st.title("Fixed Deposit Inactivity Tracker")
st.markdown("""
This application tracks Fixed Deposit accounts that haven't been claimed or renewed within 3 years of maturity.
Upload your account data CSV to begin analysis.
""")

# File uploader
uploaded_file = st.file_uploader("Upload CSV file", type="csv")


# Define functions
def calculate_maturity_status(df):
    # Convert date strings to datetime objects
    df['Last Transaction Date'] = pd.to_datetime(df['Last Transaction Date'])

    # Current date for calculations (using today's date)
    current_date = datetime.now()

    # Calculate days since last transaction
    df['Days Since Last Transaction'] = (current_date - df['Last Transaction Date']).dt.days

    # Calculate years since last transaction
    df['Years Since Last Transaction'] = df['Days Since Last Transaction'] / 365.25

    # Flag accounts based on inactivity criteria (3 years)
    df['Inactive Flag'] = df['Years Since Last Transaction'] >= 3

    # Determine maturity status for visualization
    conditions = [
        (df['Years Since Last Transaction'] < 1),
        (df['Years Since Last Transaction'] >= 1) & (df['Years Since Last Transaction'] < 2),
        (df['Years Since Last Transaction'] >= 2) & (df['Years Since Last Transaction'] < 3),
        (df['Years Since Last Transaction'] >= 3)
    ]
    choices = ['Active', 'Approaching Inactivity', 'High Risk', 'Inactive']
    df['Maturity Status'] = pd.Series(np.select(conditions, choices, default='Unknown'), index=df.index)

    return df


def generate_account_summary(df):
    # Filter for Fixed Deposit accounts
    fd_accounts = df[df['Account Type'] == 'Fixed Deposit']

    # Calculate statistics
    total_fd = len(fd_accounts)
    inactive_fd = len(fd_accounts[fd_accounts['Inactive Flag']])
    active_fd = total_fd - inactive_fd

    inactive_value = fd_accounts[fd_accounts['Inactive Flag']]['Account Balance'].sum()

    # Generate branch statistics
    branch_stats = fd_accounts[fd_accounts['Inactive Flag']].groupby('Branch').agg(
        account_count=('Account ID', 'count'),
        total_balance=('Account Balance', 'sum')
    ).reset_index()

    return {
        'total_fd': total_fd,
        'inactive_fd': inactive_fd,
        'active_fd': active_fd,
        'inactive_value': inactive_value,
        'branch_stats': branch_stats
    }


def get_contact_summary(df):
    # Focus on inactive Fixed Deposit accounts
    inactive_fd = df[(df['Account Type'] == 'Fixed Deposit') & (df['Inactive Flag'])]

    # Count contact attempts
    email_attempts = len(inactive_fd[inactive_fd['Email Contact Attempt'] == 'Yes'])
    sms_attempts = len(inactive_fd[inactive_fd['SMS Contact Attempt'] == 'Yes'])
    phone_attempts = len(inactive_fd[inactive_fd['Phone Call Attempt'] == 'Yes'])

    # Accounts with no contact attempts
    no_contact = len(inactive_fd[(inactive_fd['Email Contact Attempt'] == 'No') &
                                 (inactive_fd['SMS Contact Attempt'] == 'No') &
                                 (inactive_fd['Phone Call Attempt'] == 'No')])

    return {
        'email_attempts': email_attempts,
        'sms_attempts': sms_attempts,
        'phone_attempts': phone_attempts,
        'no_contact': no_contact,
        'total': len(inactive_fd)
    }


def get_download_link(df, filename, text):
    """Generate a link to download the dataframe as CSV"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


# Main app logic
if uploaded_file is not None:
    # Read the data
    try:
        df = pd.read_csv(uploaded_file)

        # Process the data
        df = calculate_maturity_status(df)

        # Generate account summary
        summary = generate_account_summary(df)
        contact_summary = get_contact_summary(df)

        # Display dashboard in tabs
        tab1, tab2 = st.tabs(["Dashboard", "Account Details"])

        with tab1:
            # Key metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total FD Accounts", summary['total_fd'])

            with col2:
                st.metric("Inactive FD Accounts", summary['inactive_fd'],
                          f"{summary['inactive_fd'] / summary['total_fd'] * 100:.1f}%" if summary[
                                                                                            'total_fd'] > 0 else "0%")

            with col3:
                st.metric("Inactive Account Value", f"${summary['inactive_value']:,.2f}")

            # Charts row
            st.subheader("Visualizations")
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                # Pie chart showing account status distribution
                fd_accounts = df[df['Account Type'] == 'Fixed Deposit']
                status_counts = fd_accounts['Maturity Status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']

                fig1 = px.pie(status_counts, values='Count', names='Status',
                              title='Fixed Deposit Accounts by Maturity Status',
                              color='Status',
                              color_discrete_map={
                                  'Active': 'green',
                                  'Approaching Inactivity': 'yellow',
                                  'High Risk': 'orange',
                                  'Inactive': 'red'
                              })
                st.plotly_chart(fig1, use_container_width=True)

            with chart_col2:
                # Bar chart showing inactive accounts by branch
                branch_stats = summary['branch_stats']
                if not branch_stats.empty:
                    fig2 = px.bar(branch_stats, x='Branch', y='account_count',
                                  title='Inactive FD Accounts by Branch',
                                  labels={'account_count': 'Number of Accounts'})
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("No inactive accounts found in the dataset.")

            # Contact attempts summary
            st.subheader("Contact Attempts for Inactive Accounts")

            contact_col1, contact_col2 = st.columns(2)

            with contact_col1:
                contact_data = {
                    'Method': ['Email', 'SMS', 'Phone Call', 'No Attempts'],
                    'Count': [contact_summary['email_attempts'],
                              contact_summary['sms_attempts'],
                              contact_summary['phone_attempts'],
                              contact_summary['no_contact']]
                }
                contact_df = pd.DataFrame(contact_data)

                fig3 = px.bar(contact_df, x='Method', y='Count',
                              title='Contact Attempts for Inactive Accounts',
                              color='Method')
                st.plotly_chart(fig3, use_container_width=True)

            with contact_col2:
                # Calculate percentage of accounts with each contact method
                total = contact_summary['total']
                if total > 0:
                    percentages = [
                        contact_summary['email_attempts'] / total * 100,
                        contact_summary['sms_attempts'] / total * 100,
                        contact_summary['phone_attempts'] / total * 100,
                        contact_summary['no_contact'] / total * 100
                    ]
                else:
                    percentages = [0, 0, 0, 0]

                fig4 = go.Figure(data=[
                    go.Bar(name='Percentage',
                           x=['Email', 'SMS', 'Phone Call', 'No Attempts'],
                           y=percentages)
                ])
                fig4.update_layout(title_text='Contact Attempt Coverage (%)')
                st.plotly_chart(fig4, use_container_width=True)

        with tab2:
            st.subheader("Account Details")

            # Filters
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.multiselect(
                    "Filter by Maturity Status",
                    options=df['Maturity Status'].unique(),
                    default=['Inactive']
                )

            with col2:
                branch_filter = st.multiselect(
                    "Filter by Branch",
                    options=df['Branch'].unique(),
                    default=df['Branch'].unique()
                )

            # Apply filters to FD accounts
            fd_accounts = df[df['Account Type'] == 'Fixed Deposit']

            if status_filter:
                fd_accounts = fd_accounts[fd_accounts['Maturity Status'].isin(status_filter)]

            if branch_filter:
                fd_accounts = fd_accounts[fd_accounts['Branch'].isin(branch_filter)]

            # Display the filtered dataframe
            st.dataframe(fd_accounts[[
                'Account ID', 'Branch', 'Customer Type', 'Account Balance',
                'Last Transaction Date', 'Years Since Last Transaction',
                'Maturity Status', 'Email Contact Attempt', 'SMS Contact Attempt', 'Phone Call Attempt'
            ]], use_container_width=True)

            # Download option
            st.markdown(get_download_link(fd_accounts, 'filtered_fd_accounts.csv', 'Download Filtered Data as CSV'),
                        unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error processing the file: {e}")
else:
    # Display sample data when no file is uploaded
    st.info("Please upload a CSV file to begin analysis.")

    # Show structure of expected CSV
    st.markdown("### Expected CSV Format:")
    sample_data = {
        'Account ID': ['ACC0001', 'ACC0002'],
        'Account Type': ['Fixed Deposit', 'Savings'],
        'Branch': ['Main Branch', 'Downtown'],
        'Customer Type': ['Individual', 'Business'],
        'Account Balance': [50000, 75000],
        'Last Transaction Date': ['2022-01-01', '2020-01-01'],
        'Email Contact Attempt': ['Yes', 'No'],
        'SMS Contact Attempt': ['Yes', 'Yes'],
        'Phone Call Attempt': ['No', 'Yes'],
        'Account Status': ['Dormant', 'Dormant']
    }
    st.dataframe(pd.DataFrame(sample_data))

# Footer
st.markdown("---")
st.markdown("© 2025 FD Inactivity Tracker")
