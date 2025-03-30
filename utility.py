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
           df.columns = ["Txn Date", "Value Date", "Description", "Ref No./Cheque No.", "Debit", "Credit", "Balance"] + [f"Extra_{i}" for i in range(len(df.columns) - 7)]
           df = df.iloc[:, :7]
           df["Txn Date"] = pd.to_datetime(df["Txn Date"], errors='coerce')
           df["Value Date"] = pd.to_datetime(df["Value Date"], errors='coerce')
           df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce')
           df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce')
           df["Balance"] = pd.to_numeric(df["Balance"], errors='coerce')
           df.dropna(thresh=df.shape[1] - 3, inplace=True) 
           df.drop(columns=["Ref No./Cheque No.","Value Date"],inplace=True)
           st.write(df)
       except Exception as e:
           st.write(e)
   
   
