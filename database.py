from pymongo import MongoClient
MONGO_URI="mongodb+srv://MoneyMap:W8Q2If6NZpW4DNU2@cluster0.vjlnd.mongodb.net/?retryWrites=true&w=majority"
DB_NAME="MoneyMap_database"


if not MONGO_URI or not DB_NAME:
    raise ValueError("MONGO_URI or DB_NAME is not set in .env!")

client = MongoClient(MONGO_URI)  
db = client[DB_NAME] 
users_collection = db["users"] 

# users_collection.update_one(
#      {"username": "aditya"},
#      {"$unset": {"transactions": ""}}
#  )