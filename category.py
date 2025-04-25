import streamlit as st
import pandas as pd
from database import users_collection
from datetime import datetime

def extract_category(name):
    if not isinstance(name, str):
        return "Uncategorized"
    result = users_collection.find_one({"name": name})
    if result and "category" in result:
        return result["category"]
    return "Uncategorized"

def categorised():
    st.markdown("<h2 style='color: white;'>Categorise Transactions by Account Name</h2>", unsafe_allow_html=True)

    username = st.session_state.get("username")
    if not username:
        st.warning("Please log in to categorise transactions.")
        return

    user_data = users_collection.find_one({"username": username})
    if not user_data or "transactions" not in user_data:
        st.warning("No transaction data available.")
        return

    transactions_df = pd.DataFrame(user_data["transactions"])

    if 'Id' not in transactions_df.columns or 'Category' not in transactions_df.columns or 'Debit' not in transactions_df.columns or 'Account Name' not in transactions_df.columns:
        st.warning("Missing required columns ('Id', 'Category', 'Debit', 'Account Name') in transaction data.")
        return

    uncategorised_df = transactions_df[transactions_df['Category'] == 'Uncategorized'].copy()

    if uncategorised_df.empty:
        st.info("No uncategorised transactions found.")
        return

    st.subheader("Uncategorised Transactions")
    st.dataframe(uncategorised_df[['Id', 'Account Name', 'Description', 'Debit', 'Txn Date']])

    st.subheader("Categorise Transactions by Account Name")
    with st.form("categorise_by_name_form"):
        account_names_to_categorise = st.multiselect(
            "Select Account Names to categorise",
            uncategorised_df['Account Name'].unique().tolist()
        )
        new_category = st.selectbox(
            "Select new category for these Account Names",
            ["Income", "Money Transfer", "Investment", "Groceries", "Food & Drinks", "Shopping", "EMI", "Bills", "Other"]
        )
        if new_category == "Other":
            new_category = st.text_input("Enter the new category name")

        submitted = st.form_submit_button("Categorise Selected Names")

        if submitted and account_names_to_categorise and new_category:
            updated_transactions = []
            categorised_count = 0
            unique_categorised_names = set()

            for index, row in transactions_df.iterrows():
                if row['Account Name'] in account_names_to_categorise and row['Category'] == 'Uncategorized':
                    updated_transaction = row.to_dict()
                    updated_transaction['Category'] = new_category
                    updated_transactions.append(updated_transaction)
                    if row['Account Name'] not in unique_categorised_names:
                        # Save the category for this Account Name using "name" field
                        account_name = updated_transaction.get('Account Name')
                        existing_account = users_collection.find_one({"name": account_name})
                        if not existing_account:
                            users_collection.insert_one({"name": account_name, "category": new_category})
                        elif existing_account.get("category") != new_category:
                            users_collection.update_one({"name": account_name}, {"$set": {"category": new_category}})
                        unique_categorised_names.add(account_name)
                    categorised_count += 1
                else:
                    updated_transactions.append(row.to_dict())

            users_collection.update_one(
                {"username": username},
                {"$set": {"transactions": updated_transactions}}
            )
            st.success(f"Successfully categorised {categorised_count} transactions for the selected Account Names to '{new_category}' and saved the mapping(s) for future use.")
            st.rerun() # Refresh to show updated categories

    st.subheader("Spending by Category")
    category_spending = transactions_df[transactions_df['Debit'] > 0].groupby('Category')['Debit'].sum().reset_index()
    if not category_spending.empty:
        st.dataframe(category_spending.rename(columns={'Debit': 'Total Spent'}))
    else:
        st.info("No spending data available.")
