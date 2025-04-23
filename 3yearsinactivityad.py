import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import io
import base64


class AccountInactivityChecker:
    """
    A class to identify savings, call, and current accounts that have been inactive
    for a specified period (no customer-initiated transactions).
    """

    def __init__(self):
        """Initialize the checker"""
        self.accounts_df = None
        self.inactive_accounts = None
        self.today = datetime.now()

    def load_account_data(self, accounts_file):
        """Load account data from an uploaded file"""
        try:
            # Load accounts data
            self.accounts_df = pd.read_csv(accounts_file)

            # Convert Last Transaction Date to datetime
            self.accounts_df['Last Transaction Date'] = pd.to_datetime(self.accounts_df['Last Transaction Date'])

            return True
        except Exception as e:
            st.error(f"Error loading account data: {str(e)}")
            return False

    def identify_inactive_accounts(self, inactivity_years, account_types):
        """
        Identify accounts that have been inactive for the specified period.
        """
        if self.accounts_df is None:
            st.error("Error: Account data not loaded.")
            return None

        # Calculate the cutoff date
        cutoff_date = self.today - timedelta(days=inactivity_years * 365)

        # Filter accounts based on type and inactivity period
        inactive_accounts = self.accounts_df[
            (self.accounts_df['Account Type'].isin(account_types)) &
            (self.accounts_df['Last Transaction Date'] < cutoff_date)
            ].copy()

        # Add inactivity duration information
        inactive_accounts['days_inactive'] = (self.today - inactive_accounts['Last Transaction Date']).dt.days
        inactive_accounts['years_inactive'] = inactive_accounts['days_inactive'] / 365
        inactive_accounts['years_inactive'] = inactive_accounts['years_inactive'].round(2)

        # Sort by inactivity duration
        inactive_accounts = inactive_accounts.sort_values('days_inactive', ascending=False)

        self.inactive_accounts = inactive_accounts
        return inactive_accounts

    def categorize_by_inactivity(self, low_years, medium_years, high_years):
        """
        Categorize inactive accounts by inactivity duration.

        Parameters:
        -----------
        low_years : float
            Years of inactivity required for LOW category
        medium_years : float
            Years of inactivity required for MEDIUM category
        high_years : float
            Years of inactivity required for HIGH category

        Returns:
        --------
        pandas.DataFrame
            DataFrame with inactivity categories
        """
        if self.inactive_accounts is None or self.inactive_accounts.empty:
            st.warning("No inactive accounts to categorize.")
            return None

        # Make a copy to avoid SettingWithCopyWarning
        result_df = self.inactive_accounts.copy()

        # Define inactivity category based on duration
        def determine_category(years_inactive):
            if years_inactive > high_years:
                return 'HIGH'
            elif years_inactive > medium_years:
                return 'MEDIUM'
            elif years_inactive > low_years:
                return 'LOW'
            else:
                return 'MONITOR'

        result_df['inactivity_category'] = result_df['years_inactive'].apply(determine_category)

        # Add contact status
        def determine_contact_status(row):
            attempts = 0
            if row['Email Contact Attempt'] == 'Yes':
                attempts += 1
            if row['SMS Contact Attempt'] == 'Yes':
                attempts += 1
            if row['Phone Call Attempt'] == 'Yes':
                attempts += 1

            if attempts == 0:
                return 'No Contact'
            elif attempts < 3:
                return 'Partial Contact'
            else:
                return 'Full Contact'

        result_df['contact_status'] = result_df.apply(determine_contact_status, axis=1)

        # Add amount category based on account balance
        def determine_amount(balance):
            if balance > 300000:
                return 'HIGH'
            elif balance > 100000:
                return 'MEDIUM'
            else:
                return 'LOW'

        result_df['amount_category'] = result_df['Account Balance'].apply(determine_amount)

        return result_df

    def get_summary_stats(self):
        """Get summary statistics for the inactive accounts"""
        if self.inactive_accounts is None or self.inactive_accounts.empty:
            return None

        summary = {}

        # Count by account type
        summary['type_counts'] = self.inactive_accounts['Account Type'].value_counts().to_dict()

        # Count by branch
        summary['branch_counts'] = self.inactive_accounts['Branch'].value_counts().to_dict()

        # Count by customer type
        summary['customer_type_counts'] = self.inactive_accounts['Customer Type'].value_counts().to_dict()

        # Count by inactivity category
        if 'inactivity_category' in self.inactive_accounts.columns:
            summary['category_counts'] = self.inactive_accounts['inactivity_category'].value_counts().to_dict()

        # Count by amount category
        if 'amount_category' in self.inactive_accounts.columns:
            summary['amount_counts'] = self.inactive_accounts['amount_category'].value_counts().to_dict()

        # Count by contact status
        if 'contact_status' in self.inactive_accounts.columns:
            summary['contact_counts'] = self.inactive_accounts['contact_status'].value_counts().to_dict()

        # Calculate statistics for account balance
        summary['avg_balance'] = self.inactive_accounts['Account Balance'].mean()
        summary['total_balance'] = self.inactive_accounts['Account Balance'].sum()
        summary['max_balance'] = self.inactive_accounts['Account Balance'].max()
        summary['min_balance'] = self.inactive_accounts['Account Balance'].min()

        return summary


