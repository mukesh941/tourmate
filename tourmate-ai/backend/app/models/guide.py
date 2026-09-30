from typing import List, Optional
from pydantic import BaseModel, Field

class GuideInDB(BaseModel):
    name: str = Field(..., min_length=1)
    languages: List[str] = Field(default_factory=list)
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    reviews_count: int = Field(default=0)
    hourly_rate: float = Field(default=0.0)
    bio: str = Field(default="")
    verified: bool = Field(default=False)
    image_url: Optional[str] = None
    location: str = Field(default="")
    is_demo: bool = Field(default=True)
    is_lgbtq: bool = Field(default=False)

class BookingInDB(BaseModel):
    user_id: str
    guide_id: str
    date: str
    hours: int
    total_price: float
    status: str = Field(default="pending") # pending, confirmed, cancelled
