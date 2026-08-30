from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ItineraryInDB(BaseModel):
    user_id: str
    title: str = Field(..., min_length=1)
    days: int = Field(..., ge=1, le=14)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    schedule: List[dict] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
