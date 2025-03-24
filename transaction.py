import streamlit as st
def add_transaction():
    col1, col2 = st.columns(2)
    with col1:
      st.markdown("<h3 style='color: white;'>Add Transaction</h3>", unsafe_allow_html=True)
      account_name = st.text_input("Account Name")
      amount_str = st.text_input("Amount")
      category = st.selectbox("Category", ["Income", "Expense"])
      payment_method = st.selectbox("Payment Method", ["Cash", "UPI", "Credit Card", "Debit Card", "Bank Transfer"])
    with col2:
        st.markdown("<h3 style='color: white;'>Transaction Details</h3>", unsafe_allow_html=True)
        date = st.date_input("Date")
        description = st.text_input("Description")
       
