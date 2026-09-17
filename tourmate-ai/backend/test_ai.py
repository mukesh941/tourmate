import asyncio
import json
import os
import sys

# Add the backend path
sys.path.append(r"c:\Users\hp\Documents\OneDrive\Desktop\tourmate-1\tourmate-ai\backend")

from app.services.ai_service import generate_itinerary_via_llm

try:
    result = generate_itinerary_via_llm(
        places_info=[],
        days=3,
        start_time="09:00",
        end_time="20:00",
        accommodation="Hotel",
        energy_level="Moderate",
        destination_name="Bengaluru",
        budget="Medium",
        travel_type="Family",
        transportation="Taxi/Car",
        interests=["Food", "Culture"]
    )
    print("SUCCESS")
    print(json.dumps(result, indent=2))
except Exception as e:
    print("FAILED")
    print(str(e))
