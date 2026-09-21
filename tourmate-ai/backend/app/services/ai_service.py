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

def _build_fallback_itineraries(
    places_info: List[Dict],
    days: int,
    start_time: str,
    end_time: str,
    accommodation: str = None,
    energy_level: str = "Moderate",
    destination_name: str = "",
    budget: str = "Medium",
    travel_type: str = "Family",
    transportation_mode: str = "flight",
    local_transportation: str = "taxi",
    interests: List[str] = [],
    origin: str = ""
) -> List[Dict]:
    dest = destination_name or "Destination"
    orig = origin or dest
    mode = transportation_mode or "car"
    num_days = max(1, int(days))

    transportation = {
        "mode": mode,
        "origin": orig,
        "destination": dest,
        "estimated_distance_km": 240.0,
        "estimated_duration_minutes": 180,
        "estimated_cost_min": 1500,
        "estimated_cost_max": 4000,
        "fuel_cost_estimate": 600,
        "toll_estimate": 250,
        "recommendation_note": f"Recommended {mode} travel between {orig} and {dest}."
    }

    def create_activity(p_info, start_h, end_h, default_name, default_desc, is_opt=False):
        if p_info:
            return {
                "start_time": f"{start_h:02d}:00",
                "end_time": f"{end_h:02d}:00",
                "place_id": p_info.get("id"),
                "name": p_info.get("name", default_name),
                "description": p_info.get("description", default_desc),
                "activity_type": "sightseeing",
                "estimated_cost": 250,
                "travel_time_minutes": 20,
                "rating": 4.6,
                "reviewCount": 140,
                "location": dest,
                "distance": "Nearby",
                "openingHours": "09:00 AM - 05:00 PM",
                "entryFee": "₹200",
                "aiReason": f"Iconic highlight suited for {travel_type.lower()} travelers.",
                "aiTips": ["Book tickets online", "Carry water"],
                "crowdLevel": "Medium",
                "weatherSuitability": "Good",
                "isOptional": is_opt
            }
        return {
            "start_time": f"{start_h:02d}:00",
            "end_time": f"{end_h:02d}:00",
            "place_id": None,
            "name": f"{dest} {default_name}",
            "description": default_desc,
            "activity_type": "sightseeing",
            "estimated_cost": 200,
            "travel_time_minutes": 25,
            "rating": 4.4,
            "reviewCount": 85,
            "location": dest,
            "distance": "City Center",
            "openingHours": "09:00 AM - 06:00 PM",
            "entryFee": "₹100",
            "aiReason": f"Popular cultural attraction in {dest}.",
            "aiTips": ["Wear comfortable walking shoes"],
            "crowdLevel": "Low",
            "weatherSuitability": "Good",
            "isOptional": is_opt
        }

    generic_activities = [
        ("Heritage & Historic Landmark", f"Explore key historical and cultural monuments in {dest}."),
        ("Old Town & Artisan Markets", f"Stroll through historic bazaars, sample local delicacies, and shop crafts in {dest}."),
        ("Scenic Gardens & Nature Walk", f"Relax in prominent gardens and scenic nature spots in {dest}."),
        ("Museum & Cultural Exhibit", f"Discover art, heritage, and traditional history at top museums in {dest}."),
        ("Sunset Promenade & Local Cuisine", f"Enjoy the sunset view and dine at renowned local eateries in {dest}.")
    ]

    styles = [
        ("Balanced", f"A balanced blend of iconic landmarks, local food, and leisure in {dest}.", 4500, 2),
        ("Explorer", f"An active, immersive plan maximizing sightseeing and hidden gems in {dest}.", 6000, 3),
        ("Relaxed", f"A leisurely, unhurried pace focusing on premier highlights and downtime in {dest}.", 3500, 1)
    ]

    itinerary_options = []
    for style_name, style_desc, cost_per_day, acts_per_day in styles:
        schedule = []
        p_index = 0
        total_p = len(places_info)
        for d in range(num_days):
            day_acts = []
            time_slots = [
                (9, 12),
                (13, 16),
                (17, 19)
            ]
            for act_i in range(acts_per_day):
                s_h, e_h = time_slots[min(act_i, len(time_slots) - 1)]
                p_item = places_info[p_index % total_p] if total_p > 0 else None
                p_index += 1
                gen_title, gen_desc = generic_activities[(d * acts_per_day + act_i) % len(generic_activities)]
                day_acts.append(create_activity(p_item, s_h, e_h, gen_title, gen_desc, is_opt=(act_i > 1)))

            schedule.append({
                "day": d + 1,
                "aiSummary": f"Day {d + 1}: Discover {dest} highlights at a {style_name.lower()} pace.",
                "activities": day_acts
            })

        itinerary_options.append({
            "route_name": style_name,
            "description": style_desc,
            "total_estimated_cost": cost_per_day * num_days,
            "transportation": transportation,
            "schedule": schedule
        })

    return itinerary_options


def generate_itinerary_via_llm(places_info: List[Dict], days: int, start_time: str, end_time: str, accommodation: str = None, energy_level: str = "Moderate", destination_name: str = "", budget: str = "Medium", travel_type: str = "Family", transportation_mode: str = "flight", local_transportation: str = "taxi", interests: List[str] = [], origin: str = "") -> List[Dict]:
    api_key = settings.gemini_api_key
    if api_key:
        try:
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
            
            response = model.generate_content(prompt)
            text = response.text.strip()
            import re
            match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL)
            if match:
                text = match.group(1).strip()
            result = json.loads(text)
            if isinstance(result, list) and len(result) > 0:
                return result
        except Exception as e:
            print(f"Itinerary AI Error, falling back to structured deterministic itinerary: {e}")

    # Fallback to structured deterministic generator
    return _build_fallback_itineraries(
        places_info=places_info,
        days=days,
        start_time=start_time,
        end_time=end_time,
        accommodation=accommodation,
        energy_level=energy_level,
        destination_name=destination_name,
        budget=budget,
        travel_type=travel_type,
        transportation_mode=transportation_mode,
        local_transportation=local_transportation,
        interests=interests,
        origin=origin
    )

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
