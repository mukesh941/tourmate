import uuid
from datetime import date
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_dependency
from app.core.db import get_async_db
from app.schemas.auth import UserPublic
from app.models.sql.interaction import Feedback, Offer
from app.models.sql.user import User
from app.models.sql.poi import POI
from app.models.sql.trip import Trip
from app.models.sql.itinerary import Itinerary
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
    rating: int = Field(..., ge=1, le=5, description="Rating between 1 and 5")
    comment: str = Field(..., min_length=1, max_length=2000, description="Tourist feedback comment")
    trip_id: Optional[str] = None
    itinerary_id: Optional[str] = None


class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating between 1 and 5")
    comment: str = Field(..., min_length=1, max_length=2000, description="Tourist feedback comment")
    poi_id: Optional[str] = None
    trip_id: Optional[str] = None
    itinerary_id: Optional[str] = None


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
        user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
        stmt = select(Feedback).where(Feedback.user_id == user_uuid, Feedback.poi_id == poi_uuid)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="You have already reviewed this place.")

        trip_uuid = None
        if review.trip_id:
            try:
                trip_uuid = uuid.UUID(review.trip_id)
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="Invalid trip_id format.")

        itin_uuid = None
        if review.itinerary_id:
            try:
                itin_uuid = uuid.UUID(review.itinerary_id)
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="Invalid itinerary_id format.")

        fb = Feedback(
            user_id=user_uuid,
            poi_id=poi_uuid,
            trip_id=trip_uuid,
            itinerary_id=itin_uuid,
            rating=review.rating,
            comment=review.comment.strip(),
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


@router.post("/feedback", response_model=Envelope[dict])
async def submit_feedback(
    feedback: FeedbackCreate,
    current_user: UserPublic = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Submits structured feedback associated with a user and optional POI, Trip, or Itinerary.
    Enforces check constraint ck_feedback_target_not_null.
    """
    if not feedback.poi_id and not feedback.trip_id and not feedback.itinerary_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback must reference at least one target: poi_id, trip_id, or itinerary_id.",
        )

    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))

    poi_uuid = None
    if feedback.poi_id:
        try:
            poi_uuid = uuid.UUID(feedback.poi_id)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid poi_id format.")

    trip_uuid = None
    if feedback.trip_id:
        try:
            trip_uuid = uuid.UUID(feedback.trip_id)
            t_res = await db.execute(select(Trip).where(Trip.id == trip_uuid, Trip.user_id == user_uuid))
            if not t_res.scalar_one_or_none():
                raise HTTPException(status_code=403, detail="Not authorized to submit feedback for this trip.")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid trip_id format.")

    itin_uuid = None
    if feedback.itinerary_id:
        try:
            itin_uuid = uuid.UUID(feedback.itinerary_id)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid itinerary_id format.")

    sentiment_result = analyze_sentiment(feedback.comment, feedback.rating)

    fb = Feedback(
        user_id=user_uuid,
        poi_id=poi_uuid,
        trip_id=trip_uuid,
        itinerary_id=itin_uuid,
        rating=feedback.rating,
        comment=feedback.comment.strip(),
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)

    return Envelope(success=True, data={
        "id": str(fb.id),
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


class OfferResponse(BaseModel):
    id: str
    location_id: str
    poi_id: Optional[str] = None
    accommodation_id: Optional[str] = None
    title: str
    description: str
    discount_percentage: Optional[float] = None
    promo_code: Optional[str] = None
    affiliate_url: Optional[str] = None
    valid_from: str
    valid_until: str
    is_active: bool


@router.get("/offers", response_model=Envelope[List[OfferResponse]])
async def get_active_offers(
    location_id: Optional[str] = Query(None, description="Filter offers by location ID"),
    poi_id: Optional[str] = Query(None, description="Filter offers by POI ID"),
    accommodation_id: Optional[str] = Query(None, description="Filter offers by accommodation ID"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Returns only verified, active commercial affiliate offers whose validity window is current.
    Excludes expired offers and validates affiliate URLs.
    """
    today = date.today()
    conditions = [
        Offer.is_active == True,
        Offer.valid_from <= today,
        Offer.valid_until >= today,
    ]

    if location_id:
        try:
            conditions.append(Offer.location_id == uuid.UUID(location_id))
        except (ValueError, TypeError):
            return Envelope(success=True, data=[])

    if poi_id:
        try:
            conditions.append(Offer.poi_id == uuid.UUID(poi_id))
        except (ValueError, TypeError):
            return Envelope(success=True, data=[])

    if accommodation_id:
        try:
            conditions.append(Offer.accommodation_id == uuid.UUID(accommodation_id))
        except (ValueError, TypeError):
            return Envelope(success=True, data=[])

    stmt = select(Offer).where(and_(*conditions)).order_by(Offer.created_at.desc())
    res = await db.execute(stmt)
    offers = res.scalars().all()

    results = []
    for off in offers:
        # Sanitize affiliate url: must be http or https
        safe_url = off.affiliate_url
        if safe_url and not (safe_url.startswith("http://") or safe_url.startswith("https://")):
            safe_url = None

        results.append(OfferResponse(
            id=str(off.id),
            location_id=str(off.location_id),
            poi_id=str(off.poi_id) if off.poi_id else None,
            accommodation_id=str(off.accommodation_id) if off.accommodation_id else None,
            title=off.title,
            description=off.description or "",
            discount_percentage=float(off.discount_percentage) if off.discount_percentage is not None else None,
            promo_code=off.promo_code,
            affiliate_url=safe_url,
            valid_from=off.valid_from.isoformat(),
            valid_until=off.valid_until.isoformat(),
            is_active=off.is_active,
        ))

    return Envelope(success=True, data=results)

