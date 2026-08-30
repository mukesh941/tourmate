from typing import Optional
from pydantic import BaseModel, Field

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1)
    icon: str = Field(default="")

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None

class CategoryResponse(CategoryCreate):
    id: str
