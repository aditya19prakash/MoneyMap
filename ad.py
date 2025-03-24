from pymongo import MongoClient

# MongoDB connection string
MONGO_URI = "mongodb+srv://MoneyMap:W8Q2If6NZpW4DNU2@cluster0.vjlnd.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "MoneyMap_database"

try:
    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]  # Use the specified database

    print("✅ Connection Successful!")
    print("📂 Databases:", client.list_database_names())

    # Define login data
    login_data = {
        "username": "test_user",
        "password": "secure_password123"
    }

    # Insert into "users" collection
    users_collection = db["users"]
    result = users_collection.insert_one(login_data)

    print(f"✅ User added with ID: {result.inserted_id}")

    # Retrieve and print all login records
    print("\n📜 All Users:")
    for user in users_collection.find():
        print(user)

except Exception as e:
    print("❌ Connection Failed:", e)
