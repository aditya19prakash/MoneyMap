import time
import plotly.express as px
import pandas as pd
import streamlit as st
from datetime import datetime
from database import users_collection
from utility import check_internet_connection


def budget():
    st.markdown("<h3 style='color: white;'>Budget</h3>", unsafe_allow_html=True)
    try:
        if not check_internet_connection():
            st.error("No internet connection. Please check your connection and try again.")
            return None

        user_data = users_collection.find_one({"username": st.session_state["username"]})
        if not user_data or "transactions" not in user_data:
            st.warning("No transaction data available.")
            return

        df = pd.DataFrame(user_data["transactions"])

        if 'Txn Date' not in df.columns or ('Debit' not in df.columns and 'Credit' not in df.columns):
            st.warning("Missing required columns ('Txn Date', 'Debit', or 'Credit') in transaction data.")
            return

        df['date'] = pd.to_datetime(df['Txn Date'], format='%d-%m-%y', errors='coerce')
        df.dropna(subset=['date'], inplace=True)
        df['month'] = df['date'].dt.strftime('%B')
        df['year'] = df['date'].dt.year
        df['debit'] = pd.to_numeric(df['Debit'], errors='coerce').fillna(0)
        df['credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)
        df['amount'] = df['debit']
        df['category'] = df.get('Category', 'Uncategorized').str.lower().str.strip()

        years = sorted(df['year'].unique().tolist(), reverse=True)
        unique_months = sorted(df['month'].unique().tolist(), key=lambda m: datetime.strptime(m, '%B').month)

        if not years:
            st.warning("No data available")
            return

        selected_year = st.selectbox("Select Year", years, index=0 if not years else len(years) - 1)
        selected_month = st.selectbox("Select Month", unique_months, index=0)

        current_month = pd.to_datetime('today').strftime('%B')
        current_year = pd.to_datetime('today').year
        is_current_period = (selected_month == current_month and selected_year == current_year)
        is_previous_period = (selected_year < current_year) or (selected_year == current_year and unique_months.index(selected_month) < unique_months.index(current_month))

        current_df = df[(df['month'] == selected_month) & (df['year'] == selected_year) & (df['Debit'] > 0)]

        budget_record = users_collection.find_one(
            {"username": st.session_state["username"], "budget": {"$exists": True}},
            {"budget": 1}
        )
        existing_budgets = budget_record.get("budget", {}).get(f"{selected_year}_{selected_month}", {}) if budget_record else {}

        category_totals = current_df.groupby('category')['amount'].sum()

        budget_overview = pd.DataFrame({
            'Category': category_totals.index,
            'Spent': category_totals.values.astype(int),
            'Budget': [existing_budgets.get(category, 0.0) for category in category_totals.index],
        })
        budget_overview['Budget'] = budget_overview['Budget'].apply(
            lambda x: "Budget is not set" if x == 0 else f"{int(x)}"
        )
        budget_overview['Remaining'] = budget_overview['Budget'].apply(
            lambda x: 0 if x == "Budget is not set" else float(x)
        ) - budget_overview['Spent']
        budget_overview['Status'] = budget_overview['Remaining'].apply(
            lambda x: 'Within Budget' if x >= 0 else 'Exceeding Budget'
        )
        budget_overview['Remaining'] = budget_overview['Remaining'].astype(int)

        st.write(f"### Budget Overview for {selected_month} {selected_year}")
        st.table(budget_overview.round(2))
        if budget_overview.empty:
           pass
        else:
            csv = budget_overview.to_csv(index=False).encode('utf-8')
            st.download_button(
            label="Download Budget Table as CSV",
            data=csv,
            file_name=f'budget_overview_{selected_month}_{selected_year}.csv',
            mime='text/csv'
            )

        st.write("### Budget Usage")
        budget_overview['Color'] = budget_overview['Status'].map({'Within Budget': 'green', 'Exceeding Budget': 'red'})

        charts_per_row = 2
        categories = budget_overview['Category'].unique()
        figs = []

        for i in range(0, len(categories), charts_per_row):
            cols = st.columns(charts_per_row)
            for j in range(charts_per_row):
                if i + j < len(categories):
                    category = categories[i + j]
                    row = budget_overview[budget_overview['Category'] == category].iloc[0]
                    fig = px.pie(
                        names=['Spent', 'Remaining'],
                        values=[row['Spent'], max(0, row['Remaining'])],
                        color=['Spent', 'Remaining'],
                        color_discrete_map={'Spent': row['Color'], 'Remaining': 'lightgray'},
                        hole=0.5,
                        title=f" {row['Category'].title()} Budget Usage<br><sub>Status: {row['Status']}</sub>"
                    )

                    fig.update_traces(
                        hovertemplate='%{label}: %{value}<extra></extra>'
                    )
                    fig.update_layout(
                        annotations=[
                            dict(
                                text=f"<b>{row['Category']}</b>",
                                x=0.5,
                                y=0.5,
                                font_size=14,
                                showarrow=False
                            )
                        ],
                        showlegend=False,
                        width=350,
                        height=350
                    )
                    cols[j].plotly_chart(fig)
              

        if is_current_period:
            st.write("### Set Budget")
            budget_settings = {}
            all_categories = sorted(current_df['category'].unique())
            for category in all_categories:
                default_value = existing_budgets.get(category, 0.0)
                try:
                    input_value = st.text_input(
                        f"Budget for {category}",
                        value=str(int(default_value)) if default_value else ""
                    )
                    if input_value and input_value.replace(".", "").isdigit():
                        budget_settings[category] = float(input_value)
                    elif input_value != "":
                        st.error(f"Please enter a valid number for {category}")
                        budget_settings[category] = default_value
                    else:
                        budget_settings[category] = default_value
                except ValueError:
                    st.error(f"Invalid input for {category}. Using default value.")
                    budget_settings[category] = default_value

            if st.button("Save Budget"):
                if not check_internet_connection():
                    return
                budget_key = f"budget.{selected_year}_{selected_month}"
                users_collection.update_one(
                    {"username": st.session_state["username"]},
                    {"$set": {budget_key: budget_settings}}
                )
                st.success("Budget saved successfully!")
                time.sleep(2)
                st.rerun()
        elif is_previous_period:
            st.warning("Budget settings for previous months are locked. You can only view the overview.")

    except Exception as e:
        st.error(f"Error processing budget: {str(e)}")
