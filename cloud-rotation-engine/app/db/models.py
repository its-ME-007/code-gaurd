"""
SQLAlchemy ORM models for audit records
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.sql import func
from datetime import datetime
from app.db.database import Base


class AuditRecordDB(Base):
    """SQLAlchemy model for audit records - persisted to SQLite"""
    __tablename__ = "audit_records"
    
    # Primary key
    incident_id = Column(String(255), primary_key=True, unique=True, nullable=False)
    
    # Incident details
    iam_user = Column(String(255), nullable=False, index=True)
    access_key_id = Column(String(255), nullable=False)
    risk_level = Column(String(50), nullable=False)
    
    # Status information
    rotation_status = Column(String(50), nullable=False, index=True)
    policy_level = Column(String(255), nullable=False)
    
    # Timing
    timestamp = Column(String(255), nullable=False)
    rotation_time_ms = Column(Integer, nullable=True)
    
    # Rotation results
    old_key_deactivated = Column(Boolean, default=False)
    new_key_id = Column(String(255), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> dict:
        """Convert database record to dictionary"""
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
    
    def __repr__(self):
        return f"<AuditRecordDB(incident_id={self.incident_id}, iam_user={self.iam_user})>"


class SecretAuditRecordDB(Base):
    """SQLAlchemy model for secret storage and API key operations audit trail"""
    __tablename__ = "secret_audit_records"
    
    # Primary key
    audit_id = Column(String(255), primary_key=True, unique=True, nullable=False)
    
    # Request details
    secret_id = Column(String(255), nullable=False, index=True)
    service_name = Column(String(255), nullable=False, index=True)
    environment = Column(String(50), nullable=False, index=True)
    
    # Operation details
    operation_type = Column(String(50), nullable=False, index=True)  # store, retrieve, delete, etc.
    operation_status = Column(String(50), nullable=False, index=True)  # success, failed
    
    # User/Client info
    request_source = Column(String(255), nullable=True)  # IP or service name requesting
    user_identifier = Column(String(255), nullable=True)  # Who initiated the request
    
    # Code generation (if applicable)
    code_language = Column(String(50), nullable=True)  # python, javascript, go, etc.
    code_generated = Column(Boolean, default=False)
    
    # Secret type classification
    secret_type = Column(String(50), nullable=True)  # json, simple
    
    # Metadata
    version_id = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Performance
    operation_time_ms = Column(Integer, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> dict:
        """Convert database record to dictionary"""
        return {
            "audit_id": self.audit_id,
            "secret_id": self.secret_id,
            "service_name": self.service_name,
            "environment": self.environment,
            "operation_type": self.operation_type,
            "operation_status": self.operation_status,
            "request_source": self.request_source,
            "user_identifier": self.user_identifier,
            "code_language": self.code_language,
            "code_generated": self.code_generated,
            "secret_type": self.secret_type,
            "version_id": self.version_id,
            "description": self.description,
            "operation_time_ms": self.operation_time_ms,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<SecretAuditRecordDB(audit_id={self.audit_id}, secret_id={self.secret_id})>"
