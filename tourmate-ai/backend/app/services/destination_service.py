from bson import ObjectId
from app.core.database import get_db
from app.models.destination import DestinationInDB
from app.schemas.destination import DestinationCreate, DestinationUpdate, DestinationResponse

async def get_all_destinations() -> list[DestinationResponse]:
    db = get_db()
    cursor = db.destinations.find()
    destinations = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        destinations.append(DestinationResponse(**doc))
    return destinations

async def get_destination(destination_id: str) -> DestinationResponse | None:
    db = get_db()
    doc = await db.destinations.find_one({"_id": ObjectId(destination_id)})
    if doc:
        doc["id"] = str(doc["_id"])
        return DestinationResponse(**doc)
    return None

async def create_destination(payload: DestinationCreate) -> DestinationResponse:
    db = get_db()
    new_dest = DestinationInDB(**payload.dict())
    result = await db.destinations.insert_one(new_dest.dict())
    doc = await db.destinations.find_one({"_id": result.inserted_id})
    doc["id"] = str(doc["_id"])
    return DestinationResponse(**doc)

async def update_destination(destination_id: str, payload: DestinationUpdate) -> DestinationResponse | None:
    db = get_db()
    update_data = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    if update_data:
        await db.destinations.update_one({"_id": ObjectId(destination_id)}, {"$set": update_data})
    return await get_destination(destination_id)

async def delete_destination(destination_id: str) -> bool:
    db = get_db()
    result = await db.destinations.delete_one({"_id": ObjectId(destination_id)})
    return result.deleted_count > 0
