import asyncio
import json
import os
import sys

sys.path.append(r"c:\Users\hp\Documents\OneDrive\Desktop\tourmate-1\tourmate-ai\backend")

from app.services.ai_service import generate_itinerary_via_llm

try:
    result = generate_itinerary_via_llm(
        places_info=[],
        days=2,
        start_time="09:00",
        end_time="20:00",
        accommodation="Resort",
        energy_level="Moderate",
        destination_name="Coorg",
        budget="Medium",
        travel_type="Friends",
        transportation_mode="car",
        local_transportation="bike",
        interests=["Nature", "Coffee Plantations"],
        origin="Bengaluru"
    )
    print("SUCCESS")
    print(json.dumps(result, indent=2))
except Exception as e:
    print("FAILED")
    print(str(e))
