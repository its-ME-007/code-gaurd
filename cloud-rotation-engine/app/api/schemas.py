"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal


class RotationRequest(BaseModel):
    """Schema for key rotation request"""
    iam_user: str = Field(..., description="Target IAM user")
    access_key_id: str = Field(..., description="AWS Access Key ID to rotate")
    incident_id: str = Field(..., description="Incident ID for audit trail")
    risk_level: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Risk level classification"
    )

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
    status: str = Field("success", description="Operation status")
    rotation_completed: bool = Field(..., description="Whether rotation completed")
    iam_user: str = Field(..., description="IAM user affected")
    old_key_deactivated: bool = Field(..., description="Old key deactivation status")
    new_key_id: str = Field(..., description="New Access Key ID")
    policy_level: str = Field(..., description="IAM privilege level")
    rotation_time_ms: int = Field(..., description="Time taken in milliseconds")


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    status: str = Field("error", description="Error status")
    reason: str = Field(..., description="Error reason")
    rotation_completed: bool = Field(False, description="Rotation was not completed")
    details: Optional[str] = Field(None, description="Additional error details")


class RotationAuditLog(BaseModel):
    """Schema for audit log entry"""
    incident_id: str
    old_key: str
    new_key: str
    rotation_timestamp: datetime
    iam_user: str
    policy_level: str
    rotation_time_ms: int
    status: str
