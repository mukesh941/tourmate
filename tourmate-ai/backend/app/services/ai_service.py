import os
import google.generativeai as genai
from typing import List, Dict
from app.core.config import settings

def get_ai_response(user_message: str, history: List[Dict[str, str]], context: str = None, language: str = 'en') -> str:
    api_key = settings.gemini_api_key
    if not api_key:
        return "Please add your GEMINI_API_KEY to the backend .env file to activate the AI Tour Guide."

    genai.configure(api_key=api_key)
    
    # Initialize the model
    model = genai.GenerativeModel('gemini-3.6-flash')
    
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
        
    # Construct conversation history for Gemini
    # Gemini expects: [{"role": "user", "parts": [...]}, {"role": "model", "parts": [...]}]
    contents = []
    
    # We add the system prompt as the first user message, and a dummy model acknowledgment
    contents.append({"role": "user", "parts": [system_prompt]})
    contents.append({"role": "model", "parts": ["Understood! I am TourMate AI. How can I help you?"]})
    
    for msg in history:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append({
            "role": role,
            "parts": [msg.get("content", "")]
        })
        
    # Append the new user message
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

def generate_itinerary_via_llm(places_info: List[Dict], days: int, start_time: str, end_time: str, accommodation: str = None, energy_level: str = "Moderate", destination_name: str = "") -> List[Dict]:
    api_key = settings.gemini_api_key
    if not api_key:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set in the backend .env file. Please restart the backend server if you recently added it.")

    genai.configure(api_key=api_key)
    
    # Use JSON mode if available, or just prompt for strict JSON
    model = genai.GenerativeModel('gemini-3.6-flash', generation_config={"response_mime_type": "application/json"})
    
    places_context = ""
    if places_info:
        places_context = f"You must include all of the following places in the itinerary, distributing them logically:\n{json.dumps(places_info, indent=2)}"
    else:
        places_context = f"No specific places were provided. Please use your world knowledge to suggest the best, most popular landmarks, restaurants, and activities for a trip to {destination_name}."

    prompt = f"""
    You are an expert travel planner. Create realistic, detailed day-by-day itineraries for {days} days.
    The daily schedule should run roughly from {start_time} to {end_time}.
    The destination for this trip is: {destination_name if destination_name else 'Not specified'}
    
    CRITICAL CONSTRAINTS:
    - Accommodation/Starting Point: {accommodation if accommodation else 'Not specified. Assume a central downtown location.'}
    - Energy Level (Fatigue Limit): {energy_level}. If 'Relaxed', schedule fewer places per day and add more rest time. If 'Intense', pack the schedule.
    
    {places_context}
    
    Generate 3 DIFFERENT alternative route options (e.g., Option 1 is Optimal, Option 2 is a different sequence, Option 3 is a reversed sequence).
    
    Your response MUST be a valid JSON array of objects representing the alternatives. Use this exact schema:
    [
      {{
        "route_name": "Option 1: Optimal Flow",
        "schedule": [
          {{
            "day": 1,
            "activities": [
              {{
                "time": "09:00",
                "place_id": "optional_id",
                "name": "Activity or Place Name",
                "description": "Brief description"
              }}
            ]
          }}
        ]
      }}
    ]
    """
    
    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"Itinerary AI Error: {e}")
        from fastapi import HTTPException
        if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
            raise HTTPException(status_code=429, detail="AI Rate limit exceeded. Please wait 30 seconds and try again.")
        raise HTTPException(status_code=500, detail=f"Failed to generate itinerary: {str(e)}")

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
