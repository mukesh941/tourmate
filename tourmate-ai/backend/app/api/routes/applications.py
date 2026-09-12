from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from bson import ObjectId

from app.core.database import get_db
from app.api.deps import get_current_user_dependency

router = APIRouter(prefix="/applications", tags=["applications"])

# -------------------------------------------------------------
# Static Curated Data for the 4 Section 1.4 Applications
# (All using real photography, no AI placeholders)
# -------------------------------------------------------------
APPLICATIONS_DATA = {
    "campus_tours": {
        "title": "University Campus Tours",
        "description": "Virtual guides can help prospective students explore campus buildings, facilities, and student life from anywhere.",
        "icon": "GraduationCap",
        "cover_image": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&w=1200&q=80",
        "campuses": [
            {
                "id": "oxford-university",
                "name": "University of Oxford",
                "location": "Oxford, United Kingdom",
                "established": "1096",
                "ranking": "#1 World University",
                "image": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&w=1000&q=80",
                "guide_voice_intro": "Welcome prospective students! I am your AI Campus Guide. Oxford has shaped global thought for over nine centuries. Let's walk through our historic colleges, state-of-the-art research laboratories, and vibrant student societies.",
                "stops": [
                    {
                        "name": "Bodleian Library & Radcliffe Camera",
                        "category": "Academic & Research",
                        "image": "https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?auto=format&fit=crop&w=1000&q=80",
                        "description": "One of the oldest libraries in Europe, holding over 13 million printed items with iconic circular neoclassical architecture.",
                        "guide_commentary": "The Radcliffe Camera was completed in 1749. As an Oxford student, this is where you will delve into research manuscripts dating back hundreds of years."
                    },
                    {
                        "name": "Christ Church College & Great Hall",
                        "category": "College & Residence",
                        "image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1000&q=80",
                        "description": "The landmark college featuring the world-famous Great Hall, quad gardens, and centuries of tradition.",
                        "guide_commentary": "Students dine right here beneath oil portraits of British prime ministers, Nobel laureates, and world-renowned philosophers."
                    },
                    {
                        "name": "Biochemical Research Hub & Lab Complex",
                        "category": "Science & Innovation",
                        "image": "https://images.unsplash.com/photo-1532094349884-543bc11b234d?auto=format&fit=crop&w=1000&q=80",
                        "description": "Cutting-edge biotechnology, robotics, and medical science research facility funded by international grants.",
                        "guide_commentary": "Undergraduate students begin hands-on laboratory research here in their second semester under leading faculty mentors."
                    },
                    {
                        "name": "Iffley Road Sports Complex & Boat Club",
                        "category": "Athletics & Student Life",
                        "image": "https://images.unsplash.com/photo-1526676037777-05a232554f77?auto=format&fit=crop&w=1000&q=80",
                        "description": "Historic venue where Roger Bannister broke the 4-minute mile, with Olympic rowing boathouses and fitness centers.",
                        "guide_commentary": "Rowing and athletics form a core pillar of Oxford life. Every college has its own boat club competing in the annual bumps races."
                    }
                ]
            },
            {
                "id": "stanford-university",
                "name": "Stanford University",
                "location": "Stanford, California, USA",
                "established": "1885",
                "ranking": "#2 Worldwide (Engineering & CS)",
                "image": "https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?auto=format&fit=crop&w=1000&q=80",
                "guide_voice_intro": "Hello! Welcome to Stanford, the heartbeat of Silicon Valley innovation. Together, we'll explore the historic Main Quad, our cutting-edge computer science labs, and vibrant campus life under the California sun.",
                "stops": [
                    {
                        "name": "The Main Quad & Memorial Church",
                        "category": "Historic Core",
                        "image": "https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?auto=format&fit=crop&w=1000&q=80",
                        "description": "Heart of Stanford with Richardsonian Romanesque sandstone arcades and red tile roofs.",
                        "guide_commentary": "This architectural style was designed specifically for California's climate, connecting faculty offices with lush courtyard palm trees."
                    },
                    {
                        "name": "Gates Computer Science Building",
                        "category": "Technology & AI",
                        "image": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=1000&q=80",
                        "description": "Where Google and thousands of Silicon Valley tech breakthroughs were prototyped.",
                        "guide_commentary": "Here, students build machine learning systems, robotics prototypes, and launch revolutionary startups."
                    }
                ]
            }
        ]
    },
    "hotel_bookings": {
        "title": "Hotel Room Bookings",
        "description": "Virtual guides can help users explore and book hotel rooms by showing different room types and amenities.",
        "icon": "Hotel",
        "cover_image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
        "hotels": [
            {
                "id": "grand-palace-resort",
                "name": "The Grand Azure Palace & Spa",
                "location": "Udaipur / Lake Pichola",
                "rating": 4.9,
                "review_count": 842,
                "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1000&q=80",
                "guide_voice_intro": "Namaste and welcome to The Grand Azure Palace. I am your personal hospitality guide. Allow me to walk you through our heritage suites, infinity pools, and royal lakefront dining options.",
                "rooms": [
                    {
                        "id": "deluxe-lake-view",
                        "name": "Deluxe Lake View Suite",
                        "price_per_night": 185,
                        "currency": "$",
                        "size": "550 sq ft",
                        "bed": "1 King Bed",
                        "max_guests": 2,
                        "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80",
                        "amenities": ["Lake View Balcony", "Marble Bathtub", "Complimentary Breakfast", "High-Speed Wi-Fi", "24/7 Butler Service"],
                        "guide_recommendation": "This suite offers panoramic sunset views over the water, hand-carved jharokha balconies, and plush Egyptian cotton linens."
                    },
                    {
                        "id": "executive-royal-suite",
                        "name": "Executive Royal Heritage Suite",
                        "price_per_night": 320,
                        "currency": "$",
                        "size": "920 sq ft",
                        "bed": "1 Super King Bed + Living Lounge",
                        "max_guests": 3,
                        "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80",
                        "amenities": ["Private Jacuzzi", "Separate Living Room", "Executive Club Lounge", "Chauffeured Airport Transfer", "Spa Credits"],
                        "guide_recommendation": "Designed for luxury travelers. Enjoy an in-suite private jacuzzi overlooking royal courtyards and personalized afternoon tea."
                    },
                    {
                        "id": "presidential-penthouse",
                        "name": "Presidential Garden Penthouse",
                        "price_per_night": 540,
                        "currency": "$",
                        "size": "1,450 sq ft",
                        "bed": "2 Master Bedrooms",
                        "max_guests": 5,
                        "image": "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=1000&q=80",
                        "amenities": ["Private Plunge Pool", "Rooftop Terrace", "Full Chef's Kitchen", "Wine Cellar Access", "Dedicated Concierge"],
                        "guide_recommendation": "Our most exclusive residence. Features a private heated plunge pool on the rooftop terrace and dedicated 24-hour sommelier service."
                    }
                ]
            }
        ]
    },
    "historical_sites": {
        "title": "Historical Site Explorations",
        "description": "Virtual guides can explain landmarks, share context, and bring history to life during immersive visits.",
        "icon": "Landmark",
        "cover_image": "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=1200&q=80",
        "sites": [
            {
                "id": "taj-mahal-agra",
                "name": "The Taj Mahal",
                "location": "Agra, Uttar Pradesh, India",
                "period": "1632–1653 CE",
                "architectural_style": "Mughal Architecture",
                "image": "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=1000&q=80",
                "guide_voice_intro": "Greetings, traveler! I am your AI Historian. The Taj Mahal is not merely a marble tomb—it is poetry frozen in white Makrana stone, commissioned by Emperor Shah Jahan in eternal memory of Mumtaz Mahal. Let us explore its sacred geometry.",
                "checkpoints": [
                    {
                        "title": "The Main Gate (Darwaza-i Rauza)",
                        "image": "https://images.unsplash.com/photo-1585135497273-1a86b09fe70e?auto=format&fit=crop&w=1000&q=80",
                        "historical_context": "Crafted from red sandstone with calligraphy framing the archway, reading: 'O Soul, thou art at rest. Return to the Lord at peace with Him.'",
                        "guide_narration": "Notice the optical illusion as you approach: as you step backwards away from the gate, the Taj Mahal appears to grow larger and grander in front of you."
                    },
                    {
                        "title": "The Central Dome & Inlaid Pietra Dura",
                        "image": "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1000&q=80",
                        "historical_context": "The outer onion dome rises 73 meters. Italian and Persian artisans embedded 28 types of semi-precious stones including lapis lazuli, turquoise, and jade directly into marble.",
                        "guide_narration": "Each flower motif on the cenotaph contains up to 60 individually carved gemstone petals, fitted together with joints so tight you cannot slide a razor blade between them."
                    },
                    {
                        "title": "The Four Minarets & Seismic Engineering",
                        "image": "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1000&q=80",
                        "historical_context": "Rising over 40 meters at the four corners of the plinth, designed with innovative earthquake defense.",
                        "guide_narration": "Mughal engineers deliberately tilted each minaret slightly outward by several degrees. If a catastrophic earthquake occurs, the towers will collapse away from the central tomb rather than crushing it."
                    }
                ]
            },
            {
                "id": "colosseum-rome",
                "name": "The Colosseum (Flavian Amphitheater)",
                "location": "Rome, Italy",
                "period": "70–80 CE",
                "architectural_style": "Imperial Roman",
                "image": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=1000&q=80",
                "guide_voice_intro": "Salve! Step back 2,000 years to ancient Rome. As your guide, I will take you beneath the arena floor into the hypogeum where gladiators, lions, and machinery prepared for the spectacles.",
                "checkpoints": [
                    {
                        "title": "The Hypogeum Underground Labyrinths",
                        "image": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=1000&q=80",
                        "historical_context": "A two-level subterranean network of tunnels and 80 vertical trapdoor lifts powered by teams of enslaved laborers.",
                        "guide_narration": "Tigers, bears, and scenery would suddenly materialize through the wooden arena sand as hydraulic and pulley lifts engaged from below."
                    }
                ]
            }
        ]
    },
    "restaurant_reservations": {
        "title": "Restaurant Reservations",
        "description": "Virtual guides can showcase restaurant menus, ambiance, and help users make dining reservations.",
        "icon": "Utensils",
        "cover_image": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80",
        "restaurants": [
            {
                "id": "spice-route-bistro",
                "name": "The Saffron & Spice Botanical Lounge",
                "cuisine": "Contemporary Pan-Asian & Indian Fusion",
                "rating": 4.8,
                "price_level": "$$$",
                "location": "Skyline Promenade, Sector 29",
                "image": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1000&q=80",
                "guide_voice_intro": "Welcome! I am your AI Culinary Sommelier. Tonight, let me introduce you to our tranquil botanical courtyard, wood-fired hearth, and chef's tasting menu paired with artisanal mocktails.",
                "ambiance_description": "Warm ambient lighting, living plant walls, open show kitchen, and soft acoustic jazz.",
                "menu_highlights": [
                    {
                        "name": "Truffle Butter Naan & Smoked Dal Makhani",
                        "price": "$16.50",
                        "tags": ["Vegetarian", "Chef's Signature"],
                        "description": "Simmered over slow charcoal for 24 hours, finished with imported black truffle oil."
                    },
                    {
                        "name": "Kashmiri Lamb Rogan Josh Shank",
                        "price": "$28.00",
                        "tags": ["Gluten-Free", "House Special"],
                        "description": "Slow-braised New Zealand lamb shank in aromatic dried Kashmiri chilies and ratanjot."
                    },
                    {
                        "name": "Wild Morel & Cardamom Risotto",
                        "price": "$22.00",
                        "tags": ["Vegetarian", "Fusion"],
                        "description": "Himalayan gucchi morels folded into arborio rice with aged parmesan and green cardamom."
                    },
                    {
                        "name": "Gold Leaf Saffron Phirni",
                        "price": "$12.00",
                        "tags": ["Dessert", "Royal Recipe"],
                        "description": "Creamy ground rice pudding infused with pure Kashmiri saffron, crushed pistachios, and 24k edible silver leaf."
                    }
                ],
                "time_slots": ["18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30"],
                "seating_options": ["Indoor Botanical Dining Room", "Open-Air Garden Terrace", "Chef's Counter (Show Kitchen)"]
            }
        ]
    }
}


