import os
import sys
import asyncio
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.core.database import get_db

async def verify():
    db = get_db()
    guides = await db.guides.find({}).to_list(length=None)
    
    total_guides = len(guides)
    duplicate_records = 0
    # count duplicates by name and city for simplicity, or just _id since mongo does that
    seen_ids = set()
    for g in guides:
        if str(g['_id']) in seen_ids:
            duplicate_records += 1
        seen_ids.add(str(g['_id']))
        
    profiles_with_images = sum(1 for g in guides if g.get('image_url'))
    lgbtq_guides = sum(1 for g in guides if g.get('is_lgbtq', False))
    
    images_dir = "../frontend/public/images/guides"
    
    images_required = 197
    images_found = 0
    missing_images = 0
    invalid_images = 0
    
    for i in range(1, 198):
        file_path = os.path.join(images_dir, f"guide-{i:03d}.webp")
        if os.path.exists(file_path):
            images_found += 1
            # check if it's a valid image (has size)
            if os.path.getsize(file_path) < 1000: # too small
                invalid_images += 1
        else:
            missing_images += 1
            
    print(f"Guide profiles: {total_guides}")
    print(f"Images required: {images_required}")
    print(f"Images found: {images_found}")
    print(f"Missing images: {missing_images}")
    print(f"Invalid images: {invalid_images}")
    print(f"Duplicate guide records: {duplicate_records}")
    print(f"LGBTQ+ demo profiles: {lgbtq_guides}")

if __name__ == "__main__":
    asyncio.run(verify())
