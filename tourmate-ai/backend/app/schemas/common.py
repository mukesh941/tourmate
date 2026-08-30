"""
Consistent response envelope used by every endpoint, per §7 of the Phase 0 plan:
{ success, data, error }
"""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: str | None = None
