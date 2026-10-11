import asyncio
import asyncpg
async def check():
    for p in ['postgres', 'root', 'admin', '1234', 'password', '']:
        try:
            await asyncpg.connect(f'postgresql://postgres:{p}@localhost:5432/postgres')
            print('Success:', p)
            return
        except Exception as e:
            print(f"Failed {p}: {e}")
            pass
    print('None worked')
asyncio.run(check())
