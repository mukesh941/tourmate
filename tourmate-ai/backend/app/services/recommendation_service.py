"""
Recommendation Service for TourMate AI (Phase 3).
Orchestrates:
1. Active user interests and preference retrieval.
2. Canonical SBERT query-text synthesis matching stored embedding convention.
3. 384-d normalized query vector generation via EmbeddingService.
4. PostgreSQL pgvector cosine KNN ranking with pre-filtering.
5. Spatial K-Means clustering with distinct coordinate safety.
6. Calendar-day dependent opening-hours validation (0=Sunday .. 6=Saturday).
7. Operational constraints checking (visit duration capacity).
"""
import uuid
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import anyio
import numpy as np
from sklearn.cluster import KMeans
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import AsyncSessionLocal
from app.models.sql.category import Category
from app.models.sql.location import Location
from app.models.sql.media import POIImage
from app.models.sql.poi import POI, OpeningHours
from app.models.sql.user import Preference, UserInterest
from app.schemas.place import GeoJSONPointSchema, TouristPlaceResponse
from app.schemas.recommendation import (
    DayCluster,
    DayOpeningStatus,
    RecommendationPlanRequest,
    RecommendationPlanResponse,
    RecommendedPOIItem,
)
from app.services.embedding_service import get_embedding
from app.services.poi_service import _format_poi_to_response

DAY_OF_WEEK_NAMES = [
    "Sunday",     # 0
    "Monday",     # 1
    "Tuesday",    # 2
    "Wednesday",  # 3
    "Thursday",   # 4
    "Friday",     # 5
    "Saturday",   # 6
]


def date_to_db_day_of_week(d: date) -> int:
    """
    Converts Python date.weekday() (0=Monday..6=Sunday) to
    database opening_hours convention (0=Sunday, 1=Monday..6=Saturday).
    """
    return (d.weekday() + 1) % 7


def construct_poi_embedding_text(name: str, category_name: str, description: str) -> str:
    """
    Canonical text-construction format used for POI embeddings in Phase 2.
    Format: "{name} {category_name} {description}"
    """
    parts = [name.strip(), category_name.strip(), (description or "").strip()]
    return " ".join(p for p in parts if p)


def construct_recommendation_query_text(
    destination: Optional[str] = None,
    interests: Optional[List[str]] = None,
    travel_style: Optional[str] = None,
    weights: Optional[Dict[str, float]] = None,
) -> str:
    """
    Constructs a deterministic query text adhering to the same semantic token
    conventions as stored POI embeddings:
    {destination} {weighted_interest_tokens} {travel_style_or_keywords}
    """
    tokens: List[str] = []

    if destination and destination.strip():
        tokens.append(destination.strip())

    if interests:
        weights = weights or {}
        for item in interests:
            clean_item = item.strip()
            if not clean_item:
                continue
            weight = weights.get(clean_item, 1.0)
            repeat_count = max(1, min(int(round(weight)), 3))
            for _ in range(repeat_count):
                tokens.append(clean_item)

    if travel_style and travel_style.strip():
        tokens.append(travel_style.strip())

    # Fallback to general tourism terms if query tokens are empty
    if not tokens:
        tokens = ["tourism", "sightseeing", "historical", "monuments", "culture", "architecture", "nature"]

    return " ".join(tokens)


def _sync_kmeans(coords: List[List[float]], k: int) -> Tuple[List[int], List[List[float]]]:
    """Runs scikit-learn KMeans deterministically."""
    X = np.array(coords)
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X).tolist()
    centroids = kmeans.cluster_centers_.tolist()
    return labels, centroids