def get_download_link(df, filename, text):
    """Generate a download link for a dataframe"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">{text}</a>'
    return href


def main():
    # Set page title and layout
    st.set_page_config(
        page_title="Account Inactivity Checker",
        page_icon="💰",
        layout="wide",
    )

    # Create sidebar
    st.sidebar.title("Account Inactivity Checker")
    st.sidebar.markdown("Identify and analyze dormant accounts")

    # Initialize session state
    if 'checker' not in st.session_state:
        st.session_state.checker = AccountInactivityChecker()
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'categorized_results' not in st.session_state:
        st.session_state.categorized_results = None
    if 'summary_stats' not in st.session_state:
        st.session_state.summary_stats = None

    # Main app
    st.title("Account Inactivity Checker")
    st.markdown("Upload your account data to identify dormant accounts and generate reports.")

    # File upload section
    with st.sidebar.expander("📤 Upload Data", expanded=True):
        accounts_file = st.file_uploader("Upload Account CSV", type=['csv'])

    # Parameters section
    with st.sidebar.expander("⚙️ Configure Parameters", expanded=True):
        # Set parameter defaults
        inactivity_years = st.slider("Inactivity Period (Years)", min_value=1.0, max_value=10.0, value=3.0, step=0.5)

        # Account types to check
        all_account_types = ["Savings/Call/Current", "Fixed Deposit", "Investment", "Safe Deposit"]
        account_types = st.multiselect(
            "Account Types to Check",
            options=all_account_types,
            default=["Savings/Call/Current"]
        )

    # Categorization parameters
    with st.sidebar.expander("🔍 Categorization Parameters", expanded=True):
        low_years = st.number_input("Years for LOW Category", min_value=1.0, max_value=10.0, value=3.0, step=0.5)
        medium_years = st.number_input("Years for MEDIUM Category", min_value=1.0, max_value=10.0, value=4.0, step=0.5)
        high_years = st.number_input("Years for HIGH Category", min_value=1.0, max_value=10.0, value=5.0, step=0.5)

    # Process data if file is uploaded
    if accounts_file:
        checker = st.session_state.checker

        # Load data
        if checker.load_account_data(accounts_file):
            st.sidebar.success("Data loaded successfully!")

            # Run analysis button
            if st.sidebar.button("Run Analysis"):
                with st.spinner("Identifying inactive accounts..."):
                    # Perform analysis
                    results = checker.identify_inactive_accounts(
                        inactivity_years=inactivity_years,
                        account_types=account_types
                    )

                    if results is not None and not results.empty:
                        st.session_state.results = results

                        # Generate categorization
                        categorized_results = checker.categorize_by_inactivity(
                            low_years=low_years,
                            medium_years=medium_years,
                            high_years=high_years
                        )

                        if categorized_results is not None:
                            st.session_state.categorized_results = categorized_results

                            # Calculate summary statistics
                            st.session_state.summary_stats = checker.get_summary_stats()
                    else:
                        st.warning("No inactive accounts found with the specified criteria.")

    # Display results if available
    if st.session_state.results is not None and not st.session_state.results.empty:
        st.success(f"Found {len(st.session_state.results)} inactive accounts!")

        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Data Table", "Visualizations", "Export"])

        # Summary tab
        with tab1:
            if st.session_state.summary_stats:
                stats = st.session_state.summary_stats

                # Account statistics section
                st.header("Account Statistics")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Accounts", f"{len(st.session_state.results)}")
                    st.metric("Total Balance", f"AED {stats['total_balance']:,.2f}")

                with col2:
                    st.metric("Average Balance", f"AED {stats['avg_balance']:,.2f}")
                    st.metric("Maximum Balance", f"AED {stats['max_balance']:,.2f}")

                with col3:
                    if 'contact_counts' in stats:
                        st.metric("No Contact Made", f"{stats['contact_counts'].get('No Contact', 0)}")

                # Inactivity category section
                if 'category_counts' in stats:
                    st.header("Inactivity Categories")
                    category_cols = st.columns(4)

                    for i, (category, count) in enumerate(stats['category_counts'].items()):
                        with category_cols[i % 4]:
                            st.metric(f"{category}", f"{count}")

                # Amount category section
                if 'amount_counts' in stats:
                    st.header("Amount Profile")
                    amount_cols = st.columns(3)

                    for i, (amount, count) in enumerate(stats['amount_counts'].items()):
                        with amount_cols[i % 3]:
                            st.metric(f"{amount} Amount", f"{count}")

                # Distribution by account type
                st.header("Distribution by Account Type")
                type_cols = st.columns(len(stats['type_counts']))

                for i, (acc_type, count) in enumerate(stats['type_counts'].items()):
                    with type_cols[i]:
                        st.metric(f"{acc_type}", f"{count}")

                # Distribution by branch
                st.header("Distribution by Branch")
                branch_cols = st.columns(len(stats['branch_counts']))

                for i, (branch, count) in enumerate(stats['branch_counts'].items()):
                    with branch_cols[i]:
                        st.metric(f"{branch}", f"{count}")

                # Distribution by customer type
                st.header("Distribution by Customer Type")
                customer_cols = st.columns(len(stats['customer_type_counts']))

                for i, (cust_type, count) in enumerate(stats['customer_type_counts'].items()):
                    with customer_cols[i]:
                        st.metric(f"{cust_type}", f"{count}")

        # Data table tab
        with tab2:
            if st.session_state.categorized_results is not None:
                # Add filters
                st.subheader("Filter Options")
                filter_cols = st.columns(3)

                with filter_cols[0]:
                    account_type_filter = st.multiselect(
                        "Account Type",
                        options=st.session_state.categorized_results['Account Type'].unique(),
                        default=st.session_state.categorized_results['Account Type'].unique()
                    )

                with filter_cols[1]:
                    branch_filter = st.multiselect(
                        "Branch",
                        options=st.session_state.categorized_results['Branch'].unique(),
                        default=st.session_state.categorized_results['Branch'].unique()
                    )

                with filter_cols[2]:
                    customer_type_filter = st.multiselect(
                        "Customer Type",
                        options=st.session_state.categorized_results['Customer Type'].unique(),
                        default=st.session_state.categorized_results['Customer Type'].unique()
                    )

                # Second row of filters
                filter_cols2 = st.columns(2)

                with filter_cols2[0]:
                    if 'inactivity_category' in st.session_state.categorized_results.columns:
                        category_filter = st.multiselect(
                            "Inactivity Category",
                            options=st.session_state.categorized_results['inactivity_category'].unique(),
                            default=st.session_state.categorized_results['inactivity_category'].unique()
                        )
                    else:
                        category_filter = None

                with filter_cols2[1]:
                    if 'amount_category' in st.session_state.categorized_results.columns:
                        amount_filter = st.multiselect(
                            "Amount Category",
                            options=st.session_state.categorized_results['amount_category'].unique(),
                            default=st.session_state.categorized_results['amount_category'].unique()
                        )
                    else:
                        amount_filter = None

                # Apply filters
                filtered_df = st.session_state.categorized_results[
                    (st.session_state.categorized_results['Account Type'].isin(account_type_filter)) &
                    (st.session_state.categorized_results['Branch'].isin(branch_filter)) &
                    (st.session_state.categorized_results['Customer Type'].isin(customer_type_filter))
                    ]

                if category_filter:
                    filtered_df = filtered_df[filtered_df['inactivity_category'].isin(category_filter)]

                if amount_filter:
                    filtered_df = filtered_df[filtered_df['amount_category'].isin(amount_filter)]

                # Display table
                st.subheader("Inactive Accounts")
                st.dataframe(filtered_df, use_container_width=True)

        # Visualizations tab
        with tab3:
            if st.session_state.categorized_results is not None:
                st.subheader("Account Distribution Analysis")

                viz_cols = st.columns(2)

                with viz_cols[0]:
                    # Account type distribution
                    fig1 = px.pie(
                        st.session_state.categorized_results,
                        names='Account Type',
                        title='Distribution by Account Type',
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig1, use_container_width=True)

                    # Branch distribution
                    fig3 = px.bar(
                        st.session_state.categorized_results['Branch'].value_counts().reset_index(),
                        x='Branch',
                        y='count',
                        title='Distribution by Branch',
                        labels={'Branch': 'Branch', 'count': 'Count'},
                        color='Branch',
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    st.plotly_chart(fig3, use_container_width=True)

                with viz_cols[1]:
                    # Customer type distribution
                    fig2 = px.pie(
                        st.session_state.categorized_results,
                        names='Customer Type',
                        title='Distribution by Customer Type',
                        color_discrete_sequence=px.colors.qualitative.Safe
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                    # Contact status distribution
                    if 'contact_status' in st.session_state.categorized_results.columns:
                        fig4 = px.pie(
                            st.session_state.categorized_results,
                            names='contact_status',
                            title='Distribution by Contact Status',
                            color_discrete_sequence=px.colors.qualitative.Set1
                        )
                        st.plotly_chart(fig4, use_container_width=True)

                st.subheader("Inactivity Analysis")

                viz_cols2 = st.columns(2)

                with viz_cols2[0]:
                    # Inactivity category distribution
                    if 'inactivity_category' in st.session_state.categorized_results.columns:
                        fig5 = px.bar(
                            st.session_state.categorized_results['inactivity_category'].value_counts().reset_index(),
                            x='inactivity_category',
                            y='count',
                            title='Inactivity Categories',
                            labels={'inactivity_category': 'Category', 'count': 'Count'},
                            color='inactivity_category',
                            color_discrete_sequence=px.colors.qualitative.Vivid
                        )
                        st.plotly_chart(fig5, use_container_width=True)

                    # Amount category distribution
                    if 'amount_category' in st.session_state.categorized_results.columns:
                        fig6 = px.pie(
                            st.session_state.categorized_results,
                            names='amount_category',
                            title='Distribution by Amount Category',
                            color_discrete_sequence=px.colors.sequential.Plasma
                        )
                        st.plotly_chart(fig6, use_container_width=True)

                with viz_cols2[1]:
                    # Years inactive histogram
                    fig8 = px.histogram(
                        st.session_state.categorized_results,
                        x='years_inactive',
                        title='Distribution of Inactivity Period',
                        labels={'years_inactive': 'Years Inactive', 'count': 'Number of Accounts'},
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig8, use_container_width=True)

                st.subheader("Financial Analysis")

                # Account balance by account type box plot
                fig9 = px.box(
                    st.session_state.categorized_results,
                    x='Account Type',
                    y='Account Balance',
                    title='Account Balance by Account Type',
                    color='Account Type',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig9, use_container_width=True)

                viz_cols3 = st.columns(2)

                with viz_cols3[0]:
                    # Account balance by branch
                    fig10 = px.box(
                        st.session_state.categorized_results,
                        x='Branch',
                        y='Account Balance',
                        title='Account Balance by Branch',
                        color='Branch',
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    st.plotly_chart(fig10, use_container_width=True)

                with viz_cols3[1]:
                    # Account balance by customer type
                    fig11 = px.box(
                        st.session_state.categorized_results,
                        x='Customer Type',
                        y='Account Balance',
                        title='Account Balance by Customer Type',
                        color='Customer Type',
                        color_discrete_sequence=px.colors.qualitative.Safe
                    )
                    st.plotly_chart(fig11, use_container_width=True)

        # Export tab
        with tab4:
            if st.session_state.categorized_results is not None:
                st.subheader("Export Results")

                # Full report
                st.markdown("### Full Report")
                st.download_button(
                    label="Download Full Inactive Account Report (CSV)",
                    data=st.session_state.categorized_results.to_csv(index=False).encode('utf-8'),
                    file_name="inactive_accounts_full_report.csv",
                    mime="text/csv"
                )

                # Specialized reports
                st.markdown("### Specialized Reports")
                report_cols = st.columns(2)

                with report_cols[0]:
                    # High inactivity report
                    if 'inactivity_category' in st.session_state.categorized_results.columns:
                        high_df = st.session_state.categorized_results[
                            st.session_state.categorized_results['inactivity_category'] == 'HIGH'
                            ]

                        if not high_df.empty:
                            st.download_button(
                                label="Download High Inactivity Accounts (CSV)",
                                data=high_df.to_csv(index=False).encode('utf-8'),
                                file_name="inactive_accounts_high_category.csv",
                                mime="text/csv",
                                key="download_high"
                            )

                    # Savings/Call/Current report
                    savings_df = st.session_state.categorized_results[
                        st.session_state.categorized_results['Account Type'] == 'Savings/Call/Current'
                        ]

                    if not savings_df.empty:
                        st.download_button(
                            label="Download Savings/Call/Current Accounts (CSV)",
                            data=savings_df.to_csv(index=False).encode('utf-8'),
                            file_name="inactive_accounts_savings_call_current.csv",
                            mime="text/csv",
                            key="download_savings"
                        )

                with report_cols[1]:
                    # No contact report
                    if 'contact_status' in st.session_state.categorized_results.columns:
                        no_contact_df = st.session_state.categorized_results[
                            st.session_state.categorized_results['contact_status'] == 'No Contact'
                            ]

                        if not no_contact_df.empty:
                            st.download_button(
                                label="Download No Contact Accounts (CSV)",
                                data=no_contact_df.to_csv(index=False).encode('utf-8'),
                                file_name="inactive_accounts_no_contact.csv",
                                mime="text/csv",
                                key="download_no_contact"
                            )

                    # High amount report
                    if 'amount_category' in st.session_state.categorized_results.columns:
                        high_amount_df = st.session_state.categorized_results[
                            st.session_state.categorized_results['amount_category'] == 'HIGH'
                            ]

                        if not high_amount_df.empty:
                            st.download_button(
                                label="Download High Amount Accounts (CSV)",
                                data=high_amount_df.to_csv(index=False).encode('utf-8'),
                                file_name="inactive_accounts_high_amount.csv",
                                mime="text/csv",
                                key="download_high_amount"
                            )

                # Category-based reports
                if 'inactivity_category' in st.session_state.categorized_results.columns:
                    st.markdown("### Category-Based Reports")
                    category_report_cols = st.columns(3)

                    categories = st.session_state.categorized_results['inactivity_category'].unique()
                    for i, category in enumerate(categories):
                        with category_report_cols[i % 3]:
                            category_df = st.session_state.categorized_results[
                                st.session_state.categorized_results['inactivity_category'] == category
                                ]

                            if not category_df.empty:
                                st.download_button(
                                    label=f"Download {category} Accounts (CSV)",
                                    data=category_df.to_csv(index=False).encode('utf-8'),
                                    file_name=f"inactive_accounts_{category.lower()}.csv",
                                    mime="text/csv",
                                    key=f"download_{category}"
                                )


if __name__ == "__main__":
    main()
