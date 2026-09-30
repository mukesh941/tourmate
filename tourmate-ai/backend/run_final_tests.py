import asyncio
import json
import random
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user_dependency
from app.db.session import SessionLocal
from app.models.location import Location

# Bypass Auth
def override_get_current_user():
    class DummyUser:
        id = "dummy"
    return DummyUser()

app.dependency_overrides[get_current_user_dependency] = override_get_current_user
client = TestClient(app)

def print_result(name, messages, response):
    print(f"\n{'='*50}")
    print(f"TEST: {name}")
    print(f"{'='*50}")
    for m in messages:
        print(f"User: {m['message']}")
    print(f"\nResponse:\n{response.get('response', '')}")
    if response.get('location'):
        print(f"\nLocation Data Context:\n{json.dumps(response.get('location'), indent=2)[:500]}...")
    print(f"{'='*50}\n")

def chat(message, history):
    res = client.post("/api/ai/chat", json={"message": message, "history": history})
    if res.status_code == 200:
        return res.json()
    return {"response": f"ERROR: {res.text}"}

def run_tests():
    # TEST 1 - 3
    history_1 = []
    msg = "hii i have to plan a trip to Goa for 3 days"
    res1 = chat(msg, history_1)
    history_1.append({"role": "user", "content": msg})
    history_1.append({"role": "model", "content": res1.get("response", "")})
    print_result("TEST 1 - Goa", [{"message": msg}], res1)

    msg = "What hotels are there?"
    res2 = chat(msg, history_1)
    history_1.append({"role": "user", "content": msg})
    history_1.append({"role": "model", "content": res2.get("response", "")})
    print_result("TEST 2 - Goa Hotels (Context)", [{"message": msg}], res2)

    msg = "What places should I visit?"
    res3 = chat(msg, history_1)
    print_result("TEST 3 - Goa Places (Context)", [{"message": msg}], res3)
    
    # TEST 4
    history_4 = []
    msg = "Plan a trip to Mumbai for 3 days"
    res = chat(msg, history_4)
    history_4.append({"role": "user", "content": msg})
    history_4.append({"role": "model", "content": res.get("response", "")})
    
    msg = "No, I meant Goa"
    res = chat(msg, history_4)
    history_4.append({"role": "user", "content": msg})
    history_4.append({"role": "model", "content": res.get("response", "")})

    msg = "What should I visit?"
    res = chat(msg, history_4)
    print_result("TEST 4 - User Correction (Mumbai -> Goa)", [{"message": "Plan a trip to Mumbai for 3 days"}, {"message": "No, I meant Goa"}, {"message": "What should I visit?"}], res)

    # TEST 5
    res = chat("Plan a trip to Bengaluru for 2 days", [])
    print_result("TEST 5 - Bengaluru", [{"message": "Plan a trip to Bengaluru for 2 days"}], res)

    # TEST 6
    res = chat("Plan a trip to Bangalore for 2 days", [])
    print_result("TEST 6 - Bangalore Alias", [{"message": "Plan a trip to Bangalore for 2 days"}], res)

    # TEST 7
    res = chat("Tell me about Udupi", [])
    print_result("TEST 7 - Udupi", [{"message": "Tell me about Udupi"}], res)
    
    # TEST 8
    res = chat("Tourist places in Karnataka", [])
    print_result("TEST 8 - Karnataka state", [{"message": "Tourist places in Karnataka"}], res)

    # TEST 9
    res = chat("Places near Mysuru", [])
    print_result("TEST 9 - Mysuru nearby", [{"message": "Places near Mysuru"}], res)

    # TEST 10
    res = chat("Plan a trip to Jaipur for 3 days", [])
    print_result("TEST 10 - Jaipur", [{"message": "Plan a trip to Jaipur for 3 days"}], res)

    # TEST 11
    res = chat("Things to do in Varanasi", [])
    print_result("TEST 11 - Varanasi", [{"message": "Things to do in Varanasi"}], res)

    # TEST 12
    res = chat("Plan a trip to Paris", [])
    print_result("TEST 12 - Paris", [{"message": "Plan a trip to Paris"}], res)

    # TEST 13
    db = SessionLocal()
    try:
        cities = db.query(Location).filter(Location.type == "city").all()
        if len(cities) > 20:
            random_cities = random.sample(cities, 20)
        else:
            random_cities = cities
        
        city_names = [c.name for c in random_cities]
    finally:
        db.close()
    
    print("\n--- TEST 13 - Random Indian locations ---")
    for city in city_names:
        res = chat(f"Plan a trip to {city}", [])
        print_result(f"TEST 13 - {city}", [{"message": f"Plan a trip to {city}"}], res)


if __name__ == "__main__":
    run_tests()
