import requests
import json

url = "http://localhost:8000/itineraries/generate"

payload = {
  "destination_name": "Goa",
  "place_ids": [],
  "days": 2,
  "start_time": "09:00",
  "end_time": "20:00",
  "accommodation": "Taj Hotel",
  "energy_level": "Moderate",
  "budget": "Medium",
  "travel_type": "Family",
  "transportation": "Taxi/Car",
  "interests": ["Food", "Nature"]
}

# The route expects a Bearer token, but I don't have one.
# Wait, let's look at the route definition.
