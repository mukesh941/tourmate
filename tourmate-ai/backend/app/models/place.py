from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId

class GeoJSONPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float] # [longitude, latitude]

class FeatureScores(BaseModel):
    history: float = 0.0
    nature: float = 0.0
    culture: float = 0.0
    adventure: float = 0.0
    food: float = 0.0
    shopping: float = 0.0
    architecture: float = 0.0

class TouristPlaceInDB(BaseModel):
    destination_id: str
    name: str = Field(..., min_length=1)
    category_id: str
    description: str = Field(default="")
    history: str = Field(default="")
    cultural_significance: str = Field(default="")
    location: Optional[GeoJSONPoint] = None
    images: List[str] = Field(default_factory=list)
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    price_level: int = Field(default=1, ge=1, le=4)
    visit_duration_minutes: int = Field(default=60)
    feature_scores: FeatureScores = Field(default_factory=FeatureScores)
    nearby_place_ids: List[str] = Field(default_factory=list)
