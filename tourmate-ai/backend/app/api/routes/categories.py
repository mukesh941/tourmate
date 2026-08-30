from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.api.deps import require_admin
from app.schemas.common import Envelope
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services.category_service import (
    get_all_categories, get_category, create_category, update_category, delete_category
)

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("", response_model=Envelope[List[CategoryResponse]])
async def read_categories():
    categories = await get_all_categories()
    return Envelope(success=True, data=categories)

@router.post("", response_model=Envelope[CategoryResponse], dependencies=[Depends(require_admin)])
async def add_category(payload: CategoryCreate):
    cat = await create_category(payload)
    return Envelope(success=True, data=cat)

@router.put("/{category_id}", response_model=Envelope[CategoryResponse], dependencies=[Depends(require_admin)])
async def edit_category(category_id: str, payload: CategoryUpdate):
    cat = await update_category(category_id, payload)
    if not cat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    return Envelope(success=True, data=cat)

@router.delete("/{category_id}", response_model=Envelope[bool], dependencies=[Depends(require_admin)])
async def remove_category(category_id: str):
    success = await delete_category(category_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    return Envelope(success=True, data=True)
