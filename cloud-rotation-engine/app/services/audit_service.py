"""
Audit logging service for tracking rotation incidents
"""
from typing import Dict, List, Optional
from datetime import datetime
from app.models.incident_model import IncidentRecord


class AuditService:
    """In-memory audit log storage (replace with database in production)"""
    
    def __init__(self):
        self.audit_logs: Dict[str, IncidentRecord] = {}
    
    def log_incident(self, incident_data: dict) -> bool:
        """Log a rotation incident"""
        try:
            # Convert datetime to ISO string if needed
            timestamp = incident_data.get("timestamp")
            if isinstance(timestamp, datetime):
                timestamp = timestamp.isoformat()
            elif not timestamp:
                timestamp = datetime.utcnow().isoformat()
            
            incident = IncidentRecord(
                incident_id=incident_data.get("incident_id"),
                iam_user=incident_data.get("iam_user"),
                access_key_id=incident_data.get("access_key_id"),
                risk_level=incident_data.get("risk_level"),
                rotation_status=incident_data.get("rotation_status", "pending"),
                policy_level=incident_data.get("policy_level", "Unknown"),
                timestamp=timestamp,
                rotation_time_ms=incident_data.get("rotation_time_ms"),
                old_key_deactivated=incident_data.get("old_key_deactivated", False),
                new_key_id=incident_data.get("new_key_id"),
                error_message=incident_data.get("error_message")
            )
            
            self.audit_logs[incident.incident_id] = incident
            print(f"📝 Audit log saved for incident: {incident.incident_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to log incident: {str(e)}")
            return False
    
    def get_incident(self, incident_id: str) -> Optional[dict]:
        """Retrieve audit log by incident ID"""
        incident = self.audit_logs.get(incident_id)
        if incident:
            return incident.to_dict()
        return None
    
    def get_all_incidents(self) -> List[dict]:
        """Get all audit logs"""
        return [incident.to_dict() for incident in self.audit_logs.values()]
    
    def get_user_incidents(self, iam_user: str) -> List[dict]:
        """Get all incidents for a specific IAM user"""
        return [
            incident.to_dict() 
            for incident in self.audit_logs.values() 
            if incident.iam_user == iam_user
        ]
    
    def get_incidents_by_status(self, status: str) -> List[dict]:
        """Get incidents filtered by rotation status"""
        return [
            incident.to_dict() 
            for incident in self.audit_logs.values() 
            if incident.rotation_status == status
        ]
