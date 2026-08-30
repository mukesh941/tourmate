from typing import Optional
from pydantic import BaseModel, Field

class DestinationCreate(BaseModel):
    name: str = Field(..., min_length=1)
    state: str = Field(default="")
    country: str = Field(default="")
    description: str = Field(default="")
    cover_image: str = Field(default="")
    popularity_score: float = Field(default=0.0)

class DestinationUpdate(BaseModel):
    name: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    popularity_score: Optional[float] = None

class DestinationResponse(DestinationCreate):
    id: str
