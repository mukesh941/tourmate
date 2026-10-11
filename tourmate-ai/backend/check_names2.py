import asyncio
from app.core.database import get_db

MALE_FIRST_NAMES = ['Aarav', 'Vihaan', 'Aditya', 'Arjun', 'Sai', 'Reyansh', 'Krishna', 'Ishaan', 'Shaurya', 'Atharv', 'Rahul', 'Amit', 'Raj', 'Sanjay', 'Vikram', 'Arun']
FEMALE_FIRST_NAMES = ['Aanya', 'Diya', 'Priya', 'Ananya', 'Ishita', 'Sneha', 'Kavya', 'Riya', 'Aarohi', 'Saanvi', 'Sunita', 'Lakshmi', 'Anjali', 'Pooja', 'Neha']

async def run():
  db = get_db()
  guides = await db.guides.find({}).to_list(1000)
  for g in guides:
    first_name = g.get('name', '').split(' ')[0]
    gender = g.get('gender')
    if gender == 'male' and first_name in FEMALE_FIRST_NAMES:
      print(f'MISMATCH: {g.get("name")} | {gender}')
    elif gender == 'female' and first_name in MALE_FIRST_NAMES:
      print(f'MISMATCH: {g.get("name")} | {gender}')
asyncio.run(run())
