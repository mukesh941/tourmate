import asyncio, httpx
async def run():
  async with httpx.AsyncClient() as client:
    r = await client.get('http://127.0.0.1:8000/api/destinations?page=1&page_size=24')
    print(r.status_code)
    print(len(r.json()['data']['results']))
    print(r.json()['data']['total'])
asyncio.run(run())
