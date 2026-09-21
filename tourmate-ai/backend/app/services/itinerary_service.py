import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict
from app.schemas.itinerary import ItineraryCreate, ItineraryUpdate, ItineraryResponse

# Safe in-memory store for created user itineraries
_saved_itineraries: Dict[str, dict] = {}


async def get_user_itineraries(user_id: str) -> List[ItineraryResponse]:
    uid = str(user_id)
    results = [
        ItineraryResponse(**item)
        for item in _saved_itineraries.values()
        if str(item.get("user_id")) == uid
    ]
    results.sort(key=lambda x: x.created_at, reverse=True)
    return results


async def get_itinerary(itinerary_id: str, user_id: str) -> Optional[ItineraryResponse]:
    item = _saved_itineraries.get(str(itinerary_id))
    if item and str(item.get("user_id")) == str(user_id):
        return ItineraryResponse(**item)
    return None


async def create_itinerary(user_id: str, payload: ItineraryCreate) -> ItineraryResponse:
    itin_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    data = payload.dict()
    data.update({
        "id": itin_id,
        "user_id": str(user_id),
        "created_at": now,
        "updated_at": now,
    })
    _saved_itineraries[itin_id] = data
    return ItineraryResponse(**data)


async def update_itinerary(itinerary_id: str, user_id: str, payload: ItineraryUpdate) -> Optional[ItineraryResponse]:
    item = _saved_itineraries.get(str(itinerary_id))
    if not item or str(item.get("user_id")) != str(user_id):
        return None

    update_data = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    item.update(update_data)
    item["updated_at"] = datetime.now(timezone.utc)
    _saved_itineraries[str(itinerary_id)] = item
    return ItineraryResponse(**item)


async def delete_itinerary(itinerary_id: str, user_id: str) -> bool:
    iid = str(itinerary_id)
    if iid in _saved_itineraries and str(_saved_itineraries[iid].get("user_id")) == str(user_id):
        del _saved_itineraries[iid]
        return True
    return False
