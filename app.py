import streamlit as st
from Login import login
st.markdown("<h1 style='text-align: center; color: white;'>MoneyMap</h1>", unsafe_allow_html=True)
if "authenticate" not in st.session_state:
    st.session_state["authenticate"]=False
col1,col2=st.columns([0.5,0.5])
if st.session_state["authenticate"]==True:
  with col2:
   if st.button("Logout", key="logout"):
      st.session_state.clear()
      st.markdown("<meta http-equiv='refresh' content='0; url=''>", unsafe_allow_html=True)

if "username" not in st.session_state:
    st.session_state["username"]=None
login()
