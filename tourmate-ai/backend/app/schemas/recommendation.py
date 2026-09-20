"""
Recommendation schemas for Phase 3 Recommendation Engine.
Defines contracts for personalized feeds and day-clustered trip recommendations.
"""
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.schemas.place import GeoJSONPointSchema


class RecommendationPlanRequest(BaseModel):
    destination: Optional[str] = Field(
        default=None, max_length=128, description="Target city or destination name"
    )
    start_date: date = Field(
        ..., description="Calendar start date of the trip (YYYY-MM-DD)"
    )
    days: int = Field(default=2, ge=1, le=14, description="Number of trip days (1 to 14)")
    budget: Optional[str] = Field(
        default="moderate", description="Budget tier: budget, moderate, luxury"
    )
    interests: Optional[List[str]] = Field(
        default_factory=list,
        max_length=10,
        description="Canonical category names (max 10)",
    )
    max_candidates: Optional[int] = Field(
        default=15, ge=1, le=50, description="Max candidate POIs to rank (1 to 50)"
    )

    @field_validator("destination", mode="before")
    @classmethod
    def clean_destination(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    @field_validator("interests", mode="before")
    @classmethod
    def clean_interests(cls, v: Optional[List[str]]) -> List[str]:
        if not v:
            return []
        cleaned = [item.strip() for item in v if isinstance(item, str) and item.strip()]
        if len(cleaned) > 10:
            raise ValueError("A maximum of 10 interests may be specified.")
        return cleaned


class DayOpeningStatus(BaseModel):
    is_closed: bool
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    note: Optional[str] = None


class RecommendedPOIItem(BaseModel):
    id: str
    name: str
    description: str
    category_id: str
    category_name: Optional[str] = None
    location: Optional[GeoJSONPointSchema] = None
    images: List[str] = Field(default_factory=list)
    rating: float
    price_level: int
    visit_duration_minutes: int
    opening_status: Optional[DayOpeningStatus] = None


class DayCluster(BaseModel):
    day: int
    date: str
    day_of_week_name: str
    centroid: List[float] = Field(description="[latitude, longitude] centroid of the cluster")
    places: List[RecommendedPOIItem] = Field(default_factory=list)
    total_visit_duration_minutes: int = 0
    warnings: List[str] = Field(default_factory=list)


class RecommendationPlanResponse(BaseModel):
    destination: Optional[str] = None
    start_date: str
    total_days: int
    total_candidates: int
    clusters: List[DayCluster] = Field(default_factory=list)
    message: Optional[str] = None
