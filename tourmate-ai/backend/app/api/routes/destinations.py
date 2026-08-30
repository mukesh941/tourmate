from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.api.deps import require_admin
from app.schemas.common import Envelope
from app.schemas.destination import DestinationCreate, DestinationUpdate, DestinationResponse
from app.services.destination_service import (
    get_all_destinations, get_destination, create_destination, update_destination, delete_destination
)

router = APIRouter(prefix="/destinations", tags=["destinations"])

@router.get("", response_model=Envelope[List[DestinationResponse]])
async def read_destinations():
    destinations = await get_all_destinations()
    return Envelope(success=True, data=destinations)

@router.get("/{destination_id}", response_model=Envelope[DestinationResponse])
async def read_destination(destination_id: str):
    dest = await get_destination(destination_id)
    if not dest:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Destination not found")
    return Envelope(success=True, data=dest)

@router.post("", response_model=Envelope[DestinationResponse], dependencies=[Depends(require_admin)])
async def add_destination(payload: DestinationCreate):
    dest = await create_destination(payload)
    return Envelope(success=True, data=dest)

@router.put("/{destination_id}", response_model=Envelope[DestinationResponse], dependencies=[Depends(require_admin)])
async def edit_destination(destination_id: str, payload: DestinationUpdate):
    dest = await update_destination(destination_id, payload)
    if not dest:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Destination not found")
    return Envelope(success=True, data=dest)

@router.delete("/{destination_id}", response_model=Envelope[bool], dependencies=[Depends(require_admin)])
async def remove_destination(destination_id: str):
    success = await delete_destination(destination_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Destination not found")
    return Envelope(success=True, data=True)
