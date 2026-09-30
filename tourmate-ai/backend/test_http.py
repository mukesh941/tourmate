import httpx
import asyncio

async def run():
    async with httpx.AsyncClient() as client:
        # We need to hit the real endpoint running in uvicorn on port 8000
        # Since it requires auth, we should either bypass it or login first
        pass

if __name__ == "__main__":
    asyncio.run(run())
