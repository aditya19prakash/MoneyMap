import datetime
import random
import streamlit as st
import pandas as pd
import socket
import logging
from database import users_collection


def add_bank_statement():
    uploader = st.file_uploader("Add your bank statement in Excel format", type=["xls", "xlsx"])
    
    if uploader:
        try:
            df = pd.read_excel(uploader, engine="openpyxl" if uploader.name.endswith(".xlsx") else "xlrd", skiprows=19)
            df = df.iloc[:, :6]
            df.columns = ["Txn Date", "Value Date", "Description", "Ref No./Cheque No.", "Debit", "Credit"]
            df.drop(columns=["Ref No./Cheque No.", "Value Date"], inplace=True)

            df["Txn Date"] = pd.to_datetime(df["Txn Date"], errors='coerce').dt.date
            df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').apply(convert_integer)
            df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').apply(convert_integer)

            df['Account Name'] = df['Description'].apply(extract_name)
            df['Payment Method'] = df['Description'].apply(extract_payment_method)
            df['Category'] = df["Account Name"].apply(extract_category)
            df['Id'] = df['Description'].apply(extract_transc_id)

            df.dropna(thresh=df.shape[1] - 1, inplace=True)
            order = ['Id', "Txn Date", 'Account Name', "Category", "Description", "Debit", "Credit", "Payment Method"]
            df = df[order].reset_index(drop=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Transaction"):
                    save_transaction(df)
            with col2:
                if st.toggle("Show Uploaded Transactions"):
                    st.write(df)

        except Exception as e:
            st.error(f"Error while processing file: {e}")


def convert_integer(value):
    return int(value) if pd.notna(value) else None


def extract_transc_id(description):
    try:
        parts = str(description).split('/')
        if len(parts) > 2:
            return parts[2].strip()
    except Exception:
        pass
    return random.randint(1, 1000000)


def save_transaction(df):
    username = st.session_state.get("username")
    if not username:
        st.warning("User not logged in.")
        return

    df = df.where(pd.notnull(df), None)
    records = df.to_dict("records")

    user = users_collection.find_one({"username": username})
    existing_ids = {txn["Id"] for txn in user.get("transactions", [])} if user else set()

    new_records = [r for r in records if r["Id"] not in existing_ids]

    if not new_records:
        st.warning("All transactions already exist in the database!")
        return

    for record in new_records:
        if record["Txn Date"]:
            record["Txn Date"] = record["Txn Date"].strftime('%d-%m-%y')

    users_collection.update_one(
        {"username": username},
        {"$push": {"transactions": {"$each": new_records}}},
        upsert=True
    )
    st.success("New transactions saved successfully!")


def extract_category(name):
    if not isinstance(name, str):
        return "Uncategorized"
    result = users_collection.find_one({"name": name}, {"category": 1})
    return result.get("category", "Uncategorized") if result else "Uncategorized"


def extract_payment_method(description):
    if not isinstance(description, str):
        return "Unknown"
    description_upper = description.upper()
    if "UPI" in description_upper:
        return "UPI"
    if "CDM SERVICE CHARGES" in description_upper:
        return "Service Charges"
    if "CDM" in description_upper:
        return "Money Transfer"
    if "CHEQUE" in description_upper:
        return "Cheque"
    if "ATM" in description_upper:
        return "ATM"
    if "NEFT" in description_upper:
        return "NEFT"
    if "IMPS" in description_upper:
        return "IMPS"
    return "Unknown"


def extract_name(description):
    if not isinstance(description, str):
        return "Unknown"
    description_upper = description.upper()
    if "DEBIT CARD" in description_upper:
        return "Debit Card"
    if "CREDIT CARD" in description_upper:
        return "Credit Card"
    parts = description.split('/')
    return parts[3].strip() if len(parts) > 3 else "Unknown"


def check_internet_connection():
    try:
        socket.create_connection(("www.google.com", 443), timeout=5)
        return True
    except OSError as e:
        logging.error(f"Error in check_internet_connection: {e}")
        return False
