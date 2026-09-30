import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.deps import get_current_user_dependency
from app.schemas.auth import UserPublic
import uuid

mock_user = UserPublic(id=str(uuid.uuid4()), email='test@test.com', name='Test', role='user', preferred_language='en')
app.dependency_overrides[get_current_user_dependency] = lambda: mock_user

async def run():
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=True), base_url='http://test') as client:
        payload = {
            'message': 'What hotels are there?',
            'history': [
                {'role': 'user', 'content': 'Plan a trip to Goa for 3 days'}
            ]
        }
        res = await client.post('/api/ai/chat', json=payload)
        print(res.json())

if __name__ == "__main__":
    asyncio.run(run())
