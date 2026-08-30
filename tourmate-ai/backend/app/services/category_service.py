from bson import ObjectId
from app.core.database import get_db
from app.models.category import CategoryInDB
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse

async def get_all_categories() -> list[CategoryResponse]:
    db = get_db()
    cursor = db.categories.find()
    categories = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        categories.append(CategoryResponse(**doc))
    return categories

async def get_category(category_id: str) -> CategoryResponse | None:
    db = get_db()
    doc = await db.categories.find_one({"_id": ObjectId(category_id)})
    if doc:
        doc["id"] = str(doc["_id"])
        return CategoryResponse(**doc)
    return None

async def create_category(payload: CategoryCreate) -> CategoryResponse:
    db = get_db()
    new_cat = CategoryInDB(**payload.dict())
    result = await db.categories.insert_one(new_cat.dict())
    doc = await db.categories.find_one({"_id": result.inserted_id})
    doc["id"] = str(doc["_id"])
    return CategoryResponse(**doc)

async def update_category(category_id: str, payload: CategoryUpdate) -> CategoryResponse | None:
    db = get_db()
    update_data = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    if update_data:
        await db.categories.update_one({"_id": ObjectId(category_id)}, {"$set": update_data})
    return await get_category(category_id)

async def delete_category(category_id: str) -> bool:
    db = get_db()
    result = await db.categories.delete_one({"_id": ObjectId(category_id)})
    return result.deleted_count > 0
