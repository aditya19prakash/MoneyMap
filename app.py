import streamlit as st
from Login import login
st.markdown("<h1 style='text-align: center; color: white;'>MoneyMap</h1>", unsafe_allow_html=True)
if "authenticate" not in st.session_state:
    st.session_state["authenticate"]=False
    
if "username" not in st.session_state:
    st.session_state["username"]=None
login()
