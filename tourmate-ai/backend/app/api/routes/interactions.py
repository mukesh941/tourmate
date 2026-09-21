import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_dependency
from app.core.db import get_async_db
from app.schemas.auth import UserPublic
from app.models.sql.interaction import Feedback
from app.models.sql.user import User
from app.models.sql.poi import POI
from app.models.interaction import ReviewResponse
from app.schemas.common import Envelope
from app.services.sentiment_service import analyze_sentiment

router = APIRouter()

# In-memory favorites store: user_id -> set of place_ids
_user_favorites: Dict[str, set] = {}


@router.post("/favorites/{place_id}", response_model=Envelope[dict])
async def toggle_favorite(
    place_id: str,
    current_user: UserPublic = Depends(get_current_user_dependency)
):
    uid = str(current_user.id)
    if uid not in _user_favorites:
        _user_favorites[uid] = set()

    if place_id in _user_favorites[uid]:
        _user_favorites[uid].remove(place_id)
        return Envelope(success=True, data={"status": "removed"})
    else:
        _user_favorites[uid].add(place_id)
        return Envelope(success=True, data={"status": "added"})


@router.get("/favorites", response_model=Envelope[List[dict]])
async def get_favorites(
    current_user: UserPublic = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_async_db),
):
    uid = str(current_user.id)
    place_ids = list(_user_favorites.get(uid, set()))
    if not place_ids:
        return Envelope(success=True, data=[])

    # Lookup places from PostgreSQL
    valid_uuids = []
    for pid in place_ids:
        try:
            valid_uuids.append(uuid.UUID(pid))
        except (ValueError, TypeError):
            pass

    places = []
    if valid_uuids:
        stmt = select(POI).where(POI.id.in_(valid_uuids))
        res = await db.execute(stmt)
        pois = res.scalars().all()
        for p in pois:
            places.append({
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "rating": float(p.rating),
            })

    return Envelope(success=True, data=places)


class ReviewCreate(BaseModel):
    rating: int
    comment: str


@router.post("/reviews/{place_id}", response_model=Envelope[dict])
async def add_review(
    place_id: str,
    review: ReviewCreate,
    current_user: UserPublic = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_async_db),
):
    poi_uuid = None
    try:
        poi_uuid = uuid.UUID(place_id)
    except (ValueError, TypeError):
        pass

    sentiment_result = analyze_sentiment(review.comment, review.rating)

    if poi_uuid:
        # Check if user already reviewed
        user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
        stmt = select(Feedback).where(Feedback.user_id == user_uuid, Feedback.poi_id == poi_uuid)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="You have already reviewed this place.")

        fb = Feedback(
            user_id=user_uuid,
            poi_id=poi_uuid,
            rating=review.rating,
            comment=review.comment,
        )
        db.add(fb)
        await db.commit()
        await db.refresh(fb)
        review_id = str(fb.id)
    else:
        review_id = str(uuid.uuid4())

    return Envelope(success=True, data={
        "id": review_id,
        "sentiment_label": sentiment_result["sentiment_label"],
        "sentiment_score": sentiment_result["sentiment_score"],
        "sentiment_emoji": sentiment_result["sentiment_emoji"]
    })


@router.get("/reviews/{place_id}", response_model=Envelope[List[ReviewResponse]])
async def get_reviews(
    place_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    poi_uuid = None
    try:
        poi_uuid = uuid.UUID(place_id)
    except (ValueError, TypeError):
        return Envelope(success=True, data=[])

    stmt = (
        select(Feedback)
        .options(selectinload(Feedback.user))
        .where(Feedback.poi_id == poi_uuid)
        .order_by(Feedback.created_at.desc())
    )
    res = await db.execute(stmt)
    feedback_items = res.scalars().all()

    result = []
    for fb in feedback_items:
        analyzed = analyze_sentiment(fb.comment or "", fb.rating)
        user_name = fb.user.name if (fb.user and fb.user.name) else "Verified Tourist"
        result.append(ReviewResponse(
            id=str(fb.id),
            user_id=str(fb.user_id),
            place_id=place_id,
            rating=fb.rating,
            comment=fb.comment or "",
            sentiment_label=analyzed["sentiment_label"],
            sentiment_score=analyzed["sentiment_score"],
            sentiment_emoji=analyzed["sentiment_emoji"],
            created_at=fb.created_at.isoformat() if fb.created_at else "",
            user_name=user_name,
        ))

    return Envelope(success=True, data=result)


@router.get("/reviews/{place_id}/sentiment-summary", response_model=Envelope[dict])
async def get_review_sentiment_summary(
    place_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Computes overall tourist sentiment distribution using PostgreSQL Feedback records.
    """
    poi_uuid = None
    try:
        poi_uuid = uuid.UUID(place_id)
    except (ValueError, TypeError):
        return Envelope(success=True, data={
            "total_reviews": 0,
            "positive_pct": 100,
            "neutral_pct": 0,
            "negative_pct": 0,
            "overall_sentiment": "Positive",
            "overall_emoji": "😊"
        })

    stmt = select(Feedback).where(Feedback.poi_id == poi_uuid)
    res = await db.execute(stmt)
    feedback_items = res.scalars().all()

    if not feedback_items:
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

    for fb in feedback_items:
        analyzed = analyze_sentiment(fb.comment or "", fb.rating)
        label = analyzed["sentiment_label"]
        if label == "Positive":
            pos += 1
        elif label == "Negative":
            neg += 1
        else:
            neu += 1

    total = len(feedback_items)
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
