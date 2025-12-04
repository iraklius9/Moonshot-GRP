from typing import Any, Optional
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    details: Optional[dict] = None
    requestId: Optional[str] = None


class ProxyResponse(BaseModel):
    """Normalized response model"""
    success: bool
    data: Any
    requestId: Optional[str] = None
