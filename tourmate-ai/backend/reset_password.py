import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

MONGO_URI = "mongodb+srv://mukeshprasad9695_db_user:LCpsXsAIsbAgqcCR@cluster0.3cms1bv.mongodb.net/?appName=Cluster0"
DB_NAME = "tourmate"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Change this to whatever password you want to use
NEW_PASSWORD = "mukesh123"
EMAIL = "mukeshthakuru709@gmail.com"


async def reset():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    new_hash = pwd_context.hash(NEW_PASSWORD)
    result = await db.users.update_one(
        {"email": EMAIL},
        {"$set": {"password_hash": new_hash}}
    )
    print("Modified count:", result.modified_count)
    if result.modified_count:
        print(f"Password successfully reset to: {NEW_PASSWORD}")
        print(f"You can now log in with: {EMAIL} / {NEW_PASSWORD}")
    else:
        print("No user was updated. Check the email address.")


asyncio.run(reset())
