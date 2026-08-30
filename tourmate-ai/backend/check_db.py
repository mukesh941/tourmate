import asyncio
from app.core.database import get_db

async def main():
    db = get_db()
    count = await db.tourist_places.count_documents({})
    print("PLACES:", count)

if __name__ == "__main__":
    asyncio.run(main())
