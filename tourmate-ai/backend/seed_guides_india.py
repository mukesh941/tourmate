import asyncio
import os
import random
from dotenv import load_dotenv

# Load env variables before getting the db client so MONGO_URI is picked up
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.core.database import get_db, close_client

STATES_AND_CITIES = {
    "Andhra Pradesh": ["Amaravati", "Visakhapatnam", "Vijayawada", "Tirupati"],
    "Arunachal Pradesh": ["Itanagar", "Tawang", "Ziro", "Bomdila"],
    "Assam": ["Guwahati", "Kaziranga", "Jorhat", "Majuli"],
    "Bihar": ["Patna", "Bodh Gaya", "Gaya", "Rajgir", "Nalanda"],
    "Chhattisgarh": ["Raipur", "Jagdalpur", "Bilaspur"],
    "Goa": ["Panaji", "Calangute", "Candolim", "Old Goa", "Margao"],
    "Gujarat": ["Ahmedabad", "Vadodara", "Surat", "Dwarka", "Somnath", "Rann of Kutch", "Bhuj"],
    "Haryana": ["Gurugram", "Faridabad", "Kurukshetra"],
    "Himachal Pradesh": ["Shimla", "Manali", "Dharamshala", "Dalhousie", "Kasol", "Kullu", "Spiti"],
    "Jharkhand": ["Ranchi", "Jamshedpur", "Deoghar"],
    "Karnataka": ["Bengaluru", "Mysuru", "Hampi", "Coorg", "Mangaluru", "Hubballi", "Gokarna", "Badami"],
    "Kerala": ["Thiruvananthapuram", "Kochi", "Munnar", "Alappuzha", "Kozhikode", "Kovalam", "Varkala", "Thekkady", "Wayanad"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Ujjain", "Gwalior", "Khajuraho", "Jabalpur", "Sanchi"],
    "Maharashtra": ["Mumbai", "Pune", "Nashik", "Nagpur", "Aurangabad", "Mahabaleshwar", "Lonavala", "Shirdi", "Alibaug"],
    "Manipur": ["Imphal", "Loktak Lake"],
    "Meghalaya": ["Shillong", "Cherrapunji", "Dawki", "Mawlynnong"],
    "Mizoram": ["Aizawl", "Champhai"],
    "Nagaland": ["Kohima", "Dimapur"],
    "Odisha": ["Bhubaneswar", "Puri", "Konark", "Cuttack", "Chilika"],
    "Punjab": ["Amritsar", "Ludhiana", "Patiala", "Jalandhar"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Jaisalmer", "Pushkar", "Mount Abu", "Ajmer", "Bikaner"],
    "Sikkim": ["Gangtok", "Pelling", "Lachung", "Namchi"],
    "Tamil Nadu": ["Chennai", "Madurai", "Ooty", "Coimbatore", "Rameswaram", "Kanyakumari", "Thanjavur", "Mahabalipuram"],
    "Telangana": ["Hyderabad", "Warangal", "Karimnagar"],
    "Tripura": ["Agartala", "Udaipur"],
    "Uttar Pradesh": ["Lucknow", "Agra", "Varanasi", "Ayodhya", "Prayagraj", "Mathura", "Vrindavan", "Sarnath", "Jhansi"],
    "Uttarakhand": ["Dehradun", "Rishikesh", "Haridwar", "Nainital", "Mussoorie", "Almora", "Auli", "Kedarnath", "Badrinath"],
    "West Bengal": ["Kolkata", "Darjeeling", "Siliguri", "Kalimpong", "Digha", "Sundarbans"],
    "Jammu and Kashmir": ["Srinagar", "Gulmarg", "Pahalgam", "Jammu", "Sonamarg"],
    "Ladakh": ["Leh", "Nubra Valley", "Pangong Lake", "Kargil"],
    "Delhi": ["New Delhi", "Delhi"],
    "Andaman and Nicobar Islands": ["Port Blair", "Havelock Island", "Neil Island"],
    "Chandigarh": ["Chandigarh"],
    "Lakshadweep": ["Kavaratti", "Agatti"],
    "Puducherry": ["Puducherry", "Auroville"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Daman", "Diu", "Silvassa"]
}

LANGUAGES_BY_STATE = {
    "Andhra Pradesh": ["Telugu"], "Arunachal Pradesh": ["Nyishi", "Adi"], "Assam": ["Assamese"],
    "Bihar": ["Bhojpuri", "Maithili"], "Chhattisgarh": ["Chhattisgarhi"], "Goa": ["Konkani"],
    "Gujarat": ["Gujarati"], "Haryana": ["Haryanvi"], "Himachal Pradesh": ["Pahari"],
    "Jharkhand": ["Santali"], "Karnataka": ["Kannada"], "Kerala": ["Malayalam"],
    "Madhya Pradesh": ["Hindi"], "Maharashtra": ["Marathi"], "Manipur": ["Meiteilon"],
    "Meghalaya": ["Khasi", "Garo"], "Mizoram": ["Mizo"], "Nagaland": ["Nagamese"],
    "Odisha": ["Odia"], "Punjab": ["Punjabi"], "Rajasthan": ["Rajasthani", "Marwari"],
    "Sikkim": ["Nepali", "Sikkimese"], "Tamil Nadu": ["Tamil"], "Telangana": ["Telugu"],
    "Tripura": ["Kokborok", "Bengali"], "Uttar Pradesh": ["Hindi"], "Uttarakhand": ["Garhwali", "Kumaoni"],
    "West Bengal": ["Bengali"], "Jammu and Kashmir": ["Kashmiri", "Dogri"], "Ladakh": ["Ladakhi"],
    "Delhi": ["Hindi", "Punjabi"], "Andaman and Nicobar Islands": ["Bengali", "Tamil"],
    "Chandigarh": ["Punjabi"], "Lakshadweep": ["Malayalam", "Mahl"], "Puducherry": ["Tamil", "French"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Gujarati", "Marathi"]
}

FIRST_NAMES = ["Amit", "Priya", "Rahul", "Anjali", "Vikram", "Sneha", "Karthik", "Divya", "Suresh", "Pooja"]
LAST_NAMES = ["Kumar", "Sharma", "Singh", "Patil", "Reddy", "Nair", "Das", "Gupta", "Joshi", "Iyer"]
IMAGES = [
    "/images/guides/guide_1.jpg",
    "/images/guides/guide_2.jpg",
    "/images/guides/guide_3.jpg",
    "/images/guides/guide_4.jpg",
    "/images/guides/guide_5.jpg"
]

def generate_guides():
    random.seed(20260924)  # Deterministic
    guides = []
    
    for state, cities_list in STATES_AND_CITIES.items():
        for city in cities_list:
            num_guides = random.randint(1, 3)
            for _ in range(num_guides):
                name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                
                langs = ["English", "Hindi"]
                local_langs = LANGUAGES_BY_STATE.get(state, [])
                if local_langs:
                    langs.append(random.choice(local_langs))
                
                # Make them unique
                langs = list(dict.fromkeys(langs))
                
                guide = {
                    "name": name,
                    "languages": langs,
                    "rating": round(random.uniform(4.0, 5.0), 1),
                    "reviews_count": random.randint(10, 500),
                    "hourly_rate": random.choice([400, 500, 600, 750, 800, 1000]),
                    "bio": f"Local Expert for {city}. Passionate about showing the best of {state}'s culture and heritage.",
                    "verified": False,
                    "is_demo": True,
                    "is_lgbtq": random.random() < 0.15,
                    "image_url": random.choice(IMAGES),
                    "location": f"{city}, {state}, India",
                    "country": "India",
                    "state_or_ut": state,
                    "city": city
                }
                guides.append(guide)
                
    return guides


async def seed():
    db = get_db()
    
    # clear only the guides collection
    await db.guides.delete_many({})
    
    # generate and insert
    guides = generate_guides()
    if guides:
        await db.guides.insert_many(guides)
        
    print(f"Inserted {len(guides)} demo guide profiles across India.")
    close_client()


if __name__ == "__main__":
    asyncio.run(seed())
