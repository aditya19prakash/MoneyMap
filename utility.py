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
           df["Txn Date"] = pd.to_datetime(df["Txn Date"], errors='coerce').dt.date
           df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce')
           df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce')
           df["Balance"] = pd.to_numeric(df["Balance"], errors='coerce')
           df['Account Name'] = df['Description'].apply(extract_name)
           df.dropna(thresh=df.shape[1] - 3, inplace=True) 
           df.drop(columns=["Ref No./Cheque No.","Value Date"],inplace=True)
           desired_order = ["Txn Date", 'Account Name', "Description", "Debit", "Credit", "Balance"]
           df=df[desired_order]
           if st.button():
             toggle_state = st.toggle("show Uploaded Transaction")
           if toggle_state:
             st.write(df)
           else:
              st.warning("The button is OFF ❌")
       except Exception as e:
           st.write(e)
   
   
def extract_name(description):
    if not isinstance(description, str):
        return "Unknown"
    if 'DEBIT CARD' in description.upper():
        return "Debit Card" 
    elif 'CREDIT CARD' in description.upper():
        return "Credit Card" 
    parts = description.split('/')
    if len(parts) > 3:
        return parts[3].strip()  
    return "Unknown"