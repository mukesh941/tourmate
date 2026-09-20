import os
import google.generativeai as genai
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.services.rag_service import (
    is_route_or_distance_query,
    build_grounded_system_prompt,
    format_context_block,
)


def get_grounded_chat_response(
    user_message: str,
    history: List[Dict[str, str]],
    retrieved_chunks: List[Dict[str, Any]],
    language: str = "en",
) -> Dict[str, Any]:
    """
    Produces a grounded chat response with strict authority guardrails and source attribution.
    Uses Gemini in online mode if GEMINI_API_KEY is available; otherwise uses deterministic extractive synthesis.
    """
    # 1. Authority Guardrail: Prohibit road distance and route calculations
    if is_route_or_distance_query(user_message):
        return {
            "response": (
                "For accurate road distances, directions, and travel times, please use "
                "TourMate AI's Route Optimization feature on the Itinerary page, which "
                "computes verified OpenStreetMap road routes."
            ),
            "sources": [],
            "is_grounded": True,
        }

    # 2. Insufficient Evidence Refusal
    if not retrieved_chunks:
        return {
            "response": (
                "I do not have verified knowledge about that in my database. "
                "Please ask about our supported destinations (Agra, New Delhi, Jaipur, Mumbai) "
                "or specific landmarks such as Taj Mahal, Agra Fort, Qutub Minar, etc."
            ),
            "sources": [],
            "is_grounded": False,
        }

    # Prepare sources metadata
    sources = [
        {
            "id": c["id"],
            "title": c["title"],
            "source": c["source"],
            "poi_name": c.get("poi_name"),
            "similarity": c.get("similarity"),
        }
        for c in retrieved_chunks
    ]

    # 3. Online Grounded Mode via Gemini (if GEMINI_API_KEY is configured)
    api_key = settings.gemini_api_key
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model_name = settings.gemini_model
            model = genai.GenerativeModel(model_name)

            system_instruction = build_grounded_system_prompt(language)
            context_block = format_context_block(retrieved_chunks)

            contents = [
                {"role": "user", "parts": [f"{system_instruction}\n\n{context_block}"]},
                {"role": "model", "parts": ["Understood. I will formulate my answers strictly using the verified context provided."]},
            ]

            # Append past turns
            for msg in history[-6:]:  # Limit conversation window to last 6 turns
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({"role": role, "parts": [msg.get("content", "")]})

            # Append current question
            contents.append({"role": "user", "parts": [user_message]})

            res = model.generate_content(contents)
            answer_text = res.text.strip()
            if answer_text:
                return {
                    "response": answer_text,
                    "sources": sources,
                    "is_grounded": True,
                }
        except Exception as e:
            print(f"Gemini Grounded RAG Error, falling back to local synthesis: {e}")

    # 4. Deterministic Local Fallback (when GEMINI_API_KEY is absent or API fails)
    # Conservatively extracts facts from top retrieved chunks without hallucination
    primary_chunk = retrieved_chunks[0]
    extractive_lines = [primary_chunk["content"]]

    if len(retrieved_chunks) > 1 and retrieved_chunks[1]["similarity"] >= 0.50:
        extractive_lines.append(f"\nAdditionally ({retrieved_chunks[1]['title']}): {retrieved_chunks[1]['content']}")

    return {
        "response": "\n".join(extractive_lines),
        "sources": sources,
        "is_grounded": True,
    }


def get_ai_response(user_message: str, history: List[Dict[str, str]], context: str = None, language: str = 'en') -> str:
    api_key = settings.gemini_api_key
    if not api_key:
        return "Please add your GEMINI_API_KEY to the backend .env file to activate the AI Tour Guide."

    genai.configure(api_key=api_key)
    
    # Initialize the model
    model = genai.GenerativeModel(settings.gemini_model)
    
    # Construct the system prompt
    system_prompt = (
        "You are TourMate AI, an expert, friendly local travel guide. "
        "Your goal is to help users plan trips, recommend places, and give travel tips. "
        "Keep your answers concise, helpful, and enthusiastic."
    )
    
    if language == 'hi':
        system_prompt += "\n\nPlease always reply in Hindi."
    else:
        system_prompt += "\n\nPlease always reply in English."

    if context:
        system_prompt += f"\n\nThe user is currently looking at the following place, use this context if relevant:\n{context}"
        
    contents = []
    contents.append({"role": "user", "parts": [system_prompt]})
    contents.append({"role": "model", "parts": ["Understood! I am TourMate AI. How can I help you?"]})
    
    for msg in history:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append({
            "role": role,
            "parts": [msg.get("content", "")]
        })
        
    contents.append({
        "role": "user",
        "parts": [user_message]
    })
    
    try:
        response = model.generate_content(contents)
        return response.text
    except Exception as e:
        print(f"AI Error: {e}")
        return "I'm sorry, I'm having trouble thinking right now. Please try again later."

import json

