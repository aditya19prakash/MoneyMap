# import joblib
# import pandas as pd
# from sklearn.compose import ColumnTransformer
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.impute import SimpleImputer
# from sklearn.pipeline import Pipeline
# from sklearn.preprocessing import OneHotEncoder

# CATEGORY_OPTIONS = [
#     "Income", "Money Transfer", "Investment", "Groceries",
#     "Food & Drinks", "Shopping", "EMI", "Bills", "Other"
# ]

# MODEL_PATH = "category_model.pkl"

# def train_model(transactions):
#     df = pd.DataFrame(transactions)

#     df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce')
#     df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce')

#     # Relax filtering: keep all categories except missing essential info
#     df = df[~(
#         df['Account Name'].isna() |
#         df['Category'].isna() |
#         df['Payment Method'].isna()
#     )].copy()

#     print(f"Total transactions: {len(transactions)}")
#     print(f"Filtered training data size: {len(df)}")
#     print("Category distribution in training data:")
#     print(df['Category'].value_counts())

#     # Remove 'Uncategorized' only if there are enough other categories
#     non_uncat_df = df[df['Category'] != 'Uncategorized']
#     if len(non_uncat_df) < 10:
#         print("Warning: Not enough labeled data besides 'Uncategorized'. Training aborted.")
#         return None
#     else:
#         df = non_uncat_df

#     X = df[["Account Name", "Debit", "Credit", "Payment Method"]]
#     y = df["Category"]

#     categorical_features = ["Account Name", "Payment Method"]
#     numeric_features = ["Debit", "Credit"]

#     preprocessor = ColumnTransformer([
#         ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
#         ("num", SimpleImputer(strategy="constant", fill_value=0), numeric_features),
#     ])

#     model = Pipeline([
#         ("preprocessor", preprocessor),
#         ("classifier", RandomForestClassifier(random_state=42, class_weight='balanced'))
#     ])

#     model.fit(X, y)
#     joblib.dump(model, MODEL_PATH)
#     print("Model trained and saved.")
#     return model

# def load_model():
#     try:
#         model = joblib.load(MODEL_PATH)
#         print("Model loaded.")
#         return model
#     except FileNotFoundError:
#         print("Model file not found.")
#         return None

# def predict_category(model, account_name, debit, credit, payment_method) -> str:
#     if model is None:
#         print("No model available, returning 'Uncategorized'.")
#         return "Uncategorized"

#     input_df = pd.DataFrame([{
#         "Account Name": account_name if account_name else "Unknown",
#         "Debit": debit if pd.notna(debit) else 0,
#         "Credit": credit if pd.notna(credit) else 0,
#         "Payment Method": payment_method if payment_method else "Unknown"
#     }])
#     print(f"Predicting category for input: {input_df.to_dict(orient='records')[0]}")
#     try:
#         prediction = model.predict(input_df)[0]
#         print(f"Predicted category: {prediction}")
#         return prediction
#     except Exception as e:
#         print(f"Error during prediction: {e}")
#         return "Uncategorized"
