from pydantic import BaseModel, Field

class CategoryInDB(BaseModel):
    name: str = Field(..., min_length=1)
    icon: str = Field(default="")