class BookingRequest(BaseModel):
    application_type: str = Field(..., description="campus_tours | hotel_bookings | historical_sites | restaurant_reservations")
    item_id: str
    item_name: str
    booking_date: str
    booking_time: Optional[str] = None
    guests_count: int = 1
    notes: Optional[str] = None
    sub_selection: Optional[str] = None  # e.g., room type or seating preference


@router.get("")
async def get_applications_overview():
    """
    Returns curated virtual guide data for all 4 Section 1.4 Applications:
    - University Campus Tours
    - Hotel Room Bookings
    - Historical Site Explorations
    - Restaurant Reservations
    """
    return {
        "success": True,
        "data": APPLICATIONS_DATA,
        "error": None
    }


@router.get("/{app_type}")
async def get_application_by_type(app_type: str):
    if app_type not in APPLICATIONS_DATA:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application '{app_type}' not found. Valid types: {list(APPLICATIONS_DATA.keys())}"
        )
    return {
        "success": True,
        "data": APPLICATIONS_DATA[app_type],
        "error": None
    }


@router.post("/book")
async def create_booking(
    booking: BookingRequest,
    user: dict = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    Saves a user booking (hotel room, dining reservation, campus tour) to MongoDB.
    """
    booking_doc = {
        "user_id": str(user["_id"]),
        "user_email": user.get("email"),
        "user_name": user.get("name", "Traveler"),
        "application_type": booking.application_type,
        "item_id": booking.item_id,
        "item_name": booking.item_name,
        "booking_date": booking.booking_date,
        "booking_time": booking.booking_time,
        "guests_count": booking.guests_count,
        "notes": booking.notes,
        "sub_selection": booking.sub_selection,
        "status": "confirmed",
        "created_at": datetime.utcnow()
    }
    
    result = await db["application_bookings"].insert_one(booking_doc)
    booking_doc["_id"] = str(result.inserted_id)

    return {
        "success": True,
        "data": {
            "booking_id": str(result.inserted_id),
            "message": f"Successfully confirmed reservation for {booking.item_name}!",
            "details": booking_doc
        },
        "error": None
    }


@router.get("/user/my-bookings")
async def get_my_bookings(
    user: dict = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    Fetches all application bookings confirmed by the current authenticated user.
    """
    cursor = db["application_bookings"].find({"user_id": str(user["_id"])}).sort("created_at", -1)
    bookings = await cursor.to_list(length=100)
    
    for b in bookings:
        b["_id"] = str(b["_id"])
        if isinstance(b.get("created_at"), datetime):
            b["created_at"] = b["created_at"].isoformat()

    return {
        "success": True,
        "data": bookings,
        "error": None
    }
