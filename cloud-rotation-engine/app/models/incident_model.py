"""
Incident data models for persistence/tracking
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal


@dataclass
class IncidentRecord:
    """Represents a rotation incident record"""
    incident_id: str
    iam_user: str
    access_key_id: str
    risk_level: Literal["low", "medium", "high", "critical"]
    created_at: datetime
    rotated_at: Optional[datetime] = None
    new_key_id: Optional[str] = None
    policy_level: Optional[str] = None
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    error_message: Optional[str] = None
    rotation_time_ms: Optional[int] = None


@dataclass
class AccessKeyRecord:
    """Represents an access key record"""
    access_key_id: str
    iam_user: str
    created_date: datetime
    status: Literal["Active", "Inactive"]
    age_days: Optional[int] = None


@dataclass
class PolicyRecord:
    """Represents an IAM policy record"""
    policy_name: str
    policy_type: Literal["Managed", "Inline"]
    privilege_level: str
    risk_level: str
