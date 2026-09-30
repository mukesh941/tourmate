import json
import random
import pprint

# Load the data
from seed_hotels import HOTELS_SEED_DATA

def get_price(hotel_type):
    hotel_type = hotel_type.lower()
    if 'luxury' in hotel_type or 'palace' in hotel_type or 'stupa' in hotel_type or 'fortress' in hotel_type:
        return random.randint(3500, 7000)
    elif 'heritage' in hotel_type or 'resort' in hotel_type or 'retreat' in hotel_type or 'chalet' in hotel_type:
        return random.randint(2000, 4000)
    elif 'standard' in hotel_type:
        return random.randint(1200, 2500)
    else:
        return random.randint(700, 1500)

for hotel in HOTELS_SEED_DATA:
    hotel['currency'] = 'INR'
    
    base_price = get_price(hotel.get('hotel_type', ''))
    hotel['price_per_night_start'] = float(base_price)
    
    for i, room in enumerate(hotel['rooms']):
        room_price = base_price + (i * 1500) # escalate for better rooms
        room['price_per_night'] = float(room_price)
        
with open('seed_hotels.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
# We need to recreate seed_hotels.py
out = "import asyncio\nfrom app.core.database import get_db\n\nHOTELS_SEED_DATA = "
out += pprint.pformat(HOTELS_SEED_DATA, sort_dicts=False, width=120)

out += """

async def seed_hotels():
    db = get_db()
    print("Seeding All-India Hotels into MongoDB...")
    await db.hotels.delete_many({})
    result = await db.hotels.insert_many(HOTELS_SEED_DATA)
    print(f"Successfully seeded {len(result.inserted_ids)} All-India hotels into MongoDB!")

if __name__ == "__main__":
    asyncio.run(seed_hotels())
"""

with open('seed_hotels.py', 'w', encoding='utf-8') as f:
    f.write(out)

print("seed_hotels.py updated successfully.")
