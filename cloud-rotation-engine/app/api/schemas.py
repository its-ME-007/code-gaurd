"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional
import datetime

class RotationRequest(BaseModel):
    """Schema for key rotation request"""
    iam_user: str = Field(..., description="IAM username")
    access_key_id: str = Field(..., description="Access key ID to rotate")
    incident_id: str = Field(..., description="Unique incident identifier")
    risk_level: str = Field(..., description="Risk level: critical/high/medium/low")

    class Config:
        json_schema_extra = {
            "example": {
                "iam_user": "dev-user",
                "access_key_id": "AKIA...",
                "incident_id": "550e8400-e29b-41d4-a716-446655440000",
                "risk_level": "critical"
            }
        }


class RotationResponse(BaseModel):
    """Schema for successful key rotation response"""
    status: str = Field(..., description="success or error")
    rotation_completed: bool = Field(..., description="Whether rotation was completed")
    iam_user: str = Field(..., description="IAM username")
    old_key_deactivated: Optional[bool] = Field(None, description="Whether old key was deactivated")
    new_key_id: Optional[str] = Field(None, description="New access key ID (masked)")
    policy_level: str = Field(..., description="Detected policy privilege level")
    rotation_time_ms: Optional[int] = Field(None, description="Time taken for rotation in milliseconds")
    incident_id: Optional[str] = Field(None, description="Incident ID")
    risk_level: Optional[str] = Field(None, description="Risk level")
    mode: Optional[str] = Field(None, description="DRY_RUN or production mode")
    old_key: Optional[str] = Field(None, description="Masked old key in dry run")
    message: Optional[str] = Field(None, description="Additional message")
    reason: Optional[str] = Field(None, description="Error reason if failed")


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    status: str = Field("error", description="Error status")
    reason: str = Field(..., description="Error reason")
    rotation_completed: bool = Field(False, description="Rotation was not completed")
    details: Optional[str] = Field(None, description="Additional error details")


# class RotationAuditLog(BaseModel):
#     """Schema for audit log entry"""
#     incident_id: str
#     old_key: str
#     new_key: str
#     rotation_timestamp: datetime
#     iam_user: str
#     policy_level: str
#     rotation_time_ms: int
#     status: str


# class AuditLogResponse(BaseModel):
#     incident_id: str
#     status: str
#     message: str


class KeyAnalysisResponse(BaseModel):
    iam_user: str
    status: str
    message: str
