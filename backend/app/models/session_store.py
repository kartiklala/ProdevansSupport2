# session_store.py
import time
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
user_collection = db["oauth_users"]


async def save_user(email, access_token, refresh_token, expires_in, api_domain, user_info):
    expire_at = int(time.time()) + expires_in
    await user_collection.update_one(
        {"email": email},
        {
            "$set": {
                "email": email,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expire_at,
                "api_domain": api_domain,
                "user_info": user_info,
            }
        },
        upsert=True
    )


async def get_user(email):
    return await user_collection.find_one({"email": email})


async def update_access_token(email, access_token, expires_in):
    expire_at = int(time.time()) + expires_in
    await user_collection.update_one(
        {"email": email},
        {"$set": {"access_token": access_token, "expires_at": expire_at}}
    )
