from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class OperationPayload(BaseModel):
    """Base payload model - operation-specific fields are validated in decision mapper"""
    leagueId: Optional[str] = None
    teamId: Optional[str] = None
    matchId: Optional[str] = None


class ProxyRequest(BaseModel):
    """Request model for /proxy/execute endpoint"""
    operationType: str = Field(..., description="Type of operation to execute")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Operation-specific payload")
