from pydantic import BaseModel, Field

class DestinationInDB(BaseModel):
    name: str = Field(..., min_length=1)
    state: str = Field(default="")
    country: str = Field(default="")
    description: str = Field(default="")
    cover_image: str = Field(default="")
    popularity_score: float = Field(default=0.0)
    lat: float | None = None
    lng: float | None = None
