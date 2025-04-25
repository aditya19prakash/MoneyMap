import streamlit as st
from utility import add_bank_statement
from transaction import add_transaction,show_transactions
from portfolio import portfolio
from budget import budget
from category import categorised
def home():
    menu=st.sidebar.selectbox(
        "Navigation",["add transactions","Show Transactions","add Bank Statement","portfolio","Budget","categorised"]
    )
    if menu=="add Bank Statement":
        add_bank_statement()
    elif menu=="add transactions":
        add_transaction()
    elif menu=="Show Transactions":
        show_transactions()
    elif menu =="portfolio":
        portfolio()
    elif menu=="Budget":
        budget()
    elif menu =="categorised":
        categorised()
