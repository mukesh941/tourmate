import asyncio, httpx
async def run():
  async with httpx.AsyncClient() as client:
    r = await client.get('http://127.0.0.1:8000/api/destinations?page=1&page_size=2000')
    data = r.json()['data']['results']
    print([d['name'] for d in data if '4 Arm' in d['name'] or '7LC' in d['name']])
asyncio.run(run())
