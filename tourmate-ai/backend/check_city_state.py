import asyncio
from sqlalchemy import text
from app.core.db import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as s:
        r = await s.execute(text("SELECT COUNT(*) FROM locations WHERE location_type = 'city' AND state != ''"))
        with_state = r.scalar()
        
        r2 = await s.execute(text("SELECT COUNT(*) FROM locations WHERE location_type = 'city' AND (state = '' OR state IS NULL)"))
        without_state = r2.scalar()
        
        r3 = await s.execute(text("SELECT name, state, city, parent_id FROM locations WHERE location_type = 'city' AND state != '' LIMIT 5"))
        with_s = r3.fetchall()
        
        r4 = await s.execute(text("SELECT name, state, city, parent_id FROM locations WHERE location_type = 'city' AND (state = '' OR state IS NULL) LIMIT 5"))
        without_s = r4.fetchall()
        
        print(f'Cities WITH state field: {with_state}')
        print(f'Cities WITHOUT state field: {without_state}')
        print('WITH state sample:')
        for row in with_s:
            print(f'  {row.name} | state={row.state} | parent_id={row.parent_id}')
        print('WITHOUT state sample:')
        for row in without_s:
            print(f'  {row.name} | state={row.state} | parent_id={row.parent_id}')
        
        # Check via parent_id chain
        r5 = await s.execute(text("""
            SELECT l.name, l.state, s.name as state_name 
            FROM locations l
            LEFT JOIN locations s ON l.parent_id = s.id
            WHERE l.location_type = 'city' AND (l.state = '' OR l.state IS NULL)
            AND s.id IS NOT NULL
            LIMIT 5
        """))
        via_parent = r5.fetchall()
        print('Cities with empty state but valid parent:')
        for row in via_parent:
            print(f'  {row.name} -> parent state: {row.state_name}')

asyncio.run(check())
