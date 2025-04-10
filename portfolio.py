import streamlit as st 
import pandas as pd
from database import users_collection
from datetime import date
from dateutil.relativedelta import relativedelta

today = date.today()
three_months_ago = today - relativedelta(months=3)
def portfolio():
     username = st.session_state["username"]
     today=date.today()
     month_1 = today - relativedelta(months=3)
     month_2 = today - relativedelta(months=2)
     month_3 = today - relativedelta(months=1)
     
