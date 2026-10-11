import asyncio
from app.core.database import get_db

async def run_audit():
    db = get_db()
    guides = await db.guides.find({}).to_list(length=1000)
    
    total = len(guides)
    males = 0
    females = 0
    others = 0
    missing = 0
    
    with_images = 0
    without_images = 0
    
    male_names = ["Arun", "Ravi", "Vikram", "Raj", "Sanjay"]
    female_names = ["Priya", "Sunita", "Lakshmi", "Anjali"]
    
    for g in guides:
        gender = g.get("gender")
        if not gender:
            missing += 1
        elif gender == "male":
            males += 1
        elif gender == "female":
            females += 1
        else:
            others += 1
            
        if g.get("image_url"):
            with_images += 1
        else:
            without_images += 1
            
    print(f"Total guides: {total}")
    print(f"Male: {males}")
    print(f"Female: {females}")
    print(f"Other/unspecified: {others}")
    print(f"Missing gender field: {missing}")
    print(f"Guides with images: {with_images}")
    print(f"Guides without images: {without_images}")
    
    # We will also print a few sample names to see what they look like
    print("\nSample male names from DB if we can guess:")
    for g in guides[:20]:
        print(f" - {g.get('name')} | gender: {g.get('gender')} | img: {bool(g.get('image_url'))}")
    
if __name__ == "__main__":
    asyncio.run(run_audit())
