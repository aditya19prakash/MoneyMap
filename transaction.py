import streamlit as st
from database import users_collection

def add_transaction():
    st.markdown("<h2 style='color: white;'>Add Transaction</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
      account_name = st.text_input("Account Name")
      amount = st.text_input("Amount")
      category = st.selectbox("Category",["Income", "Send Money", "Investment", "Savings", "Loan", "Bills", "Other"])
      if category=="Other":
         category=st.text_input("Enter the category name")
      payment_method = st.selectbox("Payment Method", ["Cash", "UPI", "Credit Card", "Debit Card", "Bank Transfer"])
    with col2:
        date = st.date_input("Date")
        description = st.text_area("Description")
       
    if st.button("Save Transaction"):
        transaction_data = {
            "account_name": account_name,
            "amount": int(amount),
            "category": category,
            "payment_method": payment_method,
            "date": date.strftime("%d-%m-%y"),
            "description": description
        }

        users_collection.update_one(
            {"username":st.session_state["username"]},
            {"$push": {"transactions": transaction_data}},
            upsert=True
        )
        st.success("Transaction saved successfully!")
def show_transactions():
    """Show Transactions from User's Document"""
    if "username" not in st.session_state:
        st.warning("Please log in first!")
        return

    username = st.session_state["username"]
    user = users_collection.find_one({"username": username}, {"transactions": 1, "_id": 0})

    if not user or "transactions" not in user:
        st.info("No transactions found!")
    else:
        st.table(user["transactions"])  