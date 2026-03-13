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


# ============================================================================
# Secret Management Schemas
# ============================================================================

class SecretStoreRequest(BaseModel):
    """Schema for storing a secret"""
    secret_id: str = Field(..., description="Unique secret identifier (e.g., 'codeguard/gemini/project-x')")
    secret_value: str = Field(..., description="The secret value (JSON or simple string)")
    service_name: str = Field(..., description="Service providing/using this secret")
    environment: str = Field("default", description="Environment context (dev/staging/production)")
    description: Optional[str] = Field(None, description="Optional description")
    tags: Optional[dict] = Field(None, description="Optional tags for organization")

    class Config:
        json_schema_extra = {
            "example": {
                "secret_id": "codeguard/gemini/project-alpha",
                "secret_value": '{"api_key": "AIza...", "project_id": "xyz"}',
                "service_name": "gemini",
                "environment": "production",
                "description": "Google Gemini API credentials"
            }
        }


class SecretStoreResponse(BaseModel):
    """Schema for secret storage response"""
    status: str = Field(..., description="success or error")
    operation: Optional[str] = Field(None, description="created or updated")
    secret_id: str = Field(..., description="The stored secret ID")
    secret_type: str = Field(..., description="json or simple")
    version_id: Optional[str] = Field(None, description="AWS secret version ID")
    timestamp: str = Field(..., description="Storage timestamp")
    message: str = Field(..., description="Descriptive message")


class SecretRetrieveResponse(BaseModel):
    """Schema for secret retrieval response"""
    status: str = Field(..., description="success or error")
    secret_id: str = Field(..., description="The retrieved secret ID")
    value: Optional[dict] = Field(None, description="The secret value (parsed if JSON)")
    secret_type: str = Field(..., description="json or simple")
    metadata: Optional[dict] = Field(None, description="Secret metadata")
    version_id: Optional[str] = Field(None, description="AWS version ID")
    message: str = Field(..., description="Descriptive message")


class SecretDeleteRequest(BaseModel):
    """Schema for secret deletion"""
    secret_id: str = Field(..., description="The secret to delete")
    force_delete: bool = Field(False, description="Force immediate deletion")
    recovery_days: int = Field(7, description="Recovery period in days")


class SecretClassificationResponse(BaseModel):
    """Schema for secret classification response"""
    status: str = Field(..., description="success or error")
    secret_type: str = Field(..., description="json or simple")
    is_json: bool = Field(..., description="Whether the secret is JSON format")
    message: str = Field(..., description="Descriptive message")


class CodeGenerationRequest(BaseModel):
    """Schema for code generation request"""
    secret_id: str = Field(..., description="Secret identifier (e.g., codeguard/gemini/prod)")
    language: str = Field("python", description="Programming language: python, javascript, go, java, php, csharp")
    region: Optional[str] = Field("us-east-1", description="AWS region")
    
    class Config:
        json_schema_extra = {
            "example": {
                "secret_id": "codeguard/openai/production",
                "language": "python",
                "region": "us-east-1"
            }
        }


class CodeGenerationResponse(BaseModel):
    """Schema for code generation response"""
    status: str = Field(..., description="success")
    secret_id: str = Field(..., description="The secret identifier")
    language: str = Field(..., description="Programming language")
    code: str = Field(..., description="Generated code snippet")
    message: str = Field(..., description="Descriptive message")


class SecretStoreAndGenerateRequest(BaseModel):
    """Schema for storing secret and generating retrieval code in one action"""
    secret_id: str = Field(..., description="Secret identifier (e.g., codeguard/openai/prod)")
    secret_value: str = Field(..., description="The secret value to store")
    service_name: str = Field(..., description="Service name (e.g., openai, gemini, stripe)")
    language: str = Field("python", description="Language for code generation")
    environment: str = Field("default", description="Environment (dev, staging, production)")
    description: Optional[str] = Field(None, description="Optional description of the secret")
    
    class Config:
        json_schema_extra = {
            "example": {
                "secret_id": "codeguard/openai/production",
                "secret_value": "sk-proj-abc123...",
                "service_name": "openai",
                "language": "python",
                "environment": "production"
            }
        }


class SecretStoreAndGenerateResponse(BaseModel):
    """Schema for combined store and generate response"""
    status: str = Field(..., description="success or error")
    secret_id: str = Field(..., description="The stored secret ID")
    secret_type: str = Field(..., description="json or simple")
    version_id: Optional[str] = Field(None, description="AWS secret version ID")
    operation: str = Field(..., description="The operation performed")
    storage_message: str = Field(..., description="Storage operation message")
    language: str = Field(..., description="Language used for code generation")
    code: str = Field(..., description="Generated code snippet")
    code_message: str = Field(..., description="Code generation message")
    timestamp: str = Field(..., description="Operation timestamp")


# ============================================================================
# Client-Driven Incident Logging Schemas (Supabase)
# ============================================================================

class DetectedSecretItem(BaseModel):
    """Schema for a single secret to store and generate code for"""
    type: str = Field(..., description="Type of secret (e.g., openai, aws, stripe, github)")
    language: str = Field("python", description="Language for code generation (python, javascript, go, java, php, csharp)")
    secret_value: str = Field(..., description="The actual secret value to store")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "openai",
                "language": "python",
                "secret_value": "sk-proj-abc123..."
            }
        }


class SecretIngestionRequest(BaseModel):
    """Schema for batch secret ingestion with global retrieval language"""
    secrets: list[DetectedSecretItem] = Field(..., description="Array of secrets to store")
    retrieval_language: str = Field("python", description="Language for retrieval code (python, javascript, go, java, php, csharp)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "secrets": [
                    {
                        "type": "openai",
                        "language": "python",
                        "secret_value": "sk-proj-abc123..."
                    },
                    {
                        "type": "stripe",
                        "language": "javascript",
                        "secret_value": "sk_live_..."
                    }
                ],
                "retrieval_language": "javascript"
            }
        }


class BatchSecretIngestionRequest(BaseModel):
    """Schema for batch secret detection logging (client-driven model)"""
    scan_id: str = Field(..., description="Unique identifier for this scan batch")
    repo_name: str = Field(..., description="Repository or project name")
    detected_by: str = Field(..., description="Machine or agent identifier (e.g., 'dev-machine-01')")
    secrets: list[DetectedSecretItem] = Field(..., description="List of detected secrets")
    
    class Config:
        json_schema_extra = {
            "example": {
                "scan_id": "scan_2026_01",
                "repo_name": "project-alpha",
                "detected_by": "dev-machine-01",
                "secrets": [
                    {
                        "secret_type": "gemini_api_key",
                        "secret_hash": "hash_value_1",
                        "file_path": "app/config.py",
                        "line_number": 18,
                        "risk_level": "high"
                    },
                    {
                        "secret_type": "aws_access_key",
                        "secret_hash": "hash_value_2",
                        "file_path": "aws/client.py",
                        "line_number": 5,
                        "risk_level": "critical"
                    }
                ]
            }
        }


class BatchSecretIngestionResponse(BaseModel):
    """Response from batch secret ingestion endpoint"""
    status: str = Field(..., description="success, partial, or error")
    scan_id: str = Field(..., description="The scan_id from the request")
    incidents_logged: int = Field(..., description="Number of new incidents logged")
    duplicates_detected: int = Field(..., description="Number of duplicate secrets found")
    incidents: Optional[list[str]] = Field(None, description="List of incident IDs created")
    errors: Optional[list[str]] = Field(None, description="List of processing errors if any")
    message: str = Field(..., description="Human-readable status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "scan_id": "scan_2026_01",
                "incidents_logged": 2,
                "duplicates_detected": 1,
                "incidents": ["uuid-1", "uuid-2"],
                "errors": None,
                "message": "Successfully processed 2 detected secrets"
            }
        }


class RemediationScriptGenerationRequest(BaseModel):
    """Schema for generating remediation scripts after detection"""
    incident_id: str = Field(..., description="The reported incident ID")
    secret_value: str = Field(..., description="The actual secret (provided only by developer locally)")
    secret_type: str = Field(..., description="Type of secret (aws, openai, etc.)")
    service_name: str = Field(..., description="Service name")
    language: str = Field("python", description="Language for generated script")
    environment: str = Field("production", description="Target environment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "uuid-123",
                "secret_value": "sk-proj-abc123...",
                "secret_type": "openai",
                "service_name": "openai",
                "language": "python",
                "environment": "production"
            }
        }


class RemediationScriptGenerationResponse(BaseModel):
    """Response containing storage and retrieval scripts"""
    status: str = Field(..., description="success or error")
    incident_id: str = Field(..., description="The incident ID")
    storage_script: str = Field(..., description="Python script for storing secret in AWS Secrets Manager")
    retrieval_code: str = Field(..., description="Generated code snippet for retrieving secret at runtime")
    instructions: str = Field(..., description="Step-by-step remediation instructions")
    message: str = Field(..., description="Summary message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "incident_id": "uuid-123",
                "storage_script": "import boto3\n...",
                "retrieval_code": "import boto3\nresponse = client.get_secret_value(...)",
                "instructions": "1. Run the storage script\n2. Update your code...",
                "message": "Remediation scripts generated successfully"
            }
        }
