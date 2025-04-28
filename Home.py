import streamlit as st
from utility import add_bank_statement
from transaction import add_transaction,show_transactions
from portfolio import portfolio
from budget import budget
from category import categorised
def home():
    menu=st.sidebar.selectbox(
        "Navigation",["Add transactions","Show Transactions","Add Bank Statement","Portfolio","Budget","Categorised"]
    )
    if menu=="Add Bank Statement":
        add_bank_statement()
    elif menu=="Add transactions":
        add_transaction()
    elif menu=="Show Transactions":
        show_transactions()
    elif menu =="Portfolio":
        portfolio()
    elif menu=="Budget":
        budget()
    elif menu =="Categorised":
        categorised()
