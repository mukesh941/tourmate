import asyncio
import hashlib
import random
from app.core.database import get_db

# Deterministic image pools
MALE_IMAGES = [
    "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1504257432389-52343af06ae3?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1531427186611-ecfd6d936c79?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1501196354995-cbb51c65aaea?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1521119989659-a83eee488004?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?auto=format&fit=crop&w=400&q=80"
]

FEMALE_IMAGES = [
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1554151228-14d9def656e4?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=400&q=80"
]

NEUTRAL_IMAGES = [
    "https://images.unsplash.com/photo-1515150144380-bca9f1650ed9?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1499996860827-1b6c085038ec?auto=format&fit=crop&w=400&q=80"
]

MALE_FIRST_NAMES = ["Aarav", "Vihaan", "Aditya", "Arjun", "Sai", "Reyansh", "Krishna", "Ishaan", "Shaurya", "Atharv", "Rahul", "Amit", "Raj", "Sanjay", "Vikram", "Arun"]
FEMALE_FIRST_NAMES = ["Aanya", "Diya", "Priya", "Ananya", "Ishita", "Sneha", "Kavya", "Riya", "Aarohi", "Saanvi", "Sunita", "Lakshmi", "Anjali", "Pooja", "Neha"]
LAST_NAMES = ["Sharma", "Singh", "Patel", "Kumar", "Gupta", "Reddy", "Joshi", "Bose", "Menon", "Rao", "Das", "Sengupta", "Sheikh", "Gill", "Ahluwalia"]

def deterministic_choice(choices, seed):
    h = int(hashlib.md5(seed.encode('utf-8')).hexdigest(), 16)
    return choices[h % len(choices)]

async def run_fix():
    db = get_db()
    guides = await db.guides.find({}).to_list(length=1000)
    
    for g in guides:
        gid = str(g["_id"])
        
        # Assign deterministic gender if missing
        gender = g.get("gender")
        if not gender:
            gender = deterministic_choice(["male", "female", "male", "female", "other"], gid)
        
        updates = {"gender": gender}
        
        # Assign image based on gender
        if gender == "male":
            img = deterministic_choice(MALE_IMAGES, gid)
        elif gender == "female":
            img = deterministic_choice(FEMALE_IMAGES, gid)
        else:
            img = deterministic_choice(NEUTRAL_IMAGES, gid)
            
        updates["image_url"] = img
        
        # If demo, rename
        if g.get("is_demo", True):
            # Check if name is already appropriate? Better to just re-assign deterministically based on gender to be safe.
            last_name = deterministic_choice(LAST_NAMES, gid)
            if gender == "male":
                first_name = deterministic_choice(MALE_FIRST_NAMES, gid)
            elif gender == "female":
                first_name = deterministic_choice(FEMALE_FIRST_NAMES, gid)
            else:
                first_name = deterministic_choice(MALE_FIRST_NAMES + FEMALE_FIRST_NAMES, gid)
            
            updates["name"] = f"{first_name} {last_name}"
            
        # Update db
        await db.guides.update_one({"_id": g["_id"]}, {"$set": updates})

    print("Fix completed.")

if __name__ == "__main__":
    asyncio.run(run_fix())
