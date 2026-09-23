import os
import json
import re
import logging
import google.generativeai as genai
from typing import Any, Dict, List, Optional
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.sql.poi import POI
from app.models.sql.location import Location
from app.models.sql.category import Category
from app.services.rag_service import (
    is_route_or_distance_query,
    build_grounded_system_prompt,
    format_context_block,
)

logger = logging.getLogger(__name__)


def _safe_generate_content(model, contents, timeout_sec: float = 12.0) -> Optional[str]:
    """
    Executes Gemini generate_content with a bounded timeout and safe exception handling.
    Prevents external API latency from blocking worker threads or leaking API keys.
    """
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(model.generate_content, contents)
        try:
            res = future.result(timeout=timeout_sec)
            if res and hasattr(res, "text") and res.text:
                return res.text.strip()
            return None
        except concurrent.futures.TimeoutError:
            logger.warning("Gemini API call timed out after %.1fs", timeout_sec)
            return None
        except Exception as exc:
            logger.warning("Gemini API call failed safely: %s", type(exc).__name__)
            return None



def get_grounded_chat_response(
    user_message: str,
    history: List[Dict[str, str]],
    retrieved_chunks: List[Dict[str, Any]],
    language: str = "en",
    canonical_extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Produces a grounded chat response with strict authority guardrails and source attribution.
    Uses Gemini in online mode if GEMINI_API_KEY is available; otherwise uses deterministic extractive synthesis.
    """
    # 1. Authority Guardrail: Prohibit road distance and route calculations
    if is_route_or_distance_query(user_message):
        route_msg = (
            "For accurate road distances, directions, and travel times, please use "
            "TourMate AI's Route Optimization feature on the Itinerary page, which "
            "computes verified OpenStreetMap road routes."
        )
        return {
            "response": route_msg,
            "answer": route_msg,
            "sources": [],
            "is_grounded": True,
        }

    # 2. Insufficient Evidence Refusal
    if not retrieved_chunks and not canonical_extra:
        refusal_msg = (
            "I do not have verified knowledge about that in my database. "
            "Please ask about our supported destinations (Agra, New Delhi, Jaipur, Mumbai) "
            "or specific landmarks such as Taj Mahal, Agra Fort, Qutub Minar, etc."
        )
        return {
            "response": refusal_msg,
            "answer": refusal_msg,
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

    if canonical_extra:
        sources.insert(0, {
            "id": "canonical-db",
            "title": f"{canonical_extra.get('name', 'Attraction')} Database Record",
            "source": "PostgreSQL canonical database (opening_hours / price)",
            "poi_name": canonical_extra.get("name"),
            "similarity": 1.0,
        })

    # 3. Online Grounded Mode via Gemini (if GEMINI_API_KEY is configured)
    api_key = settings.gemini_api_key
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model_name = settings.gemini_model
            model = genai.GenerativeModel(model_name)

            system_instruction = build_grounded_system_prompt(language)
            context_block = format_context_block(retrieved_chunks, canonical_extra=canonical_extra)

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

            answer_text = _safe_generate_content(model, contents, timeout_sec=12.0)
            if answer_text:
                logger.info(
                    "AI request: provider=gemini model=%s rag_candidates=%d accepted_context=%d grounded=true",
                    model_name,
                    len(retrieved_chunks),
                    len(sources),
                )
                return {
                    "response": answer_text,
                    "answer": answer_text,
                    "sources": sources,
                    "is_grounded": True,
                }
        except Exception as e:
            logger.warning("Gemini Grounded RAG Error, falling back to local synthesis: %s", type(e).__name__)

    # 4. Deterministic Local Fallback (when GEMINI_API_KEY is absent or API fails)
    # Conservatively extracts facts from canonical database and top retrieved chunks without hallucination
    extractive_lines = []

    if canonical_extra and canonical_extra.get("hours_schedule"):
        extractive_lines.append(
            f"{canonical_extra.get('name', 'Attraction')} Opening Hours (Verified Database Record):\n"
            f"{canonical_extra['hours_schedule']}\n"
        )

    if retrieved_chunks:
        if len(retrieved_chunks) == 1:
            extractive_lines.append(retrieved_chunks[0]["content"])
        else:
            extractive_lines.append("Here are relevant verified places from TourMate database:")
            for c in retrieved_chunks:
                poi_label = c.get("poi_name") or c.get("title")
                extractive_lines.append(f"• **{poi_label}**: {c['content']}")

    fallback_response = "\n".join(extractive_lines)
    logger.info(
        "AI request: provider=deterministic_fallback rag_candidates=%d accepted_context=%d grounded=true",
        len(retrieved_chunks),
        len(sources),
    )
    return {
        "response": fallback_response,
        "answer": fallback_response,
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
        text = _safe_generate_content(model, contents, timeout_sec=10.0)
        if text:
            return text
        return "I'm sorry, I'm having trouble thinking right now. Please try again later."
    except Exception as e:
        logger.warning("AI Error: %s", type(e).__name__)
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
            
            text = _safe_generate_content(model, prompt, timeout_sec=15.0)
            if text:
                import re
                match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL)
                if match:
                    text = match.group(1).strip()
                result = json.loads(text)
                if isinstance(result, list) and len(result) > 0:
                    return result
        except Exception as e:
            logger.warning("Itinerary AI Error, falling back to structured deterministic itinerary: %s", type(e).__name__)

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

async def _find_canonical_poi_match(
    name: str,
    location_str: str = "",
    db: Optional[AsyncSession] = None,
) -> Optional[Dict[str, Any]]:
    """Grounds a candidate landmark against canonical TourMate POIs in PostgreSQL."""
    if not name:
        return None

    clean_query = name.lower().strip()
    clean_norm = clean_query.replace("monument", "").replace("heritage", "").strip()

    async def _search_in_session(session: AsyncSession):
        stmt = (
            select(POI)
            .join(Location, POI.location_id == Location.id)
            .options(
                selectinload(POI.location),
                selectinload(POI.category),
                selectinload(POI.poi_images),
            )
            .where(POI.is_active == True)
        )
        res = await session.execute(stmt)
        all_pois = res.scalars().all()

        # 1. Exact match
        for p in all_pois:
            p_name = p.name.lower().strip()
            if clean_query == p_name or (clean_norm and clean_norm == p_name):
                return p

        # 2. Substring match
        for p in all_pois:
            p_name = p.name.lower().strip()
            if p_name in clean_query or (len(clean_query) >= 4 and clean_query in p_name):
                return p

        # 3. Location-aware candidate match
        if location_str:
            loc_clean = location_str.lower()
            for p in all_pois:
                if p.location and (p.location.city.lower() in loc_clean or loc_clean in p.location.city.lower()):
                    query_words = set(clean_query.split())
                    poi_words = set(p.name.lower().split())
                    if len(query_words.intersection(poi_words)) >= 1:
                        return p

        return None

    matched = None
    try:
        if db is not None:
            matched = await _search_in_session(db)
        else:
            from app.core.db import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                matched = await _search_in_session(session)
    except Exception as e:
        logger.warning("Error finding canonical POI match: %s", e)
        return None

    if matched:
        return {
            "id": str(matched.id),
            "name": matched.name,
            "location": f"{matched.location.city}, {matched.location.state}" if matched.location else "",
            "category": matched.category.name if matched.category else "Attraction",
            "rating": float(matched.rating) if matched.rating else 4.8,
            "description": matched.description,
            "latitude": matched.location.latitude if matched.location else None,
            "longitude": matched.location.longitude if matched.location else None,
        }
    return None


async def predict_landmark_from_image(image_bytes: bytes, db: Optional[AsyncSession] = None) -> dict:
    """
    Identifies tourist landmarks with strict canonical POI grounding.
    Never hallucinates generic 'palace' responses for non-landmarks.
    """
    import io
    from PIL import Image

    # 1. Validate image
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        pil_img.load()
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
        # Resize large images to max 1024px to ensure fast processing
        if max(pil_img.size) > 1024:
            pil_img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    except Exception as e:
        logger.warning("Image decoding failed: %s", e)
        return {
            "name": "Invalid Image",
            "location": "",
            "category": "Non-Landmark",
            "confidence": "None",
            "is_landmark": False,
            "is_grounded": False,
            "description": "The uploaded file could not be decoded as a valid image. Please upload a clear photo in JPEG, PNG, or WebP format."
        }

    # 2. Prefer Gemini Vision if API key is provided
    api_key = settings.gemini_api_key
    gemini_data = None
    if api_key:
        models_to_try = [
            getattr(settings, "gemini_model", "gemini-2.0-flash"),
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ]
        seen = set()
        models = [m for m in models_to_try if not (m in seen or seen.add(m))]

        prompt = (
            "You are an expert landmark and heritage recognition specialist for TourMate AI.\n"
            "Analyze this image carefully.\n"
            "Rules:\n"
            "1. If this image depicts a known tourist landmark, historical monument, heritage building, or cultural attraction:\n"
            "   - Provide the EXACT landmark name (e.g. 'Vidhana Soudha', 'Taj Mahal', 'Bangalore Palace', 'Hawa Mahal'). Do NOT return a generic label like 'palace' or 'building'.\n"
            "   - Identify its city and state/country (e.g. 'Bengaluru, Karnataka' or 'Agra, Uttar Pradesh').\n"
            "   - Identify its specific category (e.g. 'Landmark / Government Building', 'Palace', 'Fort', 'Temple', 'Mausoleum').\n"
            "   - Assess confidence: 'High' if visually distinctive and certain, or 'Moderate' if visual angle/details are partially ambiguous.\n"
            "   - Provide a factual 2-3 sentence description.\n"
            "   - Set is_landmark to true.\n"
            "2. If this image does NOT depict a recognized tourist landmark or attraction (e.g. common everyday objects, shoes, food, pets, laptops, vehicles, random interiors):\n"
            "   - Set is_landmark to false.\n"
            "   - Set name to 'Unrecognized Landmark'.\n"
            "   - Set confidence to 'None'.\n"
            "   - Set description to 'Unable to identify a recognized landmark or tourist attraction in this image.'\n"
            "Respond strictly with a JSON object in this format:\n"
            '{"is_landmark": true, "name": "Exact Landmark Name", "location": "City, State", "category": "Category", "confidence": "High", "description": "2-3 factual sentences."}'
        )

        for m_name in models:
            try:
                genai.configure(api_key=api_key)
                gemini = genai.GenerativeModel(m_name)
                res = gemini.generate_content(
                    [prompt, pil_img],
                    generation_config={"response_mime_type": "application/json"},
                )
                if res and res.text:
                    clean_text = res.text.strip()
                    if clean_text.startswith("```json"):
                        clean_text = clean_text[7:]
                    if clean_text.startswith("```"):
                        clean_text = clean_text[3:]
                    if clean_text.endswith("```"):
                        clean_text = clean_text[:-3]
                    data = json.loads(clean_text.strip())
                    if isinstance(data, dict) and data.get("name"):
                        gemini_data = data
                        break
            except Exception as e:
                logger.warning("Gemini model %s landmark recognition attempt failed: %s", m_name, e)

    if gemini_data:
        candidate_name = gemini_data.get("name", "").strip()
        is_landmark = gemini_data.get("is_landmark", True)
        confidence = str(gemini_data.get("confidence", "High")).capitalize()
        location = gemini_data.get("location", "")
        category = gemini_data.get("category", "Landmark")
        description = gemini_data.get("description", "")

        if not is_landmark or confidence.lower() == "none" or "unrecognized" in candidate_name.lower():
            return {
                "name": "Unrecognized Landmark",
                "location": "",
                "category": "Non-Landmark",
                "confidence": "None",
                "is_landmark": False,
                "is_grounded": False,
                "description": "Unable to identify a recognized landmark or tourist attraction in this image. Please upload a clear photo of an attraction, monument, or historical site."
            }

        # Ground against Canonical POI database
        grounded_poi = await _find_canonical_poi_match(candidate_name, location, db=db)
        if grounded_poi:
            return {
                "name": grounded_poi["name"],
                "location": grounded_poi["location"],
                "category": grounded_poi["category"],
                "confidence": "High",
                "is_landmark": True,
                "is_grounded": True,
                "poi_id": grounded_poi["id"],
                "rating": grounded_poi["rating"],
                "description": grounded_poi["description"] or description,
                "latitude": grounded_poi["latitude"],
                "longitude": grounded_poi["longitude"]
            }

        # Recognized real-world landmark that is not yet in TourMate's verified POI database (e.g. Vidhana Soudha)
        grounding_notice = f"Identified as {candidate_name}"
        if location:
            grounding_notice += f" in {location}"
        grounding_notice += ". TourMate does not currently have this landmark in its verified POI database."

        full_description = f"{grounding_notice} {description}".strip()

        return {
            "name": candidate_name,
            "location": location,
            "category": category,
            "confidence": confidence if confidence in ("High", "Moderate", "Low") else "Moderate",
            "is_landmark": True,
            "is_grounded": False,
            "poi_id": None,
            "description": full_description
        }

    # If Gemini Vision was unavailable / unconfigured
    return {
        "name": "Unrecognized Landmark",
        "location": "",
        "category": "Non-Landmark",
        "confidence": "None",
        "is_landmark": False,
        "is_grounded": False,
        "description": "Unable to identify a recognized landmark in this image. Please ensure the photo clearly depicts a known monument or attraction."
    }


def enrich_itinerary_with_llm(
    options: List[Dict],
    destination_name: str,
    travel_type: str = "Family",
    energy_level: str = "Moderate",
    interests: List[str] = None
) -> List[Dict]:
    """
    Calls LLM strictly to personalize aiSummary, aiReason, and aiTips for the
    pre-computed authoritative schedules. Never alters stops, order, hours, or prices.
    """
    api_key = settings.gemini_api_key
    if not api_key:
        # Deterministic fallback summaries & tips
        for opt in options:
            for day_data in opt.get("schedule", []):
                day_num = day_data.get("day", 1)
                act_names = [a.get("name") for a in day_data.get("activities", []) if a.get("activity_type") != "transit"]
                day_data["aiSummary"] = f"Day {day_num} in {destination_name}: Explore {', '.join(act_names[:3])} with curated visits and local culture."
                for act in day_data.get("activities", []):
                    act_name = act.get("name", "Attraction")
                    act_cat = act.get("activity_type", "Sightseeing")
                    act["aiReason"] = f"Verified canonical {act_cat.lower()} highlighting the heritage of {destination_name}."
                    act["aiTips"] = [
                        "Book tickets in advance during peak visiting hours",
                        "Wear comfortable footwear and carry water"
                    ]
        return options

    try:
        genai.configure(api_key=api_key)
        gemini_model_name = os.environ.get("GEMINI_MODEL", getattr(settings, "gemini_model", "gemini-1.5-flash"))
        models_to_try = [gemini_model_name, "gemini-1.5-flash", "gemini-2.0-flash"]
        seen = set()
        models = [m for m in models_to_try if not (m in seen or seen.add(m))]

        schedule_structure = []
        for opt in options:
            schedule_structure.append({
                "route_name": opt.get("route_name"),
                "days": [
                    {
                        "day": d.get("day"),
                        "stops": [a.get("name") for a in d.get("activities", [])]
                    }
                    for d in opt.get("schedule", [])
                ]
            })

        prompt = f"""
You are TourMate AI, an expert local travel guide.
Personalize the explanations for this verified trip to {destination_name}.
Travel Style: {travel_type}, Energy Level: {energy_level}, Interests: {', '.join(interests or ['Sightseeing'])}.

Authoritative itinerary schedule:
{json.dumps(schedule_structure, indent=2)}

CRITICAL: Do NOT change or add any stops. Only provide:
1. "aiSummary" for each day (1-2 engaging sentences).
2. For each stop: "aiReason" (1 sentence explaining fit for traveler) and "aiTips" (2 practical tips).

Respond strictly with a JSON object matching this schema:
{{
  "explanations": [
    {{
      "route_name": "Balanced",
      "days": [
        {{
          "day": 1,
          "aiSummary": "Summary text",
          "stops": [
            {{
              "name": "Stop Name",
              "aiReason": "Reason text",
              "aiTips": ["Tip 1", "Tip 2"]
            }}
          ]
        }}
      ]
    }}
  ]
}}
"""
        for m_name in models:
            try:
                model = genai.GenerativeModel(m_name, generation_config={"response_mime_type": "application/json"})
                text = _safe_generate_content(model, prompt, timeout_sec=10.0)
                if not text:
                    continue
                match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL)
                if match:
                    text = match.group(1).strip()
                data = json.loads(text)
                explanations = data.get("explanations", [])
                
                for opt in options:
                    opt_exp = next((e for e in explanations if e.get("route_name") == opt.get("route_name")), None)
                    if not opt_exp:
                        continue
                    for day_data in opt.get("schedule", []):
                        exp_day = next((d for d in opt_exp.get("days", []) if d.get("day") == day_data.get("day")), None)
                        if exp_day:
                            if exp_day.get("aiSummary"):
                                day_data["aiSummary"] = exp_day["aiSummary"]
                            for act in day_data.get("activities", []):
                                stop_exp = next((s for s in exp_day.get("stops", []) if s.get("name") == act.get("name")), None)
                                if stop_exp:
                                    if stop_exp.get("aiReason"):
                                        act["aiReason"] = stop_exp["aiReason"]
                                    if stop_exp.get("aiTips"):
                                        act["aiTips"] = stop_exp["aiTips"]
                return options
            except Exception as e:
                logger.warning("Gemini model %s explanation attempt failed: %s", m_name, e)

    except Exception as e:
        logger.warning("Enrich itinerary with LLM error: %s", e)

    # Fallback to deterministic summaries
    for opt in options:
        for day_data in opt.get("schedule", []):
            day_num = day_data.get("day", 1)
            act_names = [a.get("name") for a in day_data.get("activities", []) if a.get("activity_type") != "transit"]
            day_data["aiSummary"] = f"Day {day_num} in {destination_name}: Explore {', '.join(act_names[:3])} with curated visits and local culture."
            for act in day_data.get("activities", []):
                act_name = act.get("name", "Attraction")
                act_cat = act.get("activity_type", "Sightseeing")
                act["aiReason"] = f"Verified canonical {act_cat.lower()} highlighting the heritage of {destination_name}."
                act["aiTips"] = [
                    "Book tickets in advance during peak visiting hours",
                    "Wear comfortable footwear and carry water"
                ]
    return options

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
        text = _safe_generate_content(model, prompt, timeout_sec=10.0)
        if text:
            import re
            match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL)
            if match:
                text = match.group(1).strip()
            result = json.loads(text)
            return result
        return {
            "cluster_name": "Local District",
            "description": "A geographic cluster of attractions.",
            "categories": [],
            "reasons": ["Geographically close to each other"]
        }
    except Exception as e:
        logger.warning("Cluster Enrichment AI Error: %s", type(e).__name__)
        return {
            "cluster_name": "Local District",
            "description": "A geographic cluster of attractions.",
            "categories": [],
            "reasons": ["Geographically close to each other"]
        }
