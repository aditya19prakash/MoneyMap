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
            # Prepare data for date-wise analysis
            month_filtered_df['Credit_Amount'] = month_filtered_df['Credit'].fillna(0)
            month_filtered_df['Debit_Amount'] = month_filtered_df['Debit'].fillna(0)
            
            # Group by date
            daily_summary = month_filtered_df.groupby('Day').agg({
                'Debit_Amount': 'sum',
                'Credit_Amount': 'sum'
            }).reset_index()
            
            daily_summary = daily_summary.sort_values('Day')
            daily_summary['Date'] = daily_summary['Day'].apply(
                lambda x: f"{selected_year}-{selected_month_num:02d}-{x:02d}"
            )
            
            st.subheader(f"📈 Daily Transactions for {month_names[selected_month_num]} {selected_year}")
            
            # Create bar chart for daily transactions
            fig_daily = px.bar(
                daily_summary,
                x='Date',
                y=['Debit_Amount', 'Credit_Amount'],
                labels={'Date': 'Date', 'value': 'Amount', 'variable': 'Transaction Type'},
                title=f'Daily Spending and Income - {month_names[selected_month_num]} {selected_year}',
                text_auto=True
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
            
            st.plotly_chart(fig_daily, use_container_width=True)
            
            # Summary statistics for the selected month
            col1, col2, col3, col4 = st.columns(4)
            
            total_debit = daily_summary['Debit_Amount'].sum()
            total_credit = daily_summary['Credit_Amount'].sum()
            net_amount = total_credit - total_debit
            avg_daily_spend = daily_summary['Debit_Amount'].mean()
            
            with col1:
                st.metric("Total Spending", f"₹{total_debit:,.2f}")
            with col2:
                st.metric("Total Income", f"₹{total_credit:,.2f}")
            with col3:
                st.metric("Net Amount", f"₹{net_amount:,.2f}", delta=f"{'Surplus' if net_amount >= 0 else 'Deficit'}")
            with col4:
                st.metric("Avg Daily Spend", f"₹{avg_daily_spend:,.2f}")
            
            # Detailed transaction table for the selected month
            with st.expander(f"📋 Detailed Transactions - {month_names[selected_month_num]} {selected_year}"):
                display_df = month_filtered_df[['Txn Date', 'Description', 'Category', 'Debit_Amount', 'Credit_Amount']].copy()
                display_df = display_df.sort_values('Txn Date')
                display_df['Debit_Amount'] = display_df['Debit_Amount'].apply(lambda x: f"₹{x:,.2f}" if x > 0 else "")
                display_df['Credit_Amount'] = display_df['Credit_Amount'].apply(lambda x: f"₹{x:,.2f}" if x > 0 else "")
                
                st.dataframe(
                    display_df,
                    column_config={
                        "Txn Date": "Date",
                        "Description": "Description",
                        "Category": "Category", 
                        "Debit_Amount": "Debit",
                        "Credit_Amount": "Credit"
                    },
                    hide_index=True,
                    use_container_width=True
                )
        else:
            st.info(f"No transactions found for {month_names[selected_month_num]} {selected_year}")
    else:
        st.info(f"No transactions found for {selected_year}")
