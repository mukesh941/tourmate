from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user_dependency
from app.schemas.auth import UserPublic
from app.models.interaction import FavoriteInDB, ReviewInDB, ReviewResponse
from app.core.database import get_db
from app.schemas.common import Envelope
from bson import ObjectId

router = APIRouter()

@router.post("/favorites/{place_id}", response_model=Envelope[dict])
async def toggle_favorite(place_id: str, current_user: UserPublic = Depends(get_current_user_dependency)):
    db = get_db()
    existing = await db.favorites.find_one({"user_id": current_user.id, "place_id": place_id})
    
    if existing:
        await db.favorites.delete_one({"_id": existing["_id"]})
        return Envelope(success=True, data={"status": "removed"})
    else:
        fav = FavoriteInDB(user_id=current_user.id, place_id=place_id)
        await db.favorites.insert_one(fav.model_dump())
        return Envelope(success=True, data={"status": "added"})

@router.get("/favorites", response_model=Envelope[List[dict]])
async def get_favorites(current_user: UserPublic = Depends(get_current_user_dependency)):
    db = get_db()
    cursor = db.favorites.find({"user_id": current_user.id})
    favs = await cursor.to_list(length=100)
    
    # Enrich with place details
    places = []
    for fav in favs:
        place = await db.tourist_places.find_one({"_id": ObjectId(fav["place_id"])})
        if place:
            place["id"] = str(place["_id"])
            del place["_id"]
            places.append(place)
            
    return Envelope(success=True, data=places)

from pydantic import BaseModel
class ReviewCreate(BaseModel):
    rating: int
    comment: str

@router.post("/reviews/{place_id}", response_model=Envelope[dict])
async def add_review(place_id: str, review: ReviewCreate, current_user: UserPublic = Depends(get_current_user_dependency)):
    db = get_db()
    
    # Check if user already reviewed
    existing = await db.reviews.find_one({"user_id": current_user.id, "place_id": place_id})
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this place.")
        
    rev = ReviewInDB(
        user_id=current_user.id,
        place_id=place_id,
        rating=review.rating,
        comment=review.comment
    )
    
    result = await db.reviews.insert_one(rev.model_dump())
    
    # Update average rating of place
    cursor = db.reviews.find({"place_id": place_id})
    all_reviews = await cursor.to_list(length=None)
    avg_rating = sum(r["rating"] for r in all_reviews) / len(all_reviews) if all_reviews else 0.0
    await db.tourist_places.update_one({"_id": ObjectId(place_id)}, {"$set": {"rating": round(avg_rating, 1)}})
    
    return Envelope(success=True, data={"id": str(result.inserted_id)})

@router.get("/reviews/{place_id}", response_model=Envelope[List[ReviewResponse]])
async def get_reviews(place_id: str):
    db = get_db()
    cursor = db.reviews.find({"place_id": place_id}).sort("created_at", -1)
    reviews_db = await cursor.to_list(length=100)
    
    result = []
    for r in reviews_db:
        user = await db.users.find_one({"_id": ObjectId(r["user_id"])})
        result.append(ReviewResponse(
            id=str(r["_id"]),
            user_id=r["user_id"],
            place_id=r["place_id"],
            rating=r["rating"],
            comment=r["comment"],
            created_at=r["created_at"],
            user_name=user["name"] if user else "Unknown User"
        ))
        
    return Envelope(success=True, data=result)
