import streamlit as st
import pandas as pd
from database import users_collection
from datetime import date
from dateutil.relativedelta import relativedelta

today = date.today()
three_months_ago = today - relativedelta(months=3)

def Portfolio():
    username = st.session_state["username"]
    if st.button("click"): 
     today = date.today()
     month_1_end = today - relativedelta(months=1, days=today.day)
     month_1_start = month_1_end - relativedelta(months=1, days=1)
     month_2_end = today - relativedelta(months=2, days=today.day)
     month_2_start = month_2_end - relativedelta(months=1, days=1)
     month_3_end = today - relativedelta(months=3, days=today.day)
     month_3_start = month_3_end - relativedelta(months=1, days=1)

     existing_records = users_collection.find_one({"username": st.session_state["username"]})
     filtered_data = existing_records.get("transactions", []) 

     monthly_data_month1 = [
        record for record in filtered_data
        if month_1_start <= record.get("Txn Date").date() <= month_1_end 
    ]

     monthly_data_month2 = [
        record for record in filtered_data
        if month_2_start <= record.get("Txn Date").date() <= month_2_end 
    ]

     monthly_data_month3 = [
        record for record in filtered_data
        if month_3_start <= record.get("Txn Date").date() <= month_3_end 
    ]

     st.write("Transactions for", month_3_start.strftime("%B %Y"), "to", month_3_end.strftime("%B %Y"), ":", monthly_data_month3)
     st.write("Transactions for", month_2_start.strftime("%B %Y"), "to", month_2_end.strftime("%B %Y"), ":", monthly_data_month2)
     st.write("Transactions for", month_1_start.strftime("%B %Y"), "to", month_1_end.strftime("%B %Y"), ":", monthly_data_month1)

    #return monthly_data_month1, monthly_data_month2, monthly_data_month3

if "username" in st.session_state:
    month1_transactions, month2_transactions, month3_transactions = portfolio()
else:
    st.warning("Please log in to view your portfolio.")