from datetime import datetime
import streamlit as st
from database import users_collection
import random
import pandas as pd
from utility import check_internet_connection
def add_transaction():
    st.markdown("<h2 style='color: white;'>Add Transaction</h2>", unsafe_allow_html=True)
    if not check_internet_connection():
        st.error("No internet connection. Please check your connection and try again.")
        return None
    col1, col2 = st.columns(2)
    
    with col1:
        account_name = st.text_input("Account Name")
        transaction_type = st.radio("Transaction Type", ("Credit", "Debit"))
        amount_input = st.text_input("Amount")
        category = st.selectbox(
            "Category",
            ["Income", "Money Transfer", "Investment", "Groceries", "Food & Drinks", "Shopping", "EMI", "Bills", "Other"]
        )
        if category == "Other":
            category = st.text_input("Enter Custom Category")
        
        payment_method = st.selectbox(
            "Payment Method",
            ["Cash", "UPI", "Credit Card", "Debit Card", "Bank Transfer"]
        )

    with col2:
        date = st.date_input("Transaction Date")
        description = st.text_area("Description")

    if st.button("Save Transaction"):
        # Validation
        if not all([account_name, amount_input, category, payment_method, date, description]):
            st.warning("Please fill in all the required fields.")
            return
        
        try:
            amount_value = int(float(amount_input))
        except ValueError:
            st.error("Please enter a valid number for the amount.")
            return

        now = int(datetime.now().timestamp())
        random.seed(now)
        transaction_id = random.randint(1, 1_000_000)

        transaction_data = {
            "Id": transaction_id,
            "Account Name": account_name,
            "Credit": amount_value if transaction_type == "Credit" else None,
            "Debit": amount_value if transaction_type == "Debit" else None,
            "Category": category,
            "Payment Method": payment_method,
            "Txn Date": date.strftime("%d-%m-%y"),
            "Description": description
        }

        # Save transaction in MongoDB
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
    if not check_internet_connection():
        st.error("No internet connection. Please check your connection and try again.")
        return None
    username = st.session_state["username"]
    user = users_collection.find_one({"username": username}, {"transactions": 1, "_id": 0})

    if not user or "transactions" not in user or user["transactions"] is None:
        st.info("No transactions found!")
        return

    transactions = user["transactions"]

    st.header("View Transactions by Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date")
    with col2:
        end_date = st.date_input("End Date")

    filtered_by_date = []
       
    if st.button("Filter by Date"):
        for txn in transactions:
            txn_date = datetime.strptime(txn["Txn Date"], "%d-%m-%y").date()
            if start_date <= txn_date <= end_date:
                clean_txn = txn.copy()
                clean_txn["Credit"] = format_amount(clean_txn.get("Credit"))
                clean_txn["Debit"] = format_amount(clean_txn.get("Debit"))
                filtered_by_date.append(clean_txn)

        if filtered_by_date:
            filtered_by_date = sorted(filtered_by_date, key=lambda x: datetime.strptime(x["Txn Date"], "%d-%m-%y"))
            st.table(filtered_by_date)
            total_credit = sum(txn.get("Credit", 0) or 0 for txn in filtered_by_date)
            total_debit = sum(txn.get("Debit", 0) or 0 for txn in filtered_by_date)
            
            st.write(f"Transaction between {start_date} and {end_date}:")
            st.write(f"Total Credit: ₹{total_credit:,}")
            st.write(f"Total Debit: ₹{total_debit:,}")
            df = pd.DataFrame(filtered_by_date)
            csv = df.to_csv(index=False).encode('utf-8')
            file_name=f"transactions_{start_date}_to_{end_date}.csv"
            st.download_button("Download CSV", data=csv, file_name=file_name, mime="text/csv")
        else:
            st.info("No transactions found for the selected dates!")

    st.markdown("---")
    st.header("View Transactions by Account Name")
    account_names = list({txn.get('Account Name', 'Unknown') for txn in transactions})
    selected_account = st.selectbox("Select Account", account_names)
    
    col1, col2 = st.columns(2)
    with col1:
        acc_start_date = st.date_input("Start Date (Account)")
    with col2:
        acc_end_date = st.date_input("End Date (Account)")

    filtered_by_account = []

    if st.button("Filter by Account"):
        filtered_by_account = [
            {
                **txn,
                "Credit": format_amount(txn.get("Credit")),
                "Debit": format_amount(txn.get("Debit"))
            }
            for txn in transactions 
            if txn.get("Account Name") == selected_account 
            and acc_start_date <= datetime.strptime(txn["Txn Date"], "%d-%m-%y").date() <= acc_end_date
        ]
        if filtered_by_account:
            filtered_by_account = sorted(filtered_by_account, key=lambda x: datetime.strptime(x["Txn Date"], "%d-%m-%y"))
            st.table(filtered_by_account)
            df = pd.DataFrame(filtered_by_account)
            df['Id'] = df['Id'].astype(str)  # Convert Id column to string
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV (Account)", data=csv, file_name=f"{selected_account}transaction.csv", mime="text/csv")
            # Calculate total credit and debit
            total_credit = sum(txn.get("Credit", 0) or 0 for txn in filtered_by_account)
            total_debit = sum(txn.get("Debit", 0) or 0 for txn in filtered_by_account)
            
            st.write(f"For account '{selected_account}' between {acc_start_date} and {acc_end_date}:")
            st.write(f"Total Credit: ₹{total_credit:,}")
            st.write(f"Total Debit: ₹{total_debit:,}")
        else:
            st.info(f"No transactions found for account '{selected_account}'.")

def format_amount(amount):
    if pd.isna(amount):
        return ""
    return int(amount)
