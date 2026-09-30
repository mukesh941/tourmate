import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user_dependency

# Bypass Auth
def override_get_current_user():
    class DummyUser:
        id = "dummy"
    return DummyUser()

app.dependency_overrides[get_current_user_dependency] = override_get_current_user
client = TestClient(app)

def run_tests():
    test_cases = [
        "Plan a trip to Goa",
        "Plan a trip to Banglore",
        "Plan a trip to Hampi",
        "Hotels near RR Layout",
        "What can I do in RR Layout?",
        "Distance from Bengaluru to Goa",
        "Plan a trip to Paris",
        "Plan a trip to XYZABC123",
        "Actually change it to Jaipur"
    ]
    
    for case in test_cases:
        print(f"\n--- Testing: {case} ---")
        try:
            res = client.post("/api/ai/chat", json={"message": case, "history": []})
            print("Status:", res.status_code)
            if res.status_code == 200:
                print("Response:", res.json().get("response"))
            else:
                print("Error Body:", res.text)
        except Exception as e:
            print("Exception:", e)

if __name__ == "__main__":
    run_tests()
