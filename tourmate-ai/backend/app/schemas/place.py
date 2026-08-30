from typing import List, Optional
from pydantic import BaseModel, Field

class GeoJSONPointSchema(BaseModel):
    type: str = "Point"
    coordinates: List[float] # [longitude, latitude]

class FeatureScoresSchema(BaseModel):
    history: float = 0.0
    nature: float = 0.0
    culture: float = 0.0
    adventure: float = 0.0
    food: float = 0.0
    shopping: float = 0.0
    architecture: float = 0.0

class TouristPlaceCreate(BaseModel):
    destination_id: str
    name: str = Field(..., min_length=1)
    category_id: str
    description: str = Field(default="")
    history: str = Field(default="")
    cultural_significance: str = Field(default="")
    location: Optional[GeoJSONPointSchema] = None
    images: List[str] = Field(default_factory=list)
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    price_level: int = Field(default=1, ge=1, le=4)
    visit_duration_minutes: int = Field(default=60)
    feature_scores: FeatureScoresSchema = Field(default_factory=FeatureScoresSchema)
    nearby_place_ids: List[str] = Field(default_factory=list)

class TouristPlaceUpdate(BaseModel):
    destination_id: Optional[str] = None
    name: Optional[str] = None
    category_id: Optional[str] = None
    description: Optional[str] = None
    history: Optional[str] = None
    cultural_significance: Optional[str] = None
    location: Optional[GeoJSONPointSchema] = None
    images: Optional[List[str]] = None
    rating: Optional[float] = None
    price_level: Optional[int] = None
    visit_duration_minutes: Optional[int] = None
    feature_scores: Optional[FeatureScoresSchema] = None
    nearby_place_ids: Optional[List[str]] = None

class TouristPlaceResponse(TouristPlaceCreate):
    id: str
