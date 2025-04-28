import datetime
import random
import streamlit as st
import pandas as pd
from database import users_collection
import socket
import logging
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
           df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').apply(convert_integer)
           df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').apply(convert_integer)
           df['Account Name'] = df['Description'].apply(extract_name)
           df['Payment Method'] =df['Description'].apply(extract_payment_method)
           df['Category'] =df["Account Name"].apply(extract_category)
           df['Id'] = df['Description'].apply(extract_transc_id)
           df.dropna(thresh=df.shape[1] - 1, inplace=True) 
           order = ['Id',"Txn Date", 'Account Name',"Category", "Description", "Debit", "Credit","Payment Method"]
           df=df[order]
           df.reset_index(drop=True, inplace=True)
           col1,col2 = st.columns([1,1])
           with col1:
               if st.button("Save Transaction"):
                   save_transaction(df)
           with col2:
             toggle_state = st.toggle("show Uploaded Transaction")
           if toggle_state:
            st.write(df)
       except Exception as e:
           st.write(e)


def convert_integer(data):
    if pd.isna(data):
        return None
    return int(data)


def extract_transc_id(description):
    description=str(description)
    parts = description.split('/')
    if len(parts) > 2:
        return parts[2].strip() 
    now = int(datetime.datetime.now().timestamp())
    random.seed(now)
    rand_num = random.randint(1, 1000000)
    return int(rand_num)


def save_transaction(df):
    df = df.where(pd.notnull(df), None)
    users_collection.find_one()
    records = df.to_dict('records')
    existing_user = users_collection.find_one({"username": st.session_state["username"]})
    if existing_user and "transactions" in existing_user:
        existing_ids = set(t["Id"] for t in existing_user["transactions"])
        records = [r for r in records if r["Id"] not in existing_ids]
    if not records:
        st.warning("All transactions already exist in database!")
        return
    for record in records:
        if record['Txn Date']:
            record['Txn Date'] = record['Txn Date'].strftime('%d-%m-%y')
    users_collection.update_one(
        {"username": st.session_state["username"]},
        {"$push": {"transactions": {"$each": records}}},
        upsert=True
    )
    st.success("Transactions saved successfully!")




def extract_category(name):
    if not isinstance(name, str):
        return "Uncategorized"
    result = users_collection.find_one({"name":name})
    if result and "category" in result:
        return result["category"]
    return "Uncategorized"



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

def check_internet_connection():
    """Checks internet connectivity by trying to connect to Google over port 443."""
    try:
        socket.create_connection(("www.google.com", 443), timeout=5)
        return True
    except OSError as e:
        logging.error(f"Error in check_internet_connection: {e}")
        return False