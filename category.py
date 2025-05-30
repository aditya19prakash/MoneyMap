import streamlit as st
import pandas as pd
from database import users_collection
import time
from transaction import format_amount
from utility import check_internet_connection
# from ai_categorizer import train_model, load_model, predict_category

CATEGORY_OPTIONS = [
    "Income", "Money Transfer", "Investment", "Groceries", "Food & Drinks",
    "Shopping", "EMI", "Bills", "Other"
]

def extract_category(name):
    if not isinstance(name, str):
        return "Uncategorized"
    result = users_collection.find_one({"name": name})
    if result and "category" in result:
        return result["category"]
    return "Uncategorized"

def categorised():
    st.markdown("<h2 style='color: white;'>Categorise Transactions by Account Name</h2>", unsafe_allow_html=True)

    if not check_internet_connection():
        st.error("No internet connection. Please check your connection and try again.")
        return

    username = st.session_state.get("username")
    if not username:
        st.warning("Please log in to categorise transactions.")
        return

    user_data = users_collection.find_one({"username": username})
    if not user_data or "transactions" not in user_data:
        st.warning("No transaction data available.")
        return

    transactions_df = pd.DataFrame(user_data["transactions"])
    required_cols = ['Id', 'Category', 'Debit', 'Account Name', 'Payment Method']
    if not all(col in transactions_df.columns for col in required_cols):
        st.warning("Missing required columns in transaction data.")
        return

    uncategorised_df = transactions_df[transactions_df['Category'] == 'Uncategorized'].copy()

    # ----------------------- [2] Manual Categorisation -----------------------
    if not uncategorised_df.empty:
        with st.expander("🔍 View & Categorise Uncategorized Transactions", expanded=True):
            st.dataframe(uncategorised_df[['Id', 'Account Name', 'Description', 'Debit', 'Txn Date']])

            account_names_to_categorise = st.multiselect(
                "Select Account Names to categorise",
                uncategorised_df['Account Name'].unique().tolist()
            )

            new_category = st.selectbox("Select new category", CATEGORY_OPTIONS)
            if new_category == "Other":
                new_category = st.text_input("Enter custom category")

            if st.button("✅ Categorise Selected Names"):
                if account_names_to_categorise and new_category:
                    update_transactions(transactions_df, username, account_names_to_categorise, new_category)
                else:
                    st.warning("Please select account names and a category.")

            # # 🔄 AI Suggestion Preview
            # if st.button("🤖 Suggest Categories with AI"):
            #   model = train_model(transactions_df.to_dict("records"))
            #   if account_names_to_categorise:
            #       first_account = account_names_to_categorise[0]
            #       predicted_category = predict_category(
            #           model,
            #           first_account,
            #           0,  
            #           0,
            # ""
            #       )
            #       st.session_state["predicted_category"] = predicted_category
            #       st.success(f"🤖 AI Suggestion: {predicted_category}")
            #       if st.button("💾 Save AI Suggestions to Transactions"):
            #         if "predicted_category" in st.session_state and account_names_to_categorise:
            #           new_category = st.session_state["predicted_category"]
            #           update_transactions(transactions_df, username, account_names_to_categorise, new_category)
            #           del st.session_state["predicted_category"]
            #           time.sleep(1.5)
            #           st.rerun()
            #         else:
            #           st.warning("No AI suggestion found or no account names selected.")
           

               

    # ----------------------- [1] Rename Account Name -----------------------
    with st.expander("✏️ Rename Account Name"):
        account_names = transactions_df['Account Name'].dropna().unique().tolist()
        selected_name = st.selectbox("Select Account Name to Rename", account_names)
        new_name = st.text_input("Enter New Account Name")

        if st.button("🔁 Rename"):
            if selected_name and new_name and selected_name != new_name:
                transactions_df.loc[transactions_df["Account Name"] == selected_name, "Account Name"] = new_name
                users_collection.update_one(
                    {"username": username},
                    {"$set": {"transactions": transactions_df.to_dict("records")}}
                )
                if users_collection.find_one({"name": selected_name}):
                    users_collection.update_one({"name": selected_name}, {"$set": {"name": new_name}})
                st.success(f"Renamed '{selected_name}' to '{new_name}' in all transactions.")
                st.rerun()
            else:
                st.warning("Invalid or duplicate name entered.")

    # ----------------------- [3] Update Existing Categories -----------------------
    with st.expander("🔄 Update Existing Account Name Categories"):
        all_account_names = transactions_df['Account Name'].dropna().unique().tolist()
        selected_account_name = st.selectbox("Select Account Name to Update", all_account_names, key="update_select_account")

        if st.button("🔍 Check Current Category"):
            previous_category = extract_category(selected_account_name)
            st.info(f"Previous Category: {previous_category}")

        new_category_update = st.selectbox("Select New Category", CATEGORY_OPTIONS, key="update_select_category")
        if new_category_update == "Other":
            new_category_update = st.text_input("Enter custom new category")

        if st.button("🛠️ Update Category for Selected Account"):
            if selected_account_name and new_category_update:
                update_transactions(transactions_df, username, [selected_account_name], new_category_update, force_update=True)
            else:
                st.warning("Please select an account and a new category.")

    # ----------------------- [4] Spending Summary -----------------------
    st.subheader("Spending by Category")
    category_spending = transactions_df[transactions_df['Debit'] > 0].groupby('Category')['Debit'].sum().reset_index()
    if not category_spending.empty:
        category_spending["Debit"] = category_spending["Debit"].apply(format_amount)
        st.table(category_spending.rename(columns={'Debit': 'Total Spent'}))
        csv = category_spending.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name="transactions.csv", mime="text/csv")
    else:
        st.info("No spending data available.")

def update_transactions(transactions_df, username, account_names, new_category, force_update=False):
    updated_transactions = []
    updated_count = 0
    unique_updated_names = set()

    for index, row in transactions_df.iterrows():
        if row['Account Name'] in account_names and (force_update or row['Category'] == 'Uncategorized'):
            updated_transaction = row.to_dict()
            updated_transaction['Category'] = new_category
            updated_transactions.append(updated_transaction)

            account_name = updated_transaction.get('Account Name')
            existing_account = users_collection.find_one({"name": account_name})
            if not existing_account:
                users_collection.insert_one({"name": account_name, "category": new_category})
            elif existing_account.get("category") != new_category:
                users_collection.update_one({"name": account_name}, {"$set": {"category": new_category}})
            unique_updated_names.add(account_name)
            updated_count += 1
        else:
            updated_transactions.append(row.to_dict())

    users_collection.update_one(
        {"username": username},
        {"$set": {"transactions": updated_transactions}}
    )

    st.success(f"✅ Successfully updated {account_names[0]} to category: {new_category}")
    time.sleep(1.5)
    st.rerun()
