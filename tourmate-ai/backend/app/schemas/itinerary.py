from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ActivitySchema(BaseModel):
    time: str
    place_id: Optional[str] = None
    name: str
    description: str

class DayScheduleSchema(BaseModel):
    day: int
    activities: List[ActivitySchema]

class ItineraryCreate(BaseModel):
    title: str = Field(..., min_length=1)
    days: int = Field(..., ge=1, le=14)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    schedule: List[DayScheduleSchema] = Field(default_factory=list)

class ItineraryUpdate(BaseModel):
    title: Optional[str] = None
    days: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    schedule: Optional[List[DayScheduleSchema]] = None

class ItineraryResponse(ItineraryCreate):
    id: str
    user_id: str
    created_at: datetime

class ItineraryGenerateRequest(BaseModel):
    destination_name: str = Field(default="")
    place_ids: List[str] = Field(default_factory=list)
    days: int = Field(..., ge=1, le=7)
    start_time: str = Field(default="09:00")
    end_time: str = Field(default="20:00")
    accommodation: Optional[str] = Field(default=None)
    energy_level: str = Field(default="Moderate")
