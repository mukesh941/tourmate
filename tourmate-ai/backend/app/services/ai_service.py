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

def generate_itinerary_via_llm(places_info: List[Dict], days: int, start_time: str, end_time: str) -> List[Dict]:
    api_key = settings.gemini_api_key
    if not api_key:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set in the backend .env file. Please restart the backend server if you recently added it.")

    genai.configure(api_key=api_key)
    
    # Use JSON mode if available, or just prompt for strict JSON
    model = genai.GenerativeModel('gemini-3.6-flash', generation_config={"response_mime_type": "application/json"})
    
    prompt = f"""
    You are an expert travel planner. Create a realistic, detailed day-by-day itinerary for {days} days.
    The daily schedule should run roughly from {start_time} to {end_time}.
    
    You must include all of the following places in the itinerary, distributing them logically by proximity or theme:
    {json.dumps(places_info, indent=2)}
    
    Also, please add generic activities like "Breakfast", "Lunch", "Dinner", or "Travel time" where appropriate.
    
    Your response MUST be a valid JSON array of objects representing each day. Use this exact schema:
    [
      {{
        "day": 1,
        "activities": [
          {{
            "time": "09:00",
            "place_id": "optional_id_if_it_is_one_of_the_provided_places",
            "name": "Activity or Place Name",
            "description": "Brief description of what to do"
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
        from tensorflow.keras.applications import MobileNetV2
        _mobilenet_model = MobileNetV2(weights="imagenet")
    return _mobilenet_model

def predict_landmark_from_image(image_bytes: bytes) -> dict:
    from PIL import Image
    import numpy as np
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions

    # Load image and resize to 224x224 (required by MobileNetV2)
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize((224, 224))
    
    # Preprocess the image
    img_array = np.array(image)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)
    
    # Predict
    model = get_mobilenet_model()
    predictions = model.predict(img_array)
    decoded = decode_predictions(predictions, top=1)[0][0] # (class_id, label, probability)
    
    predicted_label = decoded[1].replace("_", " ").title()
    
    # Use Gemini to generate a travel-friendly description
    api_key = settings.gemini_api_key
    description = f"This looks like a {predicted_label}."
    if api_key:
        genai.configure(api_key=api_key)
        gemini = genai.GenerativeModel('gemini-3.6-flash')
        prompt = f"Write a very short (2-3 sentences), interesting travel description about the architectural category/landmark type '{predicted_label}'."
        try:
            res = gemini.generate_content(prompt)
            description = res.text
        except Exception as e:
            print(f"Failed to generate description: {e}")
            
    return {
        "name": predicted_label,
        "description": description
    }
