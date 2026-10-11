import asyncio
from app.core.database import get_db
async def run():
  db = get_db()
  guides = await db.guides.find({}).to_list(1000)
  for g in guides[:20]:
    print(f'{g.get("name")} | {g.get("gender")}')
asyncio.run(run())
