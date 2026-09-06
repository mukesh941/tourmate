"""
Quick script to test login via the running FastAPI server.
Run with: python test_login.py
"""
import asyncio
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

MONGO_URI = "mongodb+srv://mukeshprasad9695_db_user:LCpsXsAIsbAgqcCR@cluster0.3cms1bv.mongodb.net/?appName=Cluster0"
DB_NAME = "tourmate"
EMAIL = "mukeshthakuru709@gmail.com"
TEST_PASSWORD = "mukesh123"


async def main():
    # 1. Check raw DB password hash
    print("=== Checking DB ===")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    user = await db.users.find_one({"email": EMAIL})
    if not user:
        print("ERROR: User not found in DB!")
        return

    stored_hash = user.get("password_hash", "")
    print(f"Stored hash (first 30 chars): {stored_hash[:30]}...")

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    match = pwd_context.verify(TEST_PASSWORD, stored_hash)
    print(f"Password '{TEST_PASSWORD}' matches stored hash: {match}")

    # 2. Test the actual HTTP login endpoint
    print("\n=== Testing HTTP Login Endpoint ===")
    try:
        async with httpx.AsyncClient() as http:
            resp = await http.post(
                "http://localhost:8000/api/auth/login",
                json={"email": EMAIL, "password": TEST_PASSWORD},
                timeout=10,
            )
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:300]}")
    except Exception as e:
        print(f"HTTP request failed: {e}")


asyncio.run(main())
