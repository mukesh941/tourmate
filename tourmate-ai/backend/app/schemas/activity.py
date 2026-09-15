from typing import List, Optional
from pydantic import BaseModel, Field

class GeoJSONPointSchema(BaseModel):
    type: str = "Point"
    coordinates: List[float] # [longitude, latitude]

class ActivityBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(default="")
    activity_type: str = Field(...) # e.g., Trekking, Boating
    city: str = Field(...)
    address: str = Field(default="")
    destination_id: Optional[str] = None
    location: Optional[GeoJSONPointSchema] = None
    rating: float = Field(default=4.5, ge=1.0, le=5.0)
    review_count: int = Field(default=0)
    price: float = Field(default=0.0)
    currency: str = Field(default="$")
    duration: str = Field(default="2 hours")
    difficulty_level: str = Field(default="Easy")
    cover_image: str = Field(default="")
    images: List[str] = Field(default_factory=list)

class ActivityCreate(ActivityBase):
    pass

class ActivityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    activity_type: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    destination_id: Optional[str] = None
    location: Optional[GeoJSONPointSchema] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    duration: Optional[str] = None
    difficulty_level: Optional[str] = None
    cover_image: Optional[str] = None
    images: Optional[List[str]] = None

class ActivityResponse(ActivityBase):
    id: str
