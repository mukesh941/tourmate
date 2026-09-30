import asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.deps import get_current_user_dependency
from app.schemas.auth import UserPublic

# Mock user for bypassing auth
mock_user = UserPublic(id=str(uuid.uuid4()), email="test@example.com", name="Test User", role="user", preferred_language="en")
app.dependency_overrides[get_current_user_dependency] = lambda: mock_user

async def run_tests():
    test_queries = [
        "Plan a trip to Delhi",
        "Plan a trip to dehli",
        "Plan a trip to Bangalore",
        "Plan a trip to Bengaluru",
        "Plan a trip to Mumbai",
        "Plan a trip to Bombay",
        "Plan a trip to Paris",
        "Tell me about Delhi attractions",
        "Tell me about Paris attractions",
        "Tell me about tourist places in Lakshadweep",
        "What to do in Andaman and Nicobar Islands",
        "Are there any cafes near RR Layout",
        "Suggest romantic places in Kerala",
        "Find me beaches near Goa",
        "What are the best places to visit in Pondicherry?",
        "" # Empty query
    ]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for q in test_queries:
            print(f"\n======================================")
            print(f"QUERY: '{q}'")
            try:
                res = await client.post(
                    "/api/ai/chat",
                    json={"message": q, "history": []},
                    timeout=30.0
                )
                data = res.json()
                if data.get("success"):
                    resp_data = data.get("data")
                    if resp_data:
                        print(f"Response: {resp_data.get('response', '')[:150]}...")
                        if 'location' in resp_data:
                             print(f"Location: {resp_data['location']}")
                        if resp_data.get('sources'):
                             print(f"Sources: {[s['title'] for s in resp_data['sources']]}")
                    else:
                        print("Data is None")
                else:
                    print(f"Error Response: {data.get('error') or data}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_tests())

