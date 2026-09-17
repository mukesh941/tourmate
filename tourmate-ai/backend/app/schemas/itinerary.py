from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ActivitySchema(BaseModel):
    start_time: str
    end_time: str
    place_id: Optional[str] = None
    name: str
    description: str
    activity_type: Optional[str] = None
    estimated_cost: Optional[int] = 0
    travel_time_minutes: Optional[int] = 0
    image: Optional[str] = None
    rating: Optional[float] = None
    reviewCount: Optional[int] = None
    location: Optional[str] = None
    distance: Optional[str] = None
    openingHours: Optional[str] = None
    entryFee: Optional[str] = None
    aiReason: Optional[str] = None
    aiTips: Optional[List[str]] = Field(default_factory=list)
    crowdLevel: Optional[str] = None
    weatherSuitability: Optional[str] = None
    bookingUrl: Optional[str] = None
    isOptional: Optional[bool] = False
    isCompleted: Optional[bool] = False

class DayScheduleSchema(BaseModel):
    day: int
    aiSummary: Optional[str] = None
    activities: List[ActivitySchema]

class TransportationSummarySchema(BaseModel):
    mode: str
    origin: str
    destination: str
    estimated_distance_km: Optional[float] = None
    estimated_duration_minutes: int
    estimated_cost_min: int
    estimated_cost_max: int
    fuel_cost_estimate: Optional[int] = None
    toll_estimate: Optional[int] = None
    recommendation_note: Optional[str] = None

class ItineraryCreate(BaseModel):
    title: str = Field(..., min_length=1)
    days: int = Field(..., ge=1, le=14)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    schedule: List[DayScheduleSchema] = Field(default_factory=list)
    transportation: Optional[TransportationSummarySchema] = None

class ItineraryUpdate(BaseModel):
    title: Optional[str] = None
    days: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    schedule: Optional[List[DayScheduleSchema]] = None
    transportation: Optional[TransportationSummarySchema] = None

class ItineraryResponse(ItineraryCreate):
    id: str
    user_id: str
    created_at: datetime

class ItineraryGenerateRequest(BaseModel):
    origin: Optional[str] = Field(default="")
    destination_name: str = Field(default="")
    place_ids: List[str] = Field(default_factory=list)
    days: int = Field(..., ge=1, le=7)
    start_time: str = Field(default="09:00")
    end_time: str = Field(default="20:00")
    accommodation: Optional[str] = Field(default=None)
    energy_level: str = Field(default="Moderate")
    budget: str = Field(default="Medium")
    travel_type: str = Field(default="Family")
    transportation_mode: str = Field(default="flight")
    local_transportation: str = Field(default="taxi")
    interests: List[str] = Field(default_factory=list)
