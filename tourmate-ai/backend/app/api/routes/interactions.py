from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from bson import ObjectId

from app.api.deps import get_current_user_dependency
from app.schemas.auth import UserPublic
from app.models.interaction import FavoriteInDB, ReviewInDB, ReviewResponse
from app.core.database import get_db
from app.schemas.common import Envelope
from app.services.sentiment_service import analyze_sentiment

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
        try:
            place = await db.tourist_places.find_one({"_id": ObjectId(fav["place_id"])})
            if place:
                place["id"] = str(place["_id"])
                del place["_id"]
                places.append(place)
        except Exception:
            continue
            
    return Envelope(success=True, data=places)

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
    
    # Run NLP Sentiment Analysis
    sentiment_result = analyze_sentiment(review.comment, review.rating)
        
    rev = ReviewInDB(
        user_id=current_user.id,
        place_id=place_id,
        rating=review.rating,
        comment=review.comment,
        sentiment_label=sentiment_result["sentiment_label"],
        sentiment_score=sentiment_result["sentiment_score"],
        sentiment_emoji=sentiment_result["sentiment_emoji"]
    )
    
    result = await db.reviews.insert_one(rev.model_dump())
    
    # Update average rating of place
    try:
        cursor = db.reviews.find({"place_id": place_id})
        all_reviews = await cursor.to_list(length=None)
        avg_rating = sum(r["rating"] for r in all_reviews) / len(all_reviews) if all_reviews else 0.0
        await db.tourist_places.update_one({"_id": ObjectId(place_id)}, {"$set": {"rating": round(avg_rating, 1)}})
    except Exception:
        pass
    
    return Envelope(success=True, data={
        "id": str(result.inserted_id),
        "sentiment_label": sentiment_result["sentiment_label"],
        "sentiment_score": sentiment_result["sentiment_score"],
        "sentiment_emoji": sentiment_result["sentiment_emoji"]
    })

@router.get("/reviews/{place_id}", response_model=Envelope[List[ReviewResponse]])
async def get_reviews(place_id: str):
    db = get_db()
    cursor = db.reviews.find({"place_id": place_id}).sort("created_at", -1)
    reviews_db = await cursor.to_list(length=100)
    
    result = []
    for r in reviews_db:
        user = None
        try:
            user = await db.users.find_one({"_id": ObjectId(r["user_id"])})
        except Exception:
            pass
        
        # If sentiment missing in older DB record, analyze dynamically
        sentiment_label = r.get("sentiment_label")
        sentiment_score = r.get("sentiment_score")
        sentiment_emoji = r.get("sentiment_emoji")
        if not sentiment_label:
            analyzed = analyze_sentiment(r.get("comment", ""), r.get("rating", 5))
            sentiment_label = analyzed["sentiment_label"]
            sentiment_score = analyzed["sentiment_score"]
            sentiment_emoji = analyzed["sentiment_emoji"]

        result.append(ReviewResponse(
            id=str(r["_id"]),
            user_id=r["user_id"],
            place_id=r["place_id"],
            rating=r["rating"],
            comment=r["comment"],
            sentiment_label=sentiment_label,
            sentiment_score=sentiment_score,
            sentiment_emoji=sentiment_emoji,
            created_at=r["created_at"],
            user_name=user["name"] if user else "Verified Tourist"
        ))
        
    return Envelope(success=True, data=result)

@router.get("/reviews/{place_id}/sentiment-summary", response_model=Envelope[dict])
async def get_review_sentiment_summary(place_id: str):
    """
    Computes overall tourist sentiment distribution using NLP analysis.
    """
    db = get_db()
    cursor = db.reviews.find({"place_id": place_id})
    reviews_db = await cursor.to_list(length=200)

    if not reviews_db:
        return Envelope(success=True, data={
            "total_reviews": 0,
            "positive_pct": 100,
            "neutral_pct": 0,
            "negative_pct": 0,
            "overall_sentiment": "Positive",
            "overall_emoji": "😊"
        })

    pos = 0
    neu = 0
    neg = 0

    for r in reviews_db:
        label = r.get("sentiment_label")
        if not label:
            analyzed = analyze_sentiment(r.get("comment", ""), r.get("rating", 5))
            label = analyzed["sentiment_label"]
        
        if label == "Positive":
            pos += 1
        elif label == "Negative":
            neg += 1
        else:
            neu += 1

    total = len(reviews_db)
    pos_pct = round((pos / total) * 100)
    neu_pct = round((neu / total) * 100)
    neg_pct = round((neg / total) * 100)

    overall = "Positive" if pos >= max(neu, neg) else ("Neutral" if neu >= neg else "Negative")
    overall_emoji = "😊" if overall == "Positive" else ("😐" if overall == "Neutral" else "🙁")

    return Envelope(success=True, data={
        "total_reviews": total,
        "positive_pct": pos_pct,
        "neutral_pct": neu_pct,
        "negative_pct": neg_pct,
        "overall_sentiment": overall,
        "overall_emoji": overall_emoji
    })
