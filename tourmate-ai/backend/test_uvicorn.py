import asyncio
import httpx
from app.core.security import create_access_token

async def run_tests():
    test_cases = [
        "Plan a trip to Goa",
        "Plan a trip to Banglore",
        "Hotels near RR Layout",
        "Plan a trip to Paris",
        "Plan a trip to XYZABC123",
        "Actually change it to Jaipur"
    ]
    
    token = create_access_token({"sub": "testuser"})
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        for case in test_cases:
            print(f"\n--- Testing: {case} ---")
            try:
                res = await client.post(
                    "http://127.0.0.1:8000/api/ai/chat",
                    json={"message": case, "history": []},
                    headers=headers,
                    timeout=30.0
                )
                print("Status:", res.status_code)
                if res.status_code == 200:
                    print("Response:", res.json().get("response"))
                else:
                    print("Error Body:", res.text)
            except Exception as e:
                print("Exception:", e)

if __name__ == "__main__":
    asyncio.run(run_tests())
