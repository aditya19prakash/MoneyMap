import streamlit as st
import pandas as pd

def add_bank_statement():
   uploader= st.file_uploader("add your bank statement in excel format",type=["xls","xlsx"])
   if uploader != None:
       try:
           if uploader.name.endswith(".xlsx"):
                df = pd.read_excel(uploader, engine="openpyxl") 
           else:
                df = pd.read_excel(uploader, engine="xlrd")
           st.write(df)
       except Exception as e:
           st.write(e)
   
