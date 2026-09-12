from typing import List, Optional
from pydantic import BaseModel, Field

class RoomType(BaseModel):
    id: str
    name: str = Field(..., min_length=1)
    price_per_night: float = Field(..., gt=0)
    capacity: int = Field(default=2, ge=1)
    bed_type: str = Field(default="1 King Bed")
    size: str = Field(default="400 sq ft")
    amenities: List[str] = Field(default_factory=list)
    image: Optional[str] = None
    description: Optional[str] = None

class HotelBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(...)
    city: str = Field(...)
    address: str = Field(...)
    destination_id: Optional[str] = None
    rating: float = Field(default=4.5, ge=1.0, le=5.0)
    review_count: int = Field(default=0)
    price_per_night_start: float = Field(..., gt=0)
    currency: str = Field(default="$")
    cover_image: str = Field(...)
    images: List[str] = Field(default_factory=list)
    amenities: List[str] = Field(default_factory=list)
    hotel_type: str = Field(default="Luxury Resort")  # Luxury Resort, Heritage Haveli, Boutique Hotel, Mountain Lodge, Beachfront Villa
    rooms: List[RoomType] = Field(default_factory=list)

class HotelCreate(HotelBase):
    pass

class HotelResponse(HotelBase):
    id: str

class HotelBookingCreate(BaseModel):
    hotel_id: str
    room_id: str
    room_name: str
    check_in_date: str  # YYYY-MM-DD
    check_out_date: str # YYYY-MM-DD
    guests: int = Field(default=2, ge=1)
    special_requests: Optional[str] = None

class HotelBookingResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_email: str
    hotel_id: str
    hotel_name: str
    hotel_city: str
    hotel_image: str
    room_name: str
    check_in_date: str
    check_out_date: str
    nights: int
    guests: int
    price_per_night: float
    total_price: float
    status: str
    special_requests: Optional[str] = None
    created_at: str
