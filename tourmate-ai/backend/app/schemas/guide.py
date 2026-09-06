from typing import List, Optional
from pydantic import BaseModel, Field

class GuideCreate(BaseModel):
    name: str = Field(..., min_length=1)
    languages: List[str] = Field(default_factory=list)
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    reviews_count: int = Field(default=0)
    hourly_rate: float = Field(default=0.0)
    bio: str = Field(default="")
    verified: bool = Field(default=False)
    image_url: Optional[str] = None
    location: str = Field(default="")

class GuideResponse(GuideCreate):
    id: str

class BookingCreate(BaseModel):
    guide_id: str
    date: str
    hours: int

class BookingResponse(BaseModel):
    id: str
    user_id: str
    guide_id: str
    date: str
    hours: int
    total_price: float
    status: str
    guide: Optional[GuideResponse] = None
