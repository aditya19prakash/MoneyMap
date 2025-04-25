import streamlit as st
from utility import add_bank_statement
from transaction import add_transaction,show_transactions
from portfolio import Portfolio
def home():
    menu=st.sidebar.selectbox(
        "Navigation",["add transactions","Show Transactions","add Bank Statement","portfolio"]
    )
    if menu=="add Bank Statement":
        add_bank_statement()
    elif menu=="add transactions":
        add_transaction()
    elif menu=="Show Transactions":
        show_transactions()
    elif menu =="portfolio":
        Portfolio()
    
