import asyncio
from sqlalchemy import text
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.db import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as s:
        res = await s.execute(text("UPDATE locations SET state = 'Uttar Pradesh' WHERE city = 'Agra' AND (state IS NULL OR state = '')"))
        await s.commit()
        print('Updated rows:', res.rowcount)
        check = await s.execute(text("SELECT count(*) FROM locations WHERE state IS NULL OR state = ''"))
        print('Remaining empty state count:', check.scalar())

if __name__ == '__main__':
    asyncio.run(main())
