import asyncio
from app.core.database import get_db, close_client
from bson import ObjectId

demo_guides = [
    {
        "name": "Demo Guide — Bengaluru",
        "location": "Bengaluru, Karnataka",
        "bio": "Local tourism guide demo profile for exploring Bengaluru's tech parks and gardens.",
        "languages": ["English", "Kannada", "Hindi"],
        "hourly_rate": 600,
        "rating": 4.5,
        "verified": False,
        "is_demo": True,
        "image_url": "https://images.unsplash.com/photo-1544717302-de2939b7ef71",
        "reviews_count": 12
    },
    {
        "name": "Demo Guide — Jaipur",
        "location": "Jaipur, Rajasthan",
        "bio": "Local tourism guide demo profile for exploring Jaipur's heritage and culture.",
        "languages": ["English", "Hindi"],
        "hourly_rate": 800,
        "rating": 4.8,
        "verified": False,
        "is_demo": True,
        "image_url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7",
        "reviews_count": 45
    },
    {
        "name": "Demo Guide — Kochi",
        "location": "Kochi, Kerala",
        "bio": "Local tourism guide demo profile for exploring Kerala backwaters.",
        "languages": ["English", "Malayalam"],
        "hourly_rate": 700,
        "rating": 4.9,
        "verified": False,
        "is_demo": True,
        "image_url": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80",
        "reviews_count": 89
    },
    {
        "name": "Demo Guide — Goa",
        "location": "Panaji, Goa",
        "bio": "Local tourism guide demo profile for exploring Goa beaches and churches.",
        "languages": ["English", "Konkani"],
        "hourly_rate": 500,
        "rating": 4.6,
        "verified": False,
        "is_demo": True,
        "image_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d",
        "reviews_count": 34
    }
]

async def seed_guides():
    db = get_db()
    await db.guides.delete_many({"is_demo": True})
    for guide in demo_guides:
        await db.guides.insert_one(guide)
    print(f"Seeded {len(demo_guides)} guides.")
    close_client()

if __name__ == "__main__":
    asyncio.run(seed_guides())
