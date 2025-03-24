import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

if not MONGO_URI or not DB_NAME:
    raise ValueError("MONGO_URI or DB_NAME is not set in .env!")

client = MongoClient(MONGO_URI)  
db = client[DB_NAME] 
users_collection = db["users"] 