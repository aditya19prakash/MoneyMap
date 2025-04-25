import streamlit as st
import pandas as pd
import plotly.express as px
from database import users_collection
from datetime import date
from dateutil.relativedelta import relativedelta
import calendar

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

