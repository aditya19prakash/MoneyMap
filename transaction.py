from datetime import datetime
import streamlit as st
from database import users_collection
import random

def add_transaction():
    st.markdown("<h2 style='color: white;'>Add Transaction</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        account_name = st.text_input("Account Name")
        transaction_type = st.radio("Choose transaction type", ("Credit", "Debit"))
        credit = debit = None
        if transaction_type == "Credit":
            credit = st.text_input("Credit")
        else:
            debit = st.text_input("Debit")
        category = st.selectbox("Category", ["Income", "Money Transfer", "Investment", "Groceries", "Food & Drinks", "Shopping", "EMI", "Bills", "Other"])
        if category == "Other":
            category = st.text_input("Enter the category name")
        payment_method = st.selectbox("Payment Method", ["Cash", "UPI", "Credit Card", "Debit Card", "Bank Transfer"])

    with col2:
        date = st.date_input("Date")
        description = st.text_area("Description")
    
    if st.button("Save Transaction"):
        if not account_name or not category or not payment_method or not date or not description:
            st.warning("Please provide all required fields to proceed.")
            return
        now = int(datetime.datetime.now().timestamp())
        random.seed(now)
        rand_num = random.randint(1, 1000000)
        transaction_data = {
            'Id': rand_num,
            'Account Name': account_name,
            "Credit": int(credit) if transaction_type == "Credit" and credit else None,
           "Debit": int(debit) if transaction_type == "Debit" and debit else None,
            "Category": category,
           "Payment Method": payment_method,
            "Txn Date": date.strftime("%d-%m-%y"),
            "Description": description
        }
        a = ["Txn Date", 'Account Name', "Category", "Description", "Debit", "Credit", "Payment Method"]
        users_collection.update_one(
            {"username": st.session_state["username"]},
            {"$push": {"transactions": transaction_data}},
            upsert=True
        )
        st.success("Transaction saved successfully!")

def show_transactions():
    if "username" not in st.session_state:
        st.warning("Please log in first!")
        return
    col1,col2=st.columns([1,1])
    with col1:
     start_date = st.date_input("Start Date")
    with col2:
     end_date = st.date_input("End Date") 
    if st.button("Show Transcation"):
      username = st.session_state["username"]
      user = users_collection.find_one({"username": username}, {"transactions": 1, "_id": 0})
      filtered_data=[]
      if not user or "transactions" not in user or user["transactions"] is None:
        st.info("No transactions found!")
      else:
        for transaction in user["transactions"]:
          txn_date = datetime.strptime(transaction['Txn Date'], "%d-%m-%y").date()
          if start_date <= txn_date <= end_date:
              filtered_data.append(transaction)
        if filtered_data==[]:
            st.info("No transactions found!")
        else:
              st.table(filtered_data)  