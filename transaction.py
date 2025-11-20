from datetime import datetime
import streamlit as st
import pandas as pd
from database import users_collection

# ------------------- ADD TRANSACTION --------------------

def add_transaction():
    st.markdown("<h2 style='color: white;'>Add Transaction</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        account_name = st.text_input("Account Name")
        transaction_type = st.radio("Transaction Type", ("Credit", "Debit"))
        amount_input = st.text_input("Amount")
        category = st.selectbox(
            "Category",
            ["Income", "Money Transfer", "Investment", "Groceries",
             "Food & Drinks", "Shopping", "EMI", "Bills", "Other"]
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
        if not all([account_name, amount_input, category, payment_method, date, description]):
            st.warning("Please fill in all fields.")
            return
        
        try:
            amount_value = float(amount_input)
        except:
            st.error("Invalid amount")
            return

        # Store datetime properly
        transaction_data = {
            "account": account_name,
            "type": transaction_type,
            "amount": amount_value,
            "category": category,
            "payment": payment_method,
            "date": datetime.combine(date, datetime.min.time()),
            "description": description
        }

        users_collection.update_one(
            {"username": st.session_state["username"]},
            {"$push": {"transactions": transaction_data}}
        )
        st.success("Transaction saved successfully!")

# ------------------- SHOW TRANSACTIONS --------------------

def show_transactions():
    if "username" not in st.session_state:
        st.warning("Please log in first!")
        return

    username = st.session_state["username"]

    st.header("View Transactions by Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date")
    with col2:
        end_date = st.date_input("End Date")

    if st.button("Filter by Date"):
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        pipeline = [
            {"$match": {"username": username}},
            {"$project": {
                "_id": 0,
                "transactions": {
                    "$filter": {
                        "input": "$transactions",
                        "as": "txn",
                        "cond": {
                            "$and": [
                                {"$gte": ["$$txn.date", start_dt]},
                                {"$lte": ["$$txn.date", end_dt]}
                            ]
                        }
                    }
                }
            }}
        ]

        result = list(users_collection.aggregate(pipeline))
        txns = result[0]["transactions"] if result else []

        if not txns:
            st.info("No transactions in this date range")
            return

        df = pd.DataFrame(txns)
        df["date"] = df["date"].dt.strftime("%d-%m-%Y")
        df_sorted = df.sort_values("date")

        st.table(df_sorted)

        # Totals
        st.write(f"Total Credit: ₹{df[df['type']=='Credit']['amount'].sum():,}")
        st.write(f"Total Debit: ₹{df[df['type']=='Debit']['amount'].sum():,}")

        # CSV download
        st.download_button(
            "Download CSV",
            df_sorted.to_csv(index=False),
            file_name=f"transactions_{start_date}_to_{end_date}.csv",
            mime="text/csv"
        )

    # ---------------- ACCOUNT-WISE FILTER ----------------

    st.markdown("---")
    st.header("View Transactions by Account Name")

    # Get distinct account names (fast)
    accounts_pipeline = [
        {"$match": {"username": username}},
        {"$unwind": "$transactions"},
        {"$group": {"_id": "$transactions.account"}}
    ]
    accounts_result = list(users_collection.aggregate(accounts_pipeline))
    account_names = [a["_id"] for a in accounts_result]

    selected_account = st.selectbox("Select Account", account_names)

    col1, col2 = st.columns(2)
    with col1:
        acc_start = st.date_input("Start Date (Account)")
    with col2:
        acc_end = st.date_input("End Date (Account)")

    if st.button("Filter by Account"):
        start_dt = datetime.combine(acc_start, datetime.min.time())
        end_dt = datetime.combine(acc_end, datetime.max.time())

        pipeline = [
            {"$match": {"username": username}},
            {"$unwind": "$transactions"},
            {"$match": {
                "transactions.account": selected_account,
                "transactions.date": {"$gte": start_dt, "$lte": end_dt}
            }},
            {"$replaceRoot": {"newRoot": "$transactions"}}
        ]

        txns = list(users_collection.aggregate(pipeline))

        if not txns:
            st.info("No transactions found for this account")
            return

        df = pd.DataFrame(txns)
        df["date"] = df["date"].dt.strftime("%d-%m-%Y")
        df_sorted = df.sort_values("date")

        st.table(df_sorted)

        # Totals
        st.write(f"Total Credit: ₹{df[df['type']=='Credit']['amount'].sum():,}")
        st.write(f"Total Debit: ₹{df[df['type']=='Debit']['amount'].sum():,}")

        st.download_button(
            "Download Account CSV",
            df_sorted.to_csv(index=False),
            file_name=f"{selected_account}_transactions.csv",
            mime="text/csv"
        )
