import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

MONGO_URI = "mongodb+srv://mukeshprasad9695_db_user:LCpsXsAIsbAgqcCR@cluster0.3cms1bv.mongodb.net/?appName=Cluster0"
DB_NAME = "tourmate"

# Change these to your admin credentials
ADMIN_EMAIL = "mukeshthakuru709@gmail.com"
ADMIN_PASSWORD = "mukesh123"  # Only used if creating a new user
ADMIN_NAME = "Mukesh (Admin)"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_or_promote_admin():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    existing = await db.users.find_one({"email": ADMIN_EMAIL})

    if existing:
        result = await db.users.update_one(
            {"email": ADMIN_EMAIL},
            {"$set": {"role": "admin", "is_admin": True}}
        )
        if result.modified_count:
            print(f"[SUCCESS] Promoted '{ADMIN_EMAIL}' to admin!")
        else:
            print(f"[INFO] '{ADMIN_EMAIL}' is already an admin.")
    else:
        # Create brand-new admin user
        password_hash = pwd_context.hash(ADMIN_PASSWORD)
        new_admin = {
            "name": ADMIN_NAME,
            "email": ADMIN_EMAIL,
            "password_hash": password_hash,
            "role": "admin",
            "is_admin": True,
        }
        await db.users.insert_one(new_admin)
        print(f"[SUCCESS] Created new admin account: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")

    print("\n--- Current Admins ---")
    async for u in db.users.find({"role": "admin"}, {"email": 1, "name": 1, "role": 1}):
        print(f"  {u.get('name', 'Unknown')} | {u['email']}")

    client.close()


asyncio.run(create_or_promote_admin())
