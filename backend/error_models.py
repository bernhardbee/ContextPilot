"""
Error response models for ContextPilot API.
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional


class ErrorDetail(BaseModel):
    """Detailed error information."""
    field: Optional[str] = None
    message: str
    

class ErrorResponse(BaseModel):
    """Standard error response format."""
    error_code: str
    message: str
    details: Dict[str, Any] = {}
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": {
                    "field": "content",
                    "constraint": "max_length"
                }
            }
        }
