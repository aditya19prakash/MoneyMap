import streamlit as st
import pandas as pd

def add_bank_statement():
   uploader= st.file_uploader("add your bank statement in excel format",type=["xls","xlsx"])
   if uploader != None:
       try:
           if uploader.name.endswith(".xlsx"):
                df = pd.read_excel(uploader, engine="openpyxl", skiprows=19) 
           else:
                df = pd.read_excel(uploader, engine="xlrd")
           df = df.iloc[:, :6]
           df.columns = ["Txn Date", "Value Date", "Description", "Ref No./Cheque No.", "Debit", "Credit"]
           df.drop(columns=["Ref No./Cheque No.","Value Date"],inplace=True)
           df["Txn Date"] = pd.to_datetime(df["Txn Date"], errors='coerce').dt.date
           df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce')
           df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce')
           df['Account Name'] = df['Description'].apply(extract_name)
           df['Payment Method'] =df['Description'].apply(extract_payment_method)
           df.dropna(thresh=df.shape[1] - 1, inplace=True) 
           order = ["Txn Date", 'Account Name', "Description", "Debit", "Credit","Payment Method"]
           df=df[order]
           df.reset_index(drop=True, inplace=True)
           toggle_state = st.toggle("show Uploaded Transaction")
           if toggle_state:
             st.write(df)
       except Exception as e:
           st.write(e)
   
def extract_payment_method(description):
    if not isinstance(description, str):
        return "Unknown"
    if 'UPI' in description.upper():
        return "UPI" 
    elif 'CDM SERVICE CHARGES' in description.upper():
        return "Service Charges"
    elif 'CDM' in description.upper():
        return "Money Transfer"
    elif 'CHEQUE' in description.upper():
        return "Cheque"
    elif 'ATM' in description.upper():
        return "ATM"
    elif 'NEFT'in description.upper():
        return "NEFT"
    elif 'IMPS'in description.upper():
        return "IMPS"  
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