"""
Incident data model for audit logging
"""
from typing import Optional


class IncidentRecord:
    """Data model for rotation incident tracking"""
    
    def __init__(
        self,
        incident_id: str,
        iam_user: str,
        access_key_id: str,
        risk_level: str,
        rotation_status: str,
        policy_level: str,
        timestamp: str,  # Changed from datetime to string
        rotation_time_ms: Optional[int] = None,
        old_key_deactivated: bool = False,
        new_key_id: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        self.incident_id = incident_id
        self.iam_user = iam_user
        self.access_key_id = access_key_id
        self.risk_level = risk_level
        self.rotation_status = rotation_status
        self.policy_level = policy_level
        self.timestamp = timestamp
        self.rotation_time_ms = rotation_time_ms
        self.old_key_deactivated = old_key_deactivated
        self.new_key_id = new_key_id
        self.error_message = error_message
    
    def to_dict(self) -> dict:
        """Convert incident record to dictionary"""
        return {
            "incident_id": self.incident_id,
            "iam_user": self.iam_user,
            "access_key_id": self.access_key_id,
            "risk_level": self.risk_level,
            "rotation_status": self.rotation_status,
            "policy_level": self.policy_level,
            "timestamp": self.timestamp,
            "rotation_time_ms": self.rotation_time_ms,
            "old_key_deactivated": self.old_key_deactivated,
            "new_key_id": self.new_key_id,
            "error_message": self.error_message
        }