async def get_personalized_recommendations(
    user_id: Optional[str] = None,
    destination: Optional[str] = None,
    limit: int = 10,
    db: Optional[AsyncSession] = None,
) -> List[TouristPlaceResponse]:
    """
    Primary recommendation ranking for GET /api/places/recommendations.
    Uses authenticated user interests from PostgreSQL, builds an SBERT query vector,
    and runs indexed pgvector cosine KNN ranking.
    """
    if db is None:
        async with AsyncSessionLocal() as session:
            return await get_personalized_recommendations(user_id, destination, limit, session)

    limit = max(1, min(limit, 50))
    interests: List[str] = []
    weights: Dict[str, float] = {}
    travel_style: Optional[str] = None

    if user_id:
        try:
            uid = uuid.UUID(str(user_id))
            # Retrieve user interests
            ui_stmt = (
                select(Category.name, UserInterest.weight)
                .join(UserInterest, UserInterest.category_id == Category.id)
                .where(UserInterest.user_id == uid)
            )
            ui_rows = (await db.execute(ui_stmt)).all()
            for cat_name, weight in ui_rows:
                interests.append(cat_name)
                weights[cat_name] = float(weight)

            # Retrieve travel style from preferences
            pref_stmt = select(Preference.travel_style).where(Preference.user_id == uid)
            pref_style = (await db.execute(pref_stmt)).scalar_one_or_none()
            if pref_style:
                travel_style = pref_style
        except Exception:
            interests = []

    # Construct query string and generate 384-d normalized vector
    query_text = construct_recommendation_query_text(
        destination=destination,
        interests=interests,
        travel_style=travel_style,
        weights=weights,
    )
    query_vector = await anyio.to_thread.run_sync(get_embedding, query_text)

    # pgvector cosine KNN query
    stmt = (
        select(POI)
        .join(POI.location)
        .join(POI.category)
        .options(
            selectinload(POI.location),
            selectinload(POI.category),
            selectinload(POI.poi_images).selectinload(POIImage.image),
        )
        .where(
            POI.is_active.is_(True),
            POI.embedding.is_not(None),
        )
    )

    if destination and destination.strip():
        dest_term = f"%{destination.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Location.city).like(dest_term),
                func.lower(Location.state).like(dest_term),
                func.lower(Location.name).like(dest_term),
            )
        )

    stmt = stmt.order_by(POI.embedding.cosine_distance(query_vector)).limit(limit)

    result = await db.execute(stmt)
    pois = result.scalars().all()

    return [_format_poi_to_response(poi) for poi in pois]


