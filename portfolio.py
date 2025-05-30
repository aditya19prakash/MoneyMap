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
    existing_records = users_collection.find_one({"username": username})
    if not existing_records or "transactions" not in existing_records:
        st.warning("No transactions found for this user.")
        return
    transactions = existing_records["transactions"]
    df = pd.DataFrame(transactions)
    df['Txn Date'] = pd.to_datetime(df['Txn Date'], format='%d-%m-%y')
    df['Year'] = df['Txn Date'].dt.year

    if 'Debit' not in df.columns or 'Category' not in df.columns:
        st.error("Required fields (Debit or Category) missing in transactions.")
        return

    df['Amount'] = df['Debit'].fillna(0)

    available_years = sorted(df['Year'].unique(), reverse=True)
    selected_year = st.selectbox("Select Year", available_years)

    filtered_df = df[df['Year'] == selected_year]

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
