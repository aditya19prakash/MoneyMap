import streamlit as st
import pandas as pd
import plotly.express as px
from database import users_collection
from datetime import date
from dateutil.relativedelta import relativedelta
import calendar
from utility import check_internet_connection

def extract_amount(records, transaction_type="Debit"):
    total = 0
    for record in records:
        try:
            if transaction_type in record and record[transaction_type]:
                value = record[transaction_type]
                if pd.isna(value) or value == "nan" or value == "":
                    continue
                total += float(value)
        except Exception as e:
            st.warning(f"Error processing record {record.get('Id', 'unknown')} for {transaction_type}: {e}")
    return total


def portfolio():
    if not check_internet_connection():
        st.error("No internet connection. Please check your connection and try again.")
        return None
    
    username = st.session_state["username"]
    today = date.today()

    def get_month_range(months_ago):
        target = today - relativedelta(months=months_ago)
        start = date(target.year, target.month, 1)
        last_day = calendar.monthrange(target.year, target.month)[1]
        end = date(target.year, target.month, last_day)
        return start, end

    # Monthly Overview Section
    st.header("📊 Monthly Overview")
    
    m3_start, m3_end = get_month_range(3)
    m2_start, m2_end = get_month_range(2)
    m1_start, m1_end = get_month_range(1)
    current_start = date(today.year, today.month, 1)
    current_end = today

    month_ranges = [
        (m3_start.strftime("%b %Y"), m3_start, m3_end),
        (m2_start.strftime("%b %Y"), m2_start, m2_end),
        (m1_start.strftime("%b %Y"), m1_start, m1_end),
        (current_start.strftime("%b %Y"), current_start, current_end)
    ]
    month_data = {label: [] for label, _, _ in month_ranges}
    
    existing_records = users_collection.find_one({"username": username})
    if not existing_records or "transactions" not in existing_records:
        st.warning("No transactions found for this user.")
        return
    transactions = existing_records["transactions"]

    for record in transactions:
        txn_date_str = record.get("Txn Date")
        if txn_date_str:
            try:
                txn_date = pd.to_datetime(txn_date_str, format='%d-%m-%y').date()
                for label, start, end in month_ranges:
                    if start <= txn_date <= end:
                        month_data[label].append(record)
                        break
            except ValueError:
                st.error(f"Could not parse date: {txn_date_str} in record: {record.get('Id', 'N/A')}")

    month_labels = list(month_data.keys())
    debit_amounts = [extract_amount(month_data[month], "Debit") for month in month_data]
    credit_amounts = [extract_amount(month_data[month], "Credit") for month in month_data]

    df = pd.DataFrame({
        'Month': month_labels,
        'Debit': debit_amounts,
        'Credit': credit_amounts
    })

    fig = px.bar(
        df,
        x='Month',
        y=['Debit', 'Credit'],
        labels={'Month': 'Month', 'value': 'Amount', 'variable': 'Transaction Type'},
        title='Monthly Spending and Income Overview',
        text_auto=True,
        category_orders={"Month": month_labels}
    )

    fig.update_traces(
        width=0.3,
        opacity=0.8,
        textfont_size=12,
        textangle=0,
        textposition="outside",
    )

    fig.update_layout(
        width=800,
        height=500,
        font=dict(size=16),
        title_font_size=32,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor='rgb(204, 204, 204)',
            linewidth=0.8,
            tickfont=dict(size=20)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgb(204, 204, 204)',
            showline=True,
            linecolor='rgb(204, 204, 204)',
            linewidth=0.8,
            tickfont=dict(size=20)
        ),
        legend=dict(
            title="Transaction Type",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Category Analysis Section
    st.header("🔍 Category Analysis")
    
    df_all = pd.DataFrame(transactions)
    df_all['Txn Date'] = pd.to_datetime(df_all['Txn Date'], format='%d-%m-%y')
    df_all['Year'] = df_all['Txn Date'].dt.year
    df_all['Month'] = df_all['Txn Date'].dt.month
    df_all['Day'] = df_all['Txn Date'].dt.day

    if 'Debit' not in df_all.columns or 'Category' not in df_all.columns:
        st.error("Required fields (Debit or Category) missing in transactions.")
        return

    df_all['Amount'] = df_all['Debit'].fillna(0)

    available_years = sorted(df_all['Year'].unique(), reverse=True)
    selected_year = st.selectbox("Select Year", available_years)

    filtered_df = df_all[df_all['Year'] == selected_year]

    # Group by category
    category_summary = filtered_df.groupby('Category').agg({
        'Amount': 'sum'
    }).reset_index().sort_values('Amount', ascending=False)

    if category_summary.empty:
        st.info(f"No spending records found for {selected_year}.")
        return

    # Plot
    st.subheader(f"💰 Spending by Category for {selected_year}")
    fig = px.pie(
        category_summary,
        values='Amount',
        names='Category',
        title=f'Spending Distribution for {selected_year}'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Date-wise Analysis Section
    st.header("📅 Date-wise Analysis")
    
    # Month selection for date-wise view
    available_months = sorted(filtered_df['Month'].unique())
    month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 
                   5: 'May', 6: 'June', 7: 'July', 8: 'August',
                   9: 'September', 10: 'October', 11: 'November', 12: 'December'}
    
    if available_months:
        selected_month_num = st.selectbox(
            "Select Month for Date-wise View",
            available_months,
            format_func=lambda x: month_names[x]
        )
        
        # Filter data for selected month and year
        month_filtered_df = filtered_df[filtered_df['Month'] == selected_month_num].copy()
        
        if not month_filtered_df.empty:
            # Money range filter
            st.subheader("💰 Filter by Amount Range")
            col1, col2 = st.columns(2)
            
            with col1:
                min_amount = st.number_input(
                    "Minimum Amount (₹)", 
                    min_value=0.0, 
                    value=0.0, 
                    step=100.0,
                    key=f"min_amount_{selected_year}_{selected_month_num}"
                )
            
            with col2:
                max_amount = st.number_input(
                    "Maximum Amount (₹)", 
                    min_value=0.0, 
                    value=float(month_filtered_df['Debit'].fillna(0).max()) if not month_filtered_df['Debit'].isna().all() else 10000.0,
                    step=100.0,
                    key=f"max_amount_{selected_year}_{selected_month_num}"
                )
            
            # Apply amount filter
            if min_amount > 0 or max_amount < float(month_filtered_df['Debit'].fillna(0).max()):
                amount_filtered_df = month_filtered_df[
                    (month_filtered_df['Debit'].fillna(0) >= min_amount) & 
                    (month_filtered_df['Debit'].fillna(0) <= max_amount)
                ].copy()
                
                if amount_filtered_df.empty:
                    st.warning(f"No transactions found in the amount range ₹{min_amount:,.2f} - ₹{max_amount:,.2f}")
                    return
                
                # Show filter info
                st.info(f"Showing {len(amount_filtered_df)} transactions between ₹{min_amount:,.2f} and ₹{max_amount:,.2f}")
                month_filtered_df = amount_filtered_df
            # Prepare data for date-wise analysis
            month_filtered_df['Debit_Amount'] = month_filtered_df['Debit'].fillna(0)
            
            # Group by date
            daily_summary = month_filtered_df.groupby('Day').agg({
                'Debit_Amount': 'sum'
            }).reset_index()
            
            daily_summary = daily_summary.sort_values('Day')
            daily_summary['Date'] = daily_summary['Day'].apply(
                lambda x: f"{selected_year}-{selected_month_num:02d}-{x:02d}"
            )
            
            st.subheader(f"📈 Daily Spending for {month_names[selected_month_num]} {selected_year}")
            
            # Create bar chart for daily transactions
            fig_daily = px.bar(
                daily_summary,
                x='Date',
                y='Debit_Amount',
                labels={'Date': 'Date', 'Debit_Amount': 'Amount Spent'},
                title=f'Daily Spending - {month_names[selected_month_num]} {selected_year}',
                text_auto=True,
                color_discrete_sequence=['#FF6B6B']
            )
            
            fig_daily.update_traces(
                textfont_size=10,
                textangle=0,
                textposition="outside",
            )
            
            fig_daily.update_layout(
                width=1000,
                height=500,
                font=dict(size=12),
                title_font_size=20,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    showgrid=False,
                    showline=True,
                    linecolor='rgb(204, 204, 204)',
                    linewidth=0.8,
                    tickangle=45,
                    tickfont=dict(size=10)
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgb(204, 204, 204)',
                    showline=True,
                    linecolor='rgb(204, 204, 204)',
                    linewidth=0.8,
                    tickfont=dict(size=12)
                )
            )
            
            st.plotly_chart(fig_daily, use_container_width=True)
            
            # Summary statistics for the selected month
            col1, col2, col3 = st.columns(3)
            
            total_debit = daily_summary['Debit_Amount'].sum()
            avg_daily_spend = daily_summary['Debit_Amount'].mean()
            max_daily_spend = daily_summary['Debit_Amount'].max()
            
            with col1:
                st.metric("Total Spending", f"₹{total_debit:,.2f}")
            with col2:
                st.metric("Avg Daily Spend", f"₹{avg_daily_spend:,.2f}")
            with col3:
                st.metric("Max Daily Spend", f"₹{max_daily_spend:,.2f}")
            
            # Detailed transaction table for the selected month
            with st.expander(f"📋 Detailed Transactions - {month_names[selected_month_num]} {selected_year}"):
                display_df = month_filtered_df[['Txn Date', 'Description', 'Category', 'Debit_Amount']].copy()
                display_df = display_df[display_df['Debit_Amount'] > 0]  # Only show debit transactions
                display_df = display_df.sort_values('Txn Date')
                display_df['Debit_Amount'] = display_df['Debit_Amount'].apply(lambda x: f"₹{x:,.2f}")
                
                st.dataframe(
                    display_df,
                    column_config={
                        "Txn Date": "Date",
                        "Description": "Description",
                        "Category": "Category", 
                        "Debit_Amount": "Amount Spent"
                    },
                    hide_index=True,
                    use_container_width=True
                )
        else:
            st.info(f"No transactions found for {month_names[selected_month_num]} {selected_year}")
    else:
        st.info(f"No transactions found for {selected_year}")