async def plan_trip_recommendations(
    payload: RecommendationPlanRequest,
    user_id: Optional[str] = None,
    db: Optional[AsyncSession] = None,
) -> RecommendationPlanResponse:
    """
    Clustered trip recommendation engine for POST /api/places/recommendations/plan.
    Pipeline:
    1. Resolve active user interests (explicit payload or stored profile).
    2. Build canonical query text & generate 384-d normalized query vector.
    3. Apply candidate pre-filters (active, budget tier, city).
    4. Run PostgreSQL pgvector cosine KNN for Top-N candidates.
    5. Execute spatial K-Means with distinct coordinate safety.
    6. Validate calendar-day dependent opening hours and daily visit durations.
    7. Return structured DayCluster itinerary schedule.
    """
    if db is None:
        async with AsyncSessionLocal() as session:
            return await plan_trip_recommendations(payload, user_id, session)

    requested_days = payload.days
    start_date = payload.start_date
    max_candidates = max(1, min(payload.max_candidates or 15, 50))

    # 1. Resolve interests & travel preferences
    raw_interests = [i.strip() for i in (payload.interests or []) if i.strip()]
    interests: List[str] = []
    weights: Dict[str, float] = {}
    travel_style: Optional[str] = None

    if raw_interests:
        cat_stmt = select(Category.name)
        canonical_rows = (await db.execute(cat_stmt)).scalars().all()
        canonical_map = {c.lower(): c for c in canonical_rows}
        for ri in raw_interests:
            lowered = ri.lower()
            if lowered not in canonical_map:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=400,
                    detail=f"Interest '{ri}' does not match any canonical category. Canonical categories: {list(canonical_map.values())}",
                )
            interests.append(canonical_map[lowered])
    elif user_id:
        try:
            uid = uuid.UUID(str(user_id))
            ui_stmt = (
                select(Category.name, UserInterest.weight)
                .join(UserInterest, UserInterest.category_id == Category.id)
                .where(UserInterest.user_id == uid)
            )
            for cat_name, weight in (await db.execute(ui_stmt)).all():
                interests.append(cat_name)
                weights[cat_name] = float(weight)

            pref_stmt = select(Preference.travel_style).where(Preference.user_id == uid)
            travel_style = (await db.execute(pref_stmt)).scalar_one_or_none()
        except Exception:
            interests = []

    # 2. Construct canonical query text and generate embedding
    query_text = construct_recommendation_query_text(
        destination=payload.destination,
        interests=interests,
        travel_style=travel_style,
        weights=weights,
    )
    query_vector = await anyio.to_thread.run_sync(get_embedding, query_text)

    # 3. Pre-filters & pgvector KNN query
    stmt = (
        select(POI)
        .join(POI.location)
        .join(POI.category)
        .options(
            selectinload(POI.location),
            selectinload(POI.category),
            selectinload(POI.opening_hours),
            selectinload(POI.poi_images).selectinload(POIImage.image),
        )
        .where(
            POI.is_active.is_(True),
            POI.embedding.is_not(None),
        )
    )

    # Destination filter
    if payload.destination and payload.destination.strip():
        dest_term = f"%{payload.destination.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Location.city).like(dest_term),
                func.lower(Location.state).like(dest_term),
                func.lower(Location.name).like(dest_term),
            )
        )

    # Budget filter
    budget_tier_str = (payload.budget or "moderate").strip().lower()
    max_price_tier = 2 if budget_tier_str == "budget" else (3 if budget_tier_str == "moderate" else 4)
    stmt = stmt.where(POI.price_tier <= max_price_tier)

    # Order by pgvector cosine distance
    stmt = stmt.order_by(POI.embedding.cosine_distance(query_vector)).limit(max_candidates)

    res = await db.execute(stmt)
    candidate_pois = res.scalars().all()
    candidate_count = len(candidate_pois)

    # Edge Case: Zero candidates
    if candidate_count == 0:
        return RecommendationPlanResponse(
            destination=payload.destination,
            start_date=start_date.isoformat(),
            total_days=requested_days,
            total_candidates=0,
            clusters=[],
            message="No attractions matched the requested criteria in this destination.",
        )

    # 4. K-Means Distinct Coordinate Safety
    # Extract coordinates [lat, lng]
    coords: List[List[float]] = []
    valid_candidates: List[POI] = []
    for p in candidate_pois:
        if p.location and p.location.latitude is not None and p.location.longitude is not None:
            coords.append([float(p.location.latitude), float(p.location.longitude)])
            valid_candidates.append(p)

    valid_candidate_count = len(valid_candidates)
    if valid_candidate_count == 0:
        return RecommendationPlanResponse(
            destination=payload.destination,
            start_date=start_date.isoformat(),
            total_days=requested_days,
            total_candidates=0,
            clusters=[],
            message="Candidates had no valid geographical coordinates.",
        )

    distinct_coords_count = len({(round(lat, 5), round(lng, 5)) for lat, lng in coords})

    # Effective K strictly satisfies:
    # effective_k = min(requested_days, valid_candidate_count, distinct_coords_count)
    effective_k = min(requested_days, valid_candidate_count, distinct_coords_count)

    clusters_dict: Dict[int, List[POI]] = {i: [] for i in range(effective_k)}
    centroids_dict: Dict[int, List[float]] = {}

    if effective_k <= 1:
        # Bypass KMeans entirely
        clusters_dict[0] = valid_candidates
        mean_lat = float(np.mean([c[0] for c in coords]))
        mean_lng = float(np.mean([c[1] for c in coords]))
        centroids_dict[0] = [round(mean_lat, 5), round(mean_lng, 5)]
    elif valid_candidate_count == effective_k:
        # Exactly 1 candidate per day
        for i, p in enumerate(valid_candidates):
            clusters_dict[i] = [p]
            centroids_dict[i] = [float(p.location.latitude), float(p.location.longitude)]
    else:
        # Run deterministic KMeans
        labels, centroids = await anyio.to_thread.run_sync(_sync_kmeans, coords, effective_k)
        for p, label in zip(valid_candidates, labels):
            clusters_dict[label].append(p)
        for i, c in enumerate(centroids):
            centroids_dict[i] = [round(c[0], 5), round(c[1], 5)]

    # Sort clusters deterministically by centroid latitude & longitude for geographic continuity
    sorted_cluster_ids = sorted(
        range(effective_k),
        key=lambda cid: (centroids_dict[cid][0], centroids_dict[cid][1]),
    )

    # 5. Build DayClusters with Calendar-Day Opening Hours & Duration Checks
    day_clusters: List[DayCluster] = []

    for day_idx in range(requested_days):
        current_date = start_date + timedelta(days=day_idx)
        db_day_of_week = date_to_db_day_of_week(current_date)
        day_name = DAY_OF_WEEK_NAMES[db_day_of_week]

        if day_idx < effective_k:
            original_cid = sorted_cluster_ids[day_idx]
            pois_in_day = clusters_dict[original_cid]
            centroid = centroids_dict[original_cid]
            # Order POIs within day by rating descending, name ascending
            pois_in_day.sort(key=lambda x: (-float(x.rating), x.name))
        else:
            # When requested_days > effective_k
            pois_in_day = []
            centroid = centroids_dict[sorted_cluster_ids[0]] if centroids_dict else [0.0, 0.0]

        day_places: List[RecommendedPOIItem] = []
        day_warnings: List[str] = []
        total_duration = 0

        for poi in pois_in_day:
            # Check opening hours for current_date's day of week
            opening_status = None
            if poi.opening_hours:
                for oh in poi.opening_hours:
                    if oh.day_of_week == db_day_of_week:
                        opening_status = DayOpeningStatus(
                            is_closed=bool(oh.is_closed),
                            open_time=oh.open_time.strftime("%H:%M") if oh.open_time else None,
                            close_time=oh.close_time.strftime("%H:%M") if oh.close_time else None,
                            note="Closed on this day" if oh.is_closed else "Open today",
                        )
                        if oh.is_closed:
                            day_warnings.append(
                                f"{poi.name} is closed on {day_name} ({current_date.isoformat()}). Consider visiting on another day."
                            )
                        break

            # Collect primary image
            img_urls = [
                pi.image.url
                for pi in sorted(poi.poi_images, key=lambda x: (not x.is_primary, x.display_order))
                if pi.image and pi.image.url
            ]

            duration = int(poi.typical_visit_duration_minutes)
            total_duration += duration

            location_schema = None
            if poi.location:
                location_schema = GeoJSONPointSchema(
                    type="Point",
                    coordinates=[float(poi.location.longitude), float(poi.location.latitude)],
                )

            day_places.append(
                RecommendedPOIItem(
                    id=str(poi.id),
                    name=poi.name,
                    description=poi.description or "",
                    category_id=str(poi.category_id),
                    category_name=poi.category.name if poi.category else None,
                    location=location_schema,
                    images=img_urls,
                    rating=float(poi.rating),
                    price_level=int(poi.price_tier),
                    visit_duration_minutes=duration,
                    opening_status=opening_status,
                )
            )

        if total_duration > 600:
            day_warnings.append(
                f"High activity load: {total_duration} minutes of sightseeing scheduled for Day {day_idx + 1}."
            )

        if day_idx >= effective_k:
            day_warnings.append(
                "No remaining distinct attractions available to schedule for this day."
            )

        day_clusters.append(
            DayCluster(
                day=day_idx + 1,
                date=current_date.isoformat(),
                day_of_week_name=day_name,
                centroid=centroid,
                places=day_places,
                total_visit_duration_minutes=total_duration,
                warnings=day_warnings,
            )
        )

    return RecommendationPlanResponse(
        destination=payload.destination,
        start_date=start_date.isoformat(),
        total_days=requested_days,
        total_candidates=valid_candidate_count,
        clusters=day_clusters,
        message=None,
    )