def generate_itinerary_via_llm(places_info: List[Dict], days: int, start_time: str, end_time: str, accommodation: str = None, energy_level: str = "Moderate", destination_name: str = "", budget: str = "Medium", travel_type: str = "Family", transportation_mode: str = "flight", local_transportation: str = "taxi", interests: List[str] = [], origin: str = "") -> List[Dict]:
    api_key = settings.gemini_api_key
    if not api_key:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set in the backend .env file. Please restart the backend server if you recently added it.")

    genai.configure(api_key=api_key)
    
    gemini_model_name = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
    model = genai.GenerativeModel(gemini_model_name, generation_config={"response_mime_type": "application/json"})
    
    places_context = ""
    if places_info:
        places_context = f"You must prioritize including these specific places in the itinerary, distributing them logically:\n{json.dumps(places_info, indent=2)}\nIf database places are available, use their actual IDs."
    else:
        places_context = f"No specific places were provided. Please use your world knowledge to suggest the best, most popular landmarks, restaurants, and activities for a trip to {destination_name}."

    prompt = f"""
    You are an expert travel planner. Create realistic, detailed day-by-day itineraries for {days} days.
    The daily schedule should run roughly from {start_time} to {end_time}.
    The destination for this trip is: {destination_name if destination_name else 'Not specified'}
    
    CRITICAL CONSTRAINTS:
    - Origin / Starting Location: {origin if origin else 'Not specified'}
    - Inter-City Transportation Mode: {transportation_mode}
    - Local Transportation Mode: {local_transportation}
    - Accommodation/Starting Point: {accommodation if accommodation else 'Not specified. Assume a central downtown location.'}
    - Energy Level (Fatigue Limit): {energy_level}.
    - Budget: {budget}.
    - Travel Type: {travel_type}.
    - Interests: {', '.join(interests) if interests else 'General sightseeing'}
    
    {places_context}
    
    TRANSPORTATION RULES:
    You must estimate travel time, cost, and logistics for the selected transportation modes. Do not invent real flight numbers or precise live schedules. Explicitly add transportation steps (e.g. "Taxi to Airport", "Flight to Goa") into the daily timeline. 
    
    Generate exactly 3 DIFFERENT alternative route options:
    1. "Balanced" (Mix of sightseeing, food, culture, rest)
    2. "Explorer" (More activities, attractions, adventure)
    3. "Relaxed" (More free time, fewer locations, longer visits)
    
    The options must differ in number of places, activity density, and travel intensity.
    Include realistic travel times between places using {local_transportation} and do not overlap activities.
    
    Your response MUST be a valid JSON array of objects. Use this exact schema:
    [
      {{
        "route_name": "Balanced (or Explorer/Relaxed)",
        "description": "Brief description of this option",
        "total_estimated_cost": 5000,
        "transportation": {{
          "mode": "{transportation_mode}",
          "origin": "{origin if origin else destination_name}",
          "destination": "{destination_name}",
          "estimated_distance_km": 480.5,
          "estimated_duration_minutes": 120,
          "estimated_cost_min": 2000,
          "estimated_cost_max": 5000,
          "fuel_cost_estimate": 0,
          "toll_estimate": 0,
          "recommendation_note": "A short sentence explaining why this mode is suitable."
        }},
        "schedule": [
          {{
            "day": 1,
            "aiSummary": "Today's Plan: A mix of heritage and food...",
            "activities": [
              {{
                "start_time": "09:00",
                "end_time": "11:00",
                "place_id": "optional_id_if_provided",
                "name": "Activity, Place, or Transit Name (e.g. Flight to Goa)",
                "description": "Brief description",
                "activity_type": "sightseeing or transit",
                "estimated_cost": 200,
                "travel_time_minutes": 20,
                "rating": 4.5,
                "reviewCount": 120,
                "location": "City Center",
                "distance": "2.5 km away",
                "openingHours": "09:00 AM - 05:00 PM",
                "entryFee": "₹200",
                "aiReason": "Highly recommended for first-time visitors due to its historical significance.",
                "aiTips": ["Book tickets online", "Carry water"],
                "crowdLevel": "Medium",
                "weatherSuitability": "Good",
                "isOptional": false
              }}
            ]
          }}
        ]
      }}
    ]
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        import re
        match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()
        result = json.loads(text)
        return result
    except Exception as e:
        print(f"Itinerary AI Error: {e}")
        from fastapi import HTTPException
        if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e) or "quota" in str(e).lower():
            print("Falling back to mock itinerary due to rate limits...")
            return [
                {
                    "route_name": "Fallback AI Itinerary (Rate Limited)",
                    "description": "This is a placeholder itinerary generated because the AI API quota was exceeded.",
                    "total_estimated_cost": 5000,
                    "transportation": {
                        "mode": transportation_mode or "flight",
                        "origin": origin or destination_name,
                        "destination": destination_name or "Destination",
                        "estimated_distance_km": 500,
                        "estimated_duration_minutes": 120,
                        "estimated_cost_min": 2000,
                        "estimated_cost_max": 5000,
                        "fuel_cost_estimate": 0,
                        "toll_estimate": 0,
                        "recommendation_note": "Placeholder transportation due to API limits."
                    },
                    "schedule": [
                        {
                            "day": d + 1,
                            "aiSummary": f"Today's Plan: Enjoy a relaxing day exploring {destination_name or 'the area'}.",
                            "activities": [
                                {
                                    "start_time": "09:00",
                                    "end_time": "12:00",
                                    "name": f"Explore {destination_name or 'Destination'} (Morning)",
                                    "description": "Visit local attractions and landmarks.",
                                    "activity_type": "sightseeing",
                                    "estimated_cost": 500,
                                    "travel_time_minutes": 30,
                                    "rating": 4.0,
                                    "reviewCount": 50,
                                    "location": "Central Area",
                                    "distance": "Nearby",
                                    "openingHours": "08:00 AM - 06:00 PM",
                                    "entryFee": "₹100",
                                    "aiReason": "A great way to start the day.",
                                    "aiTips": ["Wear comfortable shoes."],
                                    "crowdLevel": "Low",
                                    "weatherSuitability": "Good",
                                    "isOptional": False
                                },
                                {
                                    "start_time": "13:00",
                                    "end_time": "16:00",
                                    "name": f"Explore {destination_name or 'Destination'} (Afternoon)",
                                    "description": "More sightseeing and activities.",
                                    "activity_type": "sightseeing",
                                    "estimated_cost": 500,
                                    "travel_time_minutes": 30,
                                    "rating": 4.2,
                                    "reviewCount": 75,
                                    "location": "Downtown",
                                    "distance": "3 km away",
                                    "openingHours": "09:00 AM - 05:00 PM",
                                    "entryFee": "Free",
                                    "aiReason": "Highly recommended afternoon activity.",
                                    "aiTips": ["Carry water."],
                                    "crowdLevel": "Medium",
                                    "weatherSuitability": "Fair",
                                    "isOptional": True
                                }
                            ]
                        } for d in range(days)
                    ]
                }
            ]
        raise HTTPException(status_code=500, detail="Failed to generate itinerary. Please try again.")

import io

# We will load the model lazily to avoid slowing down server startup
_mobilenet_model = None

def get_mobilenet_model():
    global _mobilenet_model
    if _mobilenet_model is None:
        try:
            from tensorflow.keras.applications import MobileNetV2
            _mobilenet_model = MobileNetV2(weights="imagenet")
        except Exception as e:
            print(f"MobileNet model load skipped: {e}")
            _mobilenet_model = None
    return _mobilenet_model

def predict_landmark_from_image(image_bytes: bytes) -> dict:
    from PIL import Image
    import numpy as np

    # 1. Prefer Gemini Vision if API key is provided
    api_key = settings.gemini_api_key
    if api_key:
        try:
            genai.configure(api_key=api_key)
            gemini = genai.GenerativeModel('gemini-2.5-flash')
            prompt = (
                "Identify the tourist place, monument, or landmark in this picture. "
                "Respond strictly with a JSON object in this format: "
                '{"name": "Landmark Name", "description": "2-3 sentences of engaging tourist facts."}'
            )
            image_part = {"mime_type": "image/jpeg", "data": image_bytes}
            res = gemini.generate_content([prompt, image_part], generation_config={"response_mime_type": "application/json"})
            data = json.loads(res.text)
            if data.get("name"):
                return data
        except Exception as e:
            print(f"Gemini landmark recognition fallback: {e}")

    # 2. Fallback to local MobileNetV2 if TensorFlow is installed
    try:
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")
        image = image.resize((224, 224))
        
        img_array = np.array(image)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        
        model = get_mobilenet_model()
        if model is not None:
            predictions = model.predict(img_array)
            decoded = decode_predictions(predictions, top=1)[0][0]
            predicted_label = decoded[1].replace("_", " ").title()
            return {
                "name": predicted_label,
                "description": f"This appears to be a {predicted_label}."
            }
    except Exception as e:
        print(f"MobileNet prediction fallback: {e}")

    return {
        "name": "Tourist Attraction",
        "description": "Historical monument or cultural landmark."
    }

def enrich_cluster_with_ai(places: List[Dict], user_interests: List[str] = []) -> dict:
    api_key = settings.gemini_api_key
    if not api_key:
        return {
            "cluster_name": "Area Cluster",
            "description": "A group of nearby attractions.",
            "categories": [],
            "reasons": []
        }

    genai.configure(api_key=api_key)
    gemini_model_name = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
    model = genai.GenerativeModel(gemini_model_name, generation_config={"response_mime_type": "application/json"})
    
    place_names = [p.get("name") for p in places if p.get("name")]
    place_cats = [p.get("category", {}).get("name") if p.get("category") else "" for p in places]
    
    prompt = f"""
    You are an expert local guide mapping out areas of a city. I have a geographic cluster containing the following places:
    Places: {', '.join(place_names)}
    Categories: {', '.join(filter(bool, place_cats))}
    
    User interests: {', '.join(user_interests) if user_interests else 'General Sightseeing'}
    
    Based on the actual places inside this cluster, give it a catchy, descriptive name and a short summary.
    Do NOT invent information that is not supported by the places provided.
    
    Respond STRICTLY with a valid JSON object using this schema:
    {{
      "cluster_name": "Name (e.g. Historic City Center, Food District)",
      "description": "1-2 sentence summary of this specific cluster of places.",
      "categories": ["list", "of", "relevant", "categories"],
      "reasons": ["1-2 reasons why this cluster matches the user interests or why it is a good group to visit together"]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        import re
        match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()
        result = json.loads(text)
        return result
    except Exception as e:
        print(f"Cluster Enrichment AI Error: {e}")
        return {
            "cluster_name": "Local District",
            "description": "A geographic cluster of attractions.",
            "categories": [],
            "reasons": ["Geographically close to each other"]
        }
