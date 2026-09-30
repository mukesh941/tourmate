import asyncio
from app.services.ai_service import get_grounded_chat_response

async def run():
    resolved_loc = {
        'query': 'rr layout', 
        'resolved': True, 
        'source': 'openstreetmap', 
        'name': 'Ring Road', 
        'address': 'Ring Road, Bandu Soni Layout, Nagpur', 
        'latitude': 21.11, 
        'longitude': 79.05,
        'city': 'Nagpur'
    }
    res = get_grounded_chat_response("hii i want cafe near by rr layout", [], [], language="en", canonical_extra=None, resolved_loc=resolved_loc)
    print(res)

asyncio.run(run())
