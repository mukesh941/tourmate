import asyncio
from sqlalchemy import select, func
from app.core.db import AsyncSessionLocal
from app.models.sql.hotel import RoomType, Hotel

async def check():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Hotel.id, func.count(RoomType.id)).join(RoomType).group_by(Hotel.id))
        for row in res.all():
            print(f"Hotel {row[0]}: {row[1]} room types")

asyncio.run(check())
