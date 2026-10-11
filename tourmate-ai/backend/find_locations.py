import asyncio
from app.core.db import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT id, name, image FROM locations WHERE name IN ('Agra Fort', 'Amer Fort', 'Basilica of Bom Jesus');"))
        for row in res.fetchall():
            print(row)

if __name__ == "__main__":
    asyncio.run(main())
