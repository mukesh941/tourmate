from typing import List, Optional
from pydantic import BaseModel, Field

class GeoJSONPointSchema(BaseModel):
    type: str = "Point"
    coordinates: List[float] # [longitude, latitude]

class RestaurantBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(default="")
    cuisine_type: List[str] = Field(default_factory=list)
    city: str = Field(...)
    address: str = Field(...)
    destination_id: Optional[str] = None
    location: Optional[GeoJSONPointSchema] = None
    rating: float = Field(default=4.5, ge=1.0, le=5.0)
    review_count: int = Field(default=0)
    price_level: int = Field(default=2, ge=1, le=4)
    popular_dishes: List[str] = Field(default_factory=list)
    opening_hours: str = Field(default="09:00 AM - 10:00 PM")
    cover_image: str = Field(default="")
    images: List[str] = Field(default_factory=list)

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cuisine_type: Optional[List[str]] = None
    city: Optional[str] = None
    address: Optional[str] = None
    destination_id: Optional[str] = None
    location: Optional[GeoJSONPointSchema] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    price_level: Optional[int] = None
    popular_dishes: Optional[List[str]] = None
    opening_hours: Optional[str] = None
    cover_image: Optional[str] = None
    images: Optional[List[str]] = None

class RestaurantResponse(RestaurantBase):
    id: str
