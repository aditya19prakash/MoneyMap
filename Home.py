import streamlit as st
from utility import add_bank_statement
from transaction import add_transaction
def home():
    menu=st.sidebar.selectbox(
        "Navigation",["add transactions","add Bank Statement","portfolio"]
    )
    if menu=="add Bank Statement":
          add_bank_statement()
    elif menu=="add transactions":
         add_transaction()
         