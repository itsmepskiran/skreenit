from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class ErrorResponse(BaseModel):
    ok: bool = False
    error: dict

class StandardResponse(BaseModel, Generic[T]):
    ok: bool = True
    data: Optional[T] = None

class ScoreCard(BaseModel):
    communication: int
    appearance: int
    attitude: int
    behaviour: int
    confidence: int
    total: int
