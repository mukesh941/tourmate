from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional

class FavoriteInDB(BaseModel):
    user_id: str
    place_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ReviewInDB(BaseModel):
    user_id: str
    place_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., max_length=1000)
    sentiment_label: Optional[str] = "Positive"  # Positive, Neutral, Negative
    sentiment_score: Optional[float] = 0.85      # Confidence 0.0 - 1.0
    sentiment_emoji: Optional[str] = "😊"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ReviewResponse(BaseModel):
    id: str
    user_id: str
    place_id: str
    rating: int
    comment: str
    sentiment_label: Optional[str] = "Positive"
    sentiment_score: Optional[float] = 0.85
    sentiment_emoji: Optional[str] = "😊"
    created_at: datetime
    user_name: str = "" # Populated from user record
