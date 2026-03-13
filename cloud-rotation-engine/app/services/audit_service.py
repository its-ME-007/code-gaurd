"""
Audit logging service for tracking rotation incidents and secret storage operations
SQLite-backed persistence layer
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app.db.database import SessionLocal
from app.db.models import AuditRecordDB, SecretAuditRecordDB
import uuid
import time


class AuditService:
    """Audit log storage with SQLite database persistence"""
    
    def __init__(self):
        """Initialize audit service with database connection"""
        self.db = SessionLocal()
    
    def __del__(self):
        """Cleanup database session"""
        if self.db:
            self.db.close()
    
    def log_incident(self, incident_data: dict) -> bool:
        """Log a rotation incident to database"""
        db_session = SessionLocal()
        try:
            # Convert datetime to ISO string if needed
            timestamp = incident_data.get("timestamp")
            if isinstance(timestamp, datetime):
                timestamp = timestamp.isoformat()
            elif not timestamp:
                timestamp = datetime.utcnow().isoformat()
            
            # Create database record
            audit_record = AuditRecordDB(
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
            
            db_session.add(audit_record)
            db_session.commit()
            print(f"📝 Audit log saved to database for incident: {audit_record.incident_id}")
            return True
            
        except SQLAlchemyError as e:
            db_session.rollback()
            print(f"❌ Database error logging incident: {str(e)}")
            return False
        except Exception as e:
            db_session.rollback()
            print(f"❌ Failed to log incident: {str(e)}")
            return False
        finally:
            db_session.close()
    
    def get_incident(self, incident_id: str) -> Optional[dict]:
        """Retrieve audit log by incident ID from database"""
        db_session = SessionLocal()
        try:
            record = db_session.query(AuditRecordDB).filter(
                AuditRecordDB.incident_id == incident_id
            ).first()
            
            if record:
                return record.to_dict()
            return None
        except Exception as e:
            print(f"❌ Error retrieving incident {incident_id}: {str(e)}")
            return None
        finally:
            db_session.close()
    
    def get_all_incidents(self) -> List[dict]:
        """Get all audit logs from database"""
        db_session = SessionLocal()
        try:
            records = db_session.query(AuditRecordDB).order_by(
                AuditRecordDB.created_at.desc()
            ).all()
            return [record.to_dict() for record in records]
        except Exception as e:
            print(f"❌ Error retrieving all incidents: {str(e)}")
            return []
        finally:
            db_session.close()
    
    def get_user_incidents(self, iam_user: str) -> List[dict]:
        """Get all incidents for a specific IAM user from database"""
        db_session = SessionLocal()
        try:
            records = db_session.query(AuditRecordDB).filter(
                AuditRecordDB.iam_user == iam_user
            ).order_by(
                AuditRecordDB.created_at.desc()
            ).all()
            return [record.to_dict() for record in records]
        except Exception as e:
            print(f"❌ Error retrieving incidents for user {iam_user}: {str(e)}")
            return []
        finally:
            db_session.close()
    
    def get_incidents_by_status(self, status: str) -> List[dict]:
        """Get incidents filtered by rotation status from database"""
        db_session = SessionLocal()
        try:
            records = db_session.query(AuditRecordDB).filter(
                AuditRecordDB.rotation_status == status
            ).order_by(
                AuditRecordDB.created_at.desc()
            ).all()
            return [record.to_dict() for record in records]
        except Exception as e:
            print(f"❌ Error retrieving incidents with status {status}: {str(e)}")
            return []
        finally:
            db_session.close()
    
    def update_incident(self, incident_id: str, updates: dict) -> bool:
        """Update an existing audit record"""
        db_session = SessionLocal()
        try:
            record = db_session.query(AuditRecordDB).filter(
                AuditRecordDB.incident_id == incident_id
            ).first()
            
            if not record:
                print(f"⚠️  Incident {incident_id} not found for update")
                return False
            
            # Update allowed fields
            allowed_fields = [
                "rotation_status", "rotation_time_ms", 
                "old_key_deactivated", "new_key_id", "error_message"
            ]
            for field, value in updates.items():
                if field in allowed_fields and value is not None:
                    setattr(record, field, value)
            
            db_session.commit()
            print(f"✏️  Audit record updated for incident: {incident_id}")
            return True
        except Exception as e:
            db_session.rollback()
            print(f"❌ Error updating incident {incident_id}: {str(e)}")
            return False
        finally:
            db_session.close()
    
    def get_incident_count(self) -> int:
        """Get total count of audit records"""
        db_session = SessionLocal()
        try:
            count = db_session.query(AuditRecordDB).count()
            return count
        except Exception as e:
            print(f"❌ Error counting incidents: {str(e)}")
            return 0
        finally:
            db_session.close()
    
    # ========================================================================
    # Secret Storage Audit Methods
    # ========================================================================
    
    def log_secret_operation(self, secret_data: dict) -> Optional[str]:
        """
        Log a secret storage/retrieval operation to database.
        
        Args:
            secret_data: Dict containing operation details
            
        Returns:
            audit_id if successful, None if failed
        """
        db_session = SessionLocal()
        audit_id = str(uuid.uuid4())
        
        try:
            # Create database record for secret operation
            secret_record = SecretAuditRecordDB(
                audit_id=audit_id,
                secret_id=secret_data.get("secret_id"),
                service_name=secret_data.get("service_name", "unknown"),
                environment=secret_data.get("environment", "unknown"),
                operation_type=secret_data.get("operation_type", "unknown"),  # store, retrieve, delete
                operation_status=secret_data.get("operation_status", "success"),
                request_source=secret_data.get("request_source"),
                user_identifier=secret_data.get("user_identifier"),
                code_language=secret_data.get("code_language"),
                code_generated=secret_data.get("code_generated", False),
                secret_type=secret_data.get("secret_type"),  # json or simple
                version_id=secret_data.get("version_id"),
                description=secret_data.get("description"),
                operation_time_ms=secret_data.get("operation_time_ms"),
                error_message=secret_data.get("error_message")
            )
            
            db_session.add(secret_record)
            db_session.commit()
            print(f"📝 Secret audit log saved: {audit_id} for {secret_data.get('secret_id')} ({secret_data.get('operation_type')})")
            return audit_id
            
        except SQLAlchemyError as e:
            db_session.rollback()
            print(f"❌ Database error logging secret operation: {str(e)}")
            return None
        except Exception as e:
            db_session.rollback()
            print(f"❌ Failed to log secret operation: {str(e)}")
            return None
        finally:
            db_session.close()
    
    def get_secret_operations(self, secret_id: str) -> List[dict]:
        """Get all operations for a specific secret"""
        db_session = SessionLocal()
        try:
            records = db_session.query(SecretAuditRecordDB).filter(
                SecretAuditRecordDB.secret_id == secret_id
            ).order_by(
                SecretAuditRecordDB.created_at.desc()
            ).all()
            return [record.to_dict() for record in records]
        except Exception as e:
            print(f"❌ Error retrieving operations for secret {secret_id}: {str(e)}")
            return []
        finally:
            db_session.close()
    
    def get_all_secret_operations(self, limit: int = None) -> List[dict]:
        """Get all secret storage operations from database"""
        db_session = SessionLocal()
        try:
            query = db_session.query(SecretAuditRecordDB).order_by(
                SecretAuditRecordDB.created_at.desc()
            )
            
            if limit:
                query = query.limit(limit)
            
            records = query.all()
            return [record.to_dict() for record in records]
        except Exception as e:
            print(f"❌ Error retrieving all secret operations: {str(e)}")
            return []
        finally:
            db_session.close()
    
    def get_secret_operations_by_service(self, service_name: str) -> List[dict]:
        """Get all operations for a specific service"""
        db_session = SessionLocal()
        try:
            records = db_session.query(SecretAuditRecordDB).filter(
                SecretAuditRecordDB.service_name == service_name
            ).order_by(
                SecretAuditRecordDB.created_at.desc()
            ).all()
            return [record.to_dict() for record in records]
        except Exception as e:
            print(f"❌ Error retrieving operations for service {service_name}: {str(e)}")
            return []
        finally:
            db_session.close()
    
    def get_secret_operations_by_environment(self, environment: str) -> List[dict]:
        """Get all operations for a specific environment"""
        db_session = SessionLocal()
        try:
            records = db_session.query(SecretAuditRecordDB).filter(
                SecretAuditRecordDB.environment == environment
            ).order_by(
                SecretAuditRecordDB.created_at.desc()
            ).all()
            return [record.to_dict() for record in records]
        except Exception as e:
            print(f"❌ Error retrieving operations for environment {environment}: {str(e)}")
            return []
        finally:
            db_session.close()
    
    def get_secret_operations_by_type(self, operation_type: str) -> List[dict]:
        """Get all operations of a specific type (store, retrieve, delete, etc.)"""
        db_session = SessionLocal()
        try:
            records = db_session.query(SecretAuditRecordDB).filter(
                SecretAuditRecordDB.operation_type == operation_type
            ).order_by(
                SecretAuditRecordDB.created_at.desc()
            ).all()
            return [record.to_dict() for record in records]
        except Exception as e:
            print(f"❌ Error retrieving operations of type {operation_type}: {str(e)}")
            return []
        finally:
            db_session.close()
    
    def get_secret_operations_by_status(self, status: str) -> List[dict]:
        """Get all operations with a specific status (success, failed)"""
        db_session = SessionLocal()
        try:
            records = db_session.query(SecretAuditRecordDB).filter(
                SecretAuditRecordDB.operation_status == status
            ).order_by(
                SecretAuditRecordDB.created_at.desc()
            ).all()
            return [record.to_dict() for record in records]
        except Exception as e:
            print(f"❌ Error retrieving operations with status {status}: {str(e)}")
            return []
        finally:
            db_session.close()
    
    def get_secret_operation(self, audit_id: str) -> Optional[dict]:
        """Get a specific secret audit record by audit ID"""
        db_session = SessionLocal()
        try:
            record = db_session.query(SecretAuditRecordDB).filter(
                SecretAuditRecordDB.audit_id == audit_id
            ).first()
            
            if record:
                return record.to_dict()
            return None
        except Exception as e:
            print(f"❌ Error retrieving secret operation {audit_id}: {str(e)}")
            return None
        finally:
            db_session.close()
    
    def get_secret_audit_count(self) -> int:
        """Get total count of secret audit records"""
        db_session = SessionLocal()
        try:
            count = db_session.query(SecretAuditRecordDB).count()
            return count
        except Exception as e:
            print(f"❌ Error counting secret operations: {str(e)}")
            return 0
        finally:
            db_session.close()
    
    def get_secret_audit_stats(self) -> dict:
        """Get statistics about secret operations"""
        db_session = SessionLocal()
        try:
            total = db_session.query(SecretAuditRecordDB).count()
            successful = db_session.query(SecretAuditRecordDB).filter(
                SecretAuditRecordDB.operation_status == "success"
            ).count()
            failed = db_session.query(SecretAuditRecordDB).filter(
                SecretAuditRecordDB.operation_status == "failed"
            ).count()
            
            # Get unique services
            services = db_session.query(SecretAuditRecordDB.service_name).distinct().all()
            service_list = [s[0] for s in services]
            
            return {
                "total_operations": total,
                "successful": successful,
                "failed": failed,
                "failure_rate": (failed / total * 100) if total > 0 else 0,
                "unique_services": len(service_list),
                "services": service_list
            }
        except Exception as e:
            print(f"❌ Error getting secret audit stats: {str(e)}")
            return {}
        finally:
            db_session.close()
