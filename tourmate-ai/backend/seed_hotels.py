import asyncio
from app.core.database import get_db

HOTELS_SEED_DATA = [
    {
        "name": "The Leela Palace New Delhi",
        "description": "An opulent palace hotel located in New Delhi's prestigious Diplomatic Enclave. Features royal Lutyens architecture, rooftop temperature-controlled infinity pool, Michelin-standard Franco-Italian and Japanese restaurants, and luxury ESPA spa.",
        "city": "Delhi",
        "address": "Diplomatic Enclave, Chanakyapuri, New Delhi 110023",
        "rating": 4.9,
        "review_count": 1420,
        "price_per_night_start": 52.0,
        "currency": "$",
        "hotel_type": "Ultra Luxury Palace",
        "cover_image": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80",
            "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Rooftop Infinity Pool",
            "ESPA Luxury Wellness Spa",
            "24/7 Butler Service",
            "High-Speed Wi-Fi",
            "Michelin Caliber Dining",
            "Airport BMW Transfer",
            "Valet Parking"
        ],
        "rooms": [
            {
                "id": "delhi-grand-deluxe",
                "name": "Grand Heritage Deluxe Room",
                "price_per_night": 52.0,
                "capacity": 2,
                "bed_type": "1 King Bed",
                "size": "550 sq ft",
                "amenities": ["City Skyline View", "Marble Bathroom with Tub", "Complimentary High Tea", "Free Wi-Fi"],
                "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80",
                "description": "Floor-to-ceiling soundproof windows, bespoke Indian tapestries, and marble soaking tubs with embedded LCD mirrors."
            },
            {
                "id": "delhi-royal-suite",
                "name": "Royal Diplomatic Suite",
                "price_per_night": 96.0,
                "capacity": 3,
                "bed_type": "1 Super King Bed + Living Area",
                "size": "1,100 sq ft",
                "amenities": ["Separate Executive Office", "Walk-in Dressing Room", "Private Butler Service", "Club Lounge Access"],
                "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80",
                "description": "Favored by visiting dignitaries, offering hand-woven silk rugs, private dining lounge, and 24-hour butler assistance."
            }
        ]
    },
    {
        "name": "The Taj Mahal Palace & Tower",
        "description": "India's most iconic heritage hotel standing proudly opposite the Gateway of India since 1903. Overlooking the Arabian Sea, featuring legendary Victorian Moorish vaulted ceilings, floating harbor views, and grand chandeliers.",
        "city": "Mumbai",
        "address": "Apollo Bunder, Colaba, Mumbai, Maharashtra 400001",
        "rating": 5.0,
        "review_count": 2180,
        "price_per_night_start": 58.0,
        "currency": "$",
        "hotel_type": "Iconic Heritage Palace",
        "cover_image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?auto=format&fit=crop&w=1000&q=80",
            "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Arabian Sea Harbor View",
            "Palace Swimming Pool",
            "Jiva Luxury Spa",
            "Fine Dining (Wasabi by Morimoto)",
            "High-Speed Wi-Fi",
            "Historic Heritage Walks"
        ],
        "rooms": [
            {
                "id": "mumbai-sea-deluxe",
                "name": "Luxury Grand Sea-View Room",
                "price_per_night": 58.0,
                "capacity": 2,
                "bed_type": "1 King Bed",
                "size": "500 sq ft",
                "amenities": ["Gateway of India View", "Marble Bathtub", "Complimentary Breakfast", "Wi-Fi"],
                "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80",
                "description": "Watch heritage boats glide past the Gateway of India from vintage hand-carved window bays."
            },
            {
                "id": "mumbai-tata-suite",
                "name": "Heritage Presidential Harbor Suite",
                "price_per_night": 124.0,
                "capacity": 4,
                "bed_type": "2 King Bedrooms",
                "size": "1,400 sq ft",
                "amenities": ["Full Sea Panorama", "Grand Living Hall", "Private Bar & Pantry", "Dedicated Valet"],
                "image": "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=1000&q=80",
                "description": "Unrivaled oceanfront grandeur decorated with museum-piece colonial oil paintings and crystal chandeliers."
            }
        ]
    },
    {
        "name": "The Grand Azure Palace & Spa",
        "description": "A magnificent 5-star royal heritage palace perched along the tranquil waters of Lake Pichola. Features hand-carved stone arches, royal courtyards, luxury Ayurvedic wellness spa, and fine dining under the stars.",
        "city": "Udaipur",
        "address": "Haridas Ji Ki Magri, Lake Pichola Waterfront, Udaipur, Rajasthan 313001",
        "rating": 4.9,
        "review_count": 864,
        "price_per_night_start": 37.0,
        "currency": "$",
        "hotel_type": "Heritage Palace",
        "cover_image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80",
            "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Lakefront Infinity Pool",
            "Ayurvedic Spa & Wellness",
            "Complimentary Breakfast",
            "High-Speed Wi-Fi",
            "24/7 Butler Service",
            "Fine Dining Restaurant"
        ],
        "rooms": [
            {
                "id": "rm-lake-deluxe",
                "name": "Deluxe Lake View Suite",
                "price_per_night": 37.0,
                "capacity": 2,
                "bed_type": "1 King Bed",
                "size": "550 sq ft",
                "amenities": ["Lake View Balcony", "Marble Bathtub", "Complimentary Breakfast", "High-Speed Wi-Fi"],
                "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80",
                "description": "Panoramic sunset views over the water, hand-carved jharokha balconies, and plush Egyptian cotton linens."
            },
            {
                "id": "rm-royal-heritage",
                "name": "Executive Royal Heritage Suite",
                "price_per_night": 64.0,
                "capacity": 3,
                "bed_type": "1 Super King Bed + Living Lounge",
                "size": "920 sq ft",
                "amenities": ["Private Jacuzzi", "Separate Living Room", "Executive Club Lounge", "Chauffeured Transfer"],
                "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80",
                "description": "Features a private jacuzzi overlooking royal courtyards and dedicated afternoon tea service."
            }
        ]
    },
    {
        "name": "Taj Fort Heritage Haveli",
        "description": "Nestled in the heart of the Pink City, this converted 18th-century Rajput haveli offers majestic fresco ceilings, lush peacock gardens, heated courtyard swimming pool, and authentic Rajasthani folk music evenings.",
        "city": "Jaipur",
        "address": "Amer Road, Near Jal Mahal, Jaipur, Rajasthan 302002",
        "rating": 4.8,
        "review_count": 620,
        "price_per_night_start": 26.0,
        "currency": "$",
        "hotel_type": "Heritage Haveli",
        "cover_image": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Courtyard Pool",
            "Rooftop Fort View Terrace",
            "Free High-Speed Wi-Fi",
            "Traditional Folk Music",
            "Buffet Breakfast Included",
            "Complimentary Valet Parking"
        ],
        "rooms": [
            {
                "id": "rm-rajput-deluxe",
                "name": "Rajput Heritage Deluxe Room",
                "price_per_night": 26.0,
                "capacity": 2,
                "bed_type": "1 Four-Poster King Bed",
                "size": "480 sq ft",
                "amenities": ["Antique Wooden Furnishings", "Garden Courtyard View", "Free Breakfast", "Wi-Fi"],
                "image": "https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=1000&q=80",
                "description": "Authentic stone archways, hand-painted murals, and bespoke teakwood furniture."
            }
        ]
    },
    {
        "name": "Azure Sands Beachfront Resort & Villas",
        "description": "Set along the pristine golden coastline of South Goa, offering direct beach access, private oceanfront plunge pool villas, beachside shack grill, water sports desk, and sunset yoga sessions.",
        "city": "Goa",
        "address": "Varca Beach Road, South Goa, Goa 403721",
        "rating": 4.8,
        "review_count": 940,
        "price_per_night_start": 30.0,
        "currency": "$",
        "hotel_type": "Beachfront Resort",
        "cover_image": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Private Beach Access",
            "Infinity Pool with Swim-up Bar",
            "Water Sports & Kayaking",
            "Beachfront Seafood Grill",
            "Free Wi-Fi",
            "Sunset Yoga Lawn"
        ],
        "rooms": [
            {
                "id": "rm-ocean-deluxe",
                "name": "Ocean View Garden Suite",
                "price_per_night": 30.0,
                "capacity": 2,
                "bed_type": "1 King Bed",
                "size": "520 sq ft",
                "amenities": ["Private Balcony", "Walk-in Rain Shower", "Direct Beach Walkway", "Free Wi-Fi"],
                "image": "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?auto=format&fit=crop&w=1000&q=80",
                "description": "Step right onto manicured palm lawns leading directly to the white sands of Varca Beach."
            }
        ]
    },
    {
        "name": "Himalayan Pine Forest Retreat & Spa",
        "description": "Perched 2,200 meters above sea level surrounded by whispering cedar pines and snow-capped Himalayan peaks. Features heated wooden chalets, cedarwood fireplaces, open-air hot tubs, and guided alpine treks.",
        "city": "Manali",
        "address": "Log Huts Road, Old Manali, Himachal Pradesh 175131",
        "rating": 4.9,
        "review_count": 510,
        "price_per_night_start": 22.0,
        "currency": "$",
        "hotel_type": "Mountain Chalet",
        "cover_image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Mountain View Heated Rooms",
            "Fireplace & Bonfire Lounge",
            "Alpine Trekking Guides",
            "Cedar Barrel Sauna",
            "Free High-Speed Wi-Fi"
        ],
        "rooms": [
            {
                "id": "rm-cedar-deluxe",
                "name": "Pine View Cedar Chalet",
                "price_per_night": 22.0,
                "capacity": 2,
                "bed_type": "1 King Bed",
                "size": "450 sq ft",
                "amenities": ["Snow Mountain View", "Wood Fireplace", "Heated Wooden Floors", "Tea & Coffee Maker"],
                "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80",
                "description": "Crafted from local deodar cedar wood with floor-to-ceiling glass windows facing the Solang valley peaks."
            }
        ]
    },
    {
        "name": "Emerald Palm Backwaters Resort & Houseboats",
        "description": "Experience God's Own Country in ultimate luxury. Located right on the serene Vembanad backwaters in Kumarakom with private floating houseboats, freshwater lagoon pool, and traditional Kerala Sadhya culinary feasts.",
        "city": "Kerala",
        "address": "Vembanad Lakefront, Kumarakom, Kottayam, Kerala 686563",
        "rating": 4.9,
        "review_count": 780,
        "price_per_night_start": 28.0,
        "currency": "$",
        "hotel_type": "Eco-Luxury Resort",
        "cover_image": "https://images.unsplash.com/photo-1602002418082-a4443e081dd1?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1602002418082-a4443e081dd1?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Lagoon Swimming Pool",
            "Ayurvedic Herbal Treatment Center",
            "Backwater Sunset Cruise",
            "Complimentary Traditional Breakfast",
            "Speedboat Transfers"
        ],
        "rooms": [
            {
                "id": "rm-kerala-cottage",
                "name": "Heritage Backwater Cottage",
                "price_per_night": 28.0,
                "capacity": 2,
                "bed_type": "1 King Bed",
                "size": "500 sq ft",
                "amenities": ["Open-Air Rain Shower", "Waterfront Veranda", "Free Wi-Fi", "Daily Fruit Basket"],
                "image": "https://images.unsplash.com/photo-1602002418082-a4443e081dd1?auto=format&fit=crop&w=1000&q=80",
                "description": "Built in traditional Kerala architectural style with terracotta roofs, open-air courtyards, and lake views."
            }
        ]
    },
    {
        "name": "The Oberoi Amarvilas View Hotel",
        "description": "Located merely 600 meters from the Taj Mahal, every single guest room and suite offers uninterrupted views of the legendary monument of love. Features Mughal terraced pools, cobalt blue fountain courtyards, and royal dining.",
        "city": "Agra",
        "address": "Taj East Gate Road, Agra, Uttar Pradesh 282001",
        "rating": 5.0,
        "review_count": 1240,
        "price_per_night_start": 56.0,
        "currency": "$",
        "hotel_type": "Ultra Luxury",
        "cover_image": "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Unobstructed Taj Mahal Views",
            "Mughal Terraced Heated Pools",
            "Private Golf Cart to Monument",
            "Michelin-Caliber Dining",
            "Full-Service Spa & Steam"
        ],
        "rooms": [
            {
                "id": "rm-taj-premier",
                "name": "Premier Taj View Room",
                "price_per_night": 56.0,
                "capacity": 2,
                "bed_type": "1 King Bed",
                "size": "500 sq ft",
                "amenities": ["Direct Monument View", "Marble Bath with Taj View", "High-Speed Wi-Fi", "Luxury Butler Service"],
                "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80",
                "description": "Wake up to the soft morning mist rising above the white marble dome of the Taj Mahal directly from your bed."
            }
        ]
    },
    {
        "name": "BrijRama Palace on the Ganges Ghats",
        "description": "One of the oldest landmark palaces in Varanasi perched directly atop Darbhanga Ghat since the 18th century. Reached only by private heritage wooden boat ride, with evening Ganga Aarti ceremonies visible right from your room.",
        "city": "Varanasi",
        "address": "Darbhanga Ghat, Dashashwamedh, Varanasi, Uttar Pradesh 221001",
        "rating": 4.9,
        "review_count": 680,
        "price_per_night_start": 35.0,
        "currency": "$",
        "hotel_type": "Heritage River Palace",
        "cover_image": "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Direct Ganges Ghat Access",
            "Private Sunrise Boat Cruise",
            "Pure Vegetarian Gourmet Dining",
            "Classical Sitar Music Evenings",
            "Free High-Speed Wi-Fi"
        ],
        "rooms": [
            {
                "id": "varanasi-river-suite",
                "name": "Darbhanga Riverfront Suite",
                "price_per_night": 35.0,
                "capacity": 2,
                "bed_type": "1 King Bed",
                "size": "480 sq ft",
                "amenities": ["River View Bay Window", "Handcrafted Silk Upholstery", "Free Morning Boat Tour", "Breakfast Included"],
                "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80",
                "description": "Gaze over ancient pilgrim boats and sacred morning sunrises across the holy River Ganga."
            }
        ]
    },
    {
        "name": "The Khyber Himalayan Resort & Ski Spa",
        "description": "Nestled among 7 acres of pristine sylvan conifer forest at 8,825 feet in Gulmarg, Kashmir. Moments from the world's highest Gulmarg Gondola ski lift, featuring indoor heated swimming pools facing Pir Panjal snow peaks.",
        "city": "Kashmir",
        "address": "Near Gondola Base, Gulmarg, Baramulla, Jammu & Kashmir 193403",
        "rating": 4.9,
        "review_count": 890,
        "price_per_night_start": 44.0,
        "currency": "$",
        "hotel_type": "Alpine Ski Resort",
        "cover_image": "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Heated Glass Swimming Pool",
            "Ski Equipment & Gondola Concierge",
            "L'Occitane Luxury Alpine Spa",
            "Traditional Kashmiri Wazwan Feast",
            "High-Speed Wi-Fi"
        ],
        "rooms": [
            {
                "id": "kashmir-pine-deluxe",
                "name": "Pir Panjal Snow View Room",
                "price_per_night": 44.0,
                "capacity": 2,
                "bed_type": "1 King Bed",
                "size": "540 sq ft",
                "amenities": ["Snow Peak Balcony", "Walnut Wood Carvings", "Underfloor Heating", "Free Breakfast"],
                "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80",
                "description": "Warm Kashmiri walnut craftsmanship with panoramic vistas of pine forests blankets in fresh snow."
            }
        ]
    },
    {
        "name": "Ganga Kinare Himalayan Riverfront Sanctuary",
        "description": "A tranquil riverside wellness retreat located right on the banks of the sacred Ganges in Rishikesh. Offers private ghat steps, daily Kundalini & Hatha yoga sessions, sound healing, and rafting concierge.",
        "city": "Rishikesh",
        "address": "23 Barrage Road, Tapovan, Rishikesh, Uttarakhand 249201",
        "rating": 4.8,
        "review_count": 570,
        "price_per_night_start": 19.0,
        "currency": "$",
        "hotel_type": "Riverfront Wellness Retreat",
        "cover_image": "https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Private River Ghat",
            "Daily Morning & Evening Yoga",
            "Ayurvedic Spa & Herbal Baths",
            "Organic Vegetarian Restaurant",
            "Free Wi-Fi",
            "White Water Rafting Desk"
        ],
        "rooms": [
            {
                "id": "rishikesh-ganga-deluxe",
                "name": "Holy Riverfront Deluxe Room",
                "price_per_night": 19.0,
                "capacity": 2,
                "bed_type": "1 King Bed",
                "size": "420 sq ft",
                "amenities": ["Riverfront Balcony", "Yoga Mats Included", "Complimentary Herbal Tea", "Wi-Fi"],
                "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80",
                "description": "Wake up to the meditative sound of the flowing river and chant mantras from your private balcony."
            }
        ]
    },
    {
        "name": "Wildflower Cedar Mountain Sanctuary",
        "description": "Situated 8,350 feet above sea level in the Shimla Himalayas, once the private residence of Lord Kitchener. Features heated outdoor infinity whirlpools with mountain views, colonial billiards lounge, and deodar forest trails.",
        "city": "Shimla",
        "address": "Chharabra, Shimla Hills, Himachal Pradesh 171012",
        "rating": 4.9,
        "review_count": 730,
        "price_per_night_start": 32.0,
        "currency": "$",
        "hotel_type": "Colonial Heritage Sanctuary",
        "cover_image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Outdoor Heated Mountain Whirlpool",
            "Indoor Swimming Pool with Chandeliers",
            "Guided Pine Forest Mountain Biking",
            "Bespoke High Tea Service",
            "Free Wi-Fi"
        ],
        "rooms": [
            {
                "id": "shimla-premier-cedar",
                "name": "Premier Mountain Valley Room",
                "price_per_night": 32.0,
                "capacity": 2,
                "bed_type": "1 Four-Poster King Bed",
                "size": "500 sq ft",
                "amenities": ["Snow Valley Panorama", "Teak Fireplace", "Marble Soaking Tub", "Breakfast Included"],
                "image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1000&q=80",
                "description": "Rich Burmese teak flooring, crackling fireplace, and breathtaking views over the Greater Himalayas."
            }
        ]
    },
    {
        "name": "Taj Falaknuma Hilltop Palace",
        "description": "Perched 2,000 feet above the city of pearls, this magnificent Italian marble palace was the residence of the world's richest royal, the Nizam of Hyderabad. Arrive via royal horse-drawn carriage and walk marble stairways lined with rare Venetian chandeliers.",
        "city": "Hyderabad",
        "address": "Engine Bowli, Fatima Nagar, Falaknuma, Hyderabad, Telangana 500053",
        "rating": 5.0,
        "review_count": 1620,
        "price_per_night_start": 62.0,
        "currency": "$",
        "hotel_type": "Royal Nizam Palace",
        "cover_image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Horse-drawn Carriage Arrival",
            "Heritage Royal Library & Hookah Lounge",
            "Jade Terrace City Panorama",
            "Bespoke Nizam Culinary Dining",
            "Jiva Palace Spa"
        ],
        "rooms": [
            {
                "id": "hyderabad-palace-room",
                "name": "Nizam Heritage Palace Room",
                "price_per_night": 62.0,
                "capacity": 2,
                "bed_type": "1 Royal King Bed",
                "size": "580 sq ft",
                "amenities": ["Courtyard Fountain View", "Ornate Italian Plasterwork", "Dedicated Palace Butler", "Breakfast Included"],
                "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80",
                "description": "Live like royalty surrounded by century-old frescos, hand-carved walnut furniture, and royal courtesies."
            }
        ]
    },
    {
        "name": "The Leela Palace Bengaluru",
        "description": "Inspired by the architectural grandeur of the Royal Palace of Mysore. Stand in acres of lush botanical gardens with copper domes, cascading waterfalls, world-class golf concierges, and premier luxury dining.",
        "city": "Bengaluru",
        "address": "23 HAL Old Airport Road, Kodihalli, Bengaluru, Karnataka 560008",
        "rating": 4.9,
        "review_count": 1180,
        "price_per_night_start": 34.0,
        "currency": "$",
        "hotel_type": "Royal Garden Palace",
        "cover_image": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Botanical Lagoon Pool",
            "Ayurvedic Luxury Spa",
            "Jamavar Royal Indian Dining",
            "High-Speed Fiber Wi-Fi",
            "Airport Luxury Car Service"
        ],
        "rooms": [
            {
                "id": "bengaluru-deluxe",
                "name": "Royal Garden View Deluxe Room",
                "price_per_night": 34.0,
                "capacity": 2,
                "bed_type": "1 King Bed",
                "size": "520 sq ft",
                "amenities": ["Garden & Waterfall View", "Walk-in Rain Shower", "Signature Turndown Service", "Free Wi-Fi"],
                "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80",
                "description": "Serene retreat surrounded by lush tropical palms and soothing palace fountains in India's Silicon Valley."
            }
        ]
    },
    {
        "name": "The Grand Dragon Ladakh Hotel",
        "description": "The first 5-star luxury hotel in Leh Ladakh. Blends traditional Ladakhi wood architecture and Buddhist stupa aesthetics with state-of-the-art solar heating, oxygen enrichment facilities, and 360-degree views of the Stok Kangri mountains.",
        "city": "Ladakh",
        "address": "Old Road Sheynam, Leh, Ladakh, UT 194101",
        "rating": 4.8,
        "review_count": 640,
        "price_per_night_start": 29.0,
        "currency": "$",
        "hotel_type": "Himalayan Stupa Hotel",
        "cover_image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Stok Kangri Mountain Panorama",
            "Central Solar Underfloor Heating",
            "Oxygen Enrichment Support",
            "Tibetan Herbal Dining",
            "Free Wi-Fi"
        ],
        "rooms": [
            {
                "id": "ladakh-premier",
                "name": "Heritage Stok Kangri Mountain View",
                "price_per_night": 29.0,
                "capacity": 2,
                "bed_type": "1 King Bed",
                "size": "460 sq ft",
                "amenities": ["Glacier Mountain View", "Traditional Thangka Art", "Heated Bathroom", "Breakfast Included"],
                "image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1000&q=80",
                "description": "Wake up to dramatic snow-covered peaks, prayer flags flutter in the breeze, and personalized Tibetan tea."
            }
        ]
    },
    {
        "name": "Suryagarh Golden Fort Desert Fortress",
        "description": "A breathtaking desert fortress rising from the golden sands of the Thar Desert. Features ancient sandstone carvings, traditional desert musical performances under starry skies, camel safari excursions, and luxury courtyard pools.",
        "city": "Jaisalmer",
        "address": "Kahala Phata, Sam Road, Jaisalmer, Rajasthan 345001",
        "rating": 4.9,
        "review_count": 910,
        "price_per_night_start": 33.0,
        "currency": "$",
        "hotel_type": "Desert Fortress",
        "cover_image": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Thar Desert Sunsets",
            "Courtyard Indoor Heated Pool",
            "Camel & Jeep Dune Safaris",
            "Rajasthani Royal Thali Dining",
            "Free Wi-Fi"
        ],
        "rooms": [
            {
                "id": "jaisalmer-sandstone-room",
                "name": "Golden Sandstone Fortress Room",
                "price_per_night": 33.0,
                "capacity": 2,
                "bed_type": "1 Handcrafted King Bed",
                "size": "510 sq ft",
                "amenities": ["Dune Horizon View", "Yellow Jaisalmer Stone Architecture", "Free Breakfast", "Wi-Fi"],
                "image": "https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=1000&q=80",
                "description": "Carved entirely from local golden sandstone with custom brass lamps and desert breezes."
            }
        ]
    },
    {
        "name": "Savoy Nilgiri Tea Hills Retreat",
        "description": "A historic British colonial retreat established in 1841 amidst fragrant eucalyptus groves and terraced Nilgiri tea gardens in Ooty. Features crackling log fireplaces in every room, English afternoon tea, and croquet lawns.",
        "city": "Ooty",
        "address": "77 Sylks Road, Ootacamund, Nilgiris, Tamil Nadu 643001",
        "rating": 4.8,
        "review_count": 520,
        "price_per_night_start": 25.0,
        "currency": "$",
        "hotel_type": "Tea Estate Heritage",
        "cover_image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Nilgiri Tea Garden Trails",
            "In-room Wood Burning Fireplaces",
            "English High Tea & Scones",
            "Botanical Garden Tours",
            "Free Wi-Fi"
        ],
        "rooms": [
            {
                "id": "ooty-colonial-cottage",
                "name": "Heritage Fireplace Garden Cottage",
                "price_per_night": 25.0,
                "capacity": 2,
                "bed_type": "1 King Bed",
                "size": "460 sq ft",
                "amenities": ["Eucalyptus Garden Veranda", "Wood Fireplace", "English Breakfast Included", "Wi-Fi"],
                "image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1000&q=80",
                "description": "Step into 19th-century hill station elegance with evening fireplace lighting by your personal butler."
            }
        ]
    },
    {
        "name": "The Oberoi Grand Victoria Heritage",
        "description": "Affectionately known as 'The Grande Dame of Chowringhee'. Located on Kolkata's historic boulevard, featuring classical Victorian neoclassical colonnades, palm-shaded courtyard swimming pools, and legendary Thai & Bengali banquets.",
        "city": "Kolkata",
        "address": "15 Jawaharlal Nehru Road, New Market Area, Kolkata, West Bengal 700013",
        "rating": 4.9,
        "review_count": 980,
        "price_per_night_start": 23.0,
        "currency": "$",
        "hotel_type": "Victorian Grand Hotel",
        "cover_image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Palm Courtyard Swimming Pool",
            "Baan Thai Specialty Dining",
            "Therapeutic Wellness Spa",
            "Central Kolkata Location",
            "Free Wi-Fi"
        ],
        "rooms": [
            {
                "id": "kolkata-heritage-deluxe",
                "name": "Victorian Courtyard Deluxe Room",
                "price_per_night": 23.0,
                "capacity": 2,
                "bed_type": "1 King Bed",
                "size": "480 sq ft",
                "amenities": ["Pool Courtyard View", "High Victorian Ceilings", "Free Breakfast", "Wi-Fi"],
                "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80",
                "description": "14-foot colonial high ceilings, polished teak furnishings, and views over peaceful palm-shaded waters."
            }
        ]
    },
    {
        "name": "Glenburn Tea Estate & Himalayan Retreat",
        "description": "A tranquil 1,600-acre working tea estate overlooking the majestic Kanchenjunga peak in Darjeeling. Experience private tea tastings, river picnics on the banks of the Rangeet, and cozy fireside four-course dinners.",
        "city": "Darjeeling",
        "address": "Near Singritan, Darjeeling Hills, West Bengal 734101",
        "rating": 5.0,
        "review_count": 480,
        "price_per_night_start": 38.0,
        "currency": "$",
        "hotel_type": "Tea Estate Luxury",
        "cover_image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Mount Kanchenjunga Peak Views",
            "Private Tea Plucking Tours",
            "River Beach Bonfires & Rafting",
            "All Gourmet Meals Included",
            "Free Wi-Fi"
        ],
        "rooms": [
            {
                "id": "darjeeling-kanchenjunga",
                "name": "Kanchenjunga Vista Heritage Suite",
                "price_per_night": 38.0,
                "capacity": 2,
                "bed_type": "1 Hand-carved King Bed",
                "size": "560 sq ft",
                "amenities": ["Unobstructed Peak Panorama", "Free-standing Clawfoot Tub", "All Meals & Tea Tastings Included"],
                "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80",
                "description": "Watch sunrise paint the snows of Mount Kanchenjunga in shades of gold and pink directly from your bed."
            }
        ]
    },
    {
        "name": "Golden Crown Heritage Grand Amritsar",
        "description": "A majestic Punjabi hospitality haven situated just 10 minutes from the sacred Golden Temple. Features marble courtyards, traditional Amritsari tandoori kitchen, heated wellness pool, and complimentary Temple shuttle.",
        "city": "Amritsar",
        "address": "Mall Road, Near Golden Temple, Amritsar, Punjab 143001",
        "rating": 4.8,
        "review_count": 690,
        "price_per_night_start": 17.0,
        "currency": "$",
        "hotel_type": "Cultural Heritage",
        "cover_image": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80",
        "images": [
            "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80"
        ],
        "amenities": [
            "Golden Temple Shuttle Service",
            "Heated Outdoor Pool",
            "Authentic Amritsari Tandoor Dining",
            "Ayurvedic Spa",
            "Free Wi-Fi"
        ],
        "rooms": [
            {
                "id": "amritsar-deluxe",
                "name": "Royal Punjabi Deluxe Room",
                "price_per_night": 17.0,
                "capacity": 2,
                "bed_type": "1 King Bed",
                "size": "440 sq ft",
                "amenities": ["Courtyard Pool View", "Marble Bath", "Complimentary Amritsari Breakfast", "Wi-Fi"],
                "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80",
                "description": "Warm Punjabi hospitality with hand-embroidered Phulkari textiles and daily traditional buffet breakfasts."
            }
        ]
    }
]

async def seed_hotels():
    db = get_db()
    print("Seeding All-India Hotels into MongoDB...")
    await db.hotels.delete_many({})
    result = await db.hotels.insert_many(HOTELS_SEED_DATA)
    print(f"Successfully seeded {len(result.inserted_ids)} All-India hotels into MongoDB!")

if __name__ == "__main__":
    asyncio.run(seed_hotels())
