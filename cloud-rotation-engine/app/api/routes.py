"""
API routes for Cloud Key Rotation Engine
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.api.schemas import (
    RotationRequest,
    SecretStoreRequest,
    SecretRetrieveResponse,
    SecretDeleteRequest,
    SecretClassificationResponse,
    CodeGenerationRequest,
    CodeGenerationResponse,
    SecretStoreAndGenerateRequest,
    SecretStoreAndGenerateResponse
)
from app.services.rotation_service import RotationService
from app.services.secret_manager import (
    SecretsManagerService,
    DetectedSecretClassifier,
    SecretStorageError,
    SecretRetrievalError,
    SecretClassificationError
)
from app.services.secret_code_generator import SecretCodeGenerator
from app.core.config import settings

router = APIRouter(prefix="/api/v1", tags=["rotation"])

rotation_service = RotationService()
secrets_service = SecretsManagerService()
classifier = DetectedSecretClassifier()


@router.post("/rotate")
async def rotate_access_key(request: RotationRequest):
    """
    Rotate a compromised AWS access key
    
    - **iam_user**: IAM username whose key is compromised
    - **access_key_id**: The exposed access key ID
    - **incident_id**: Unique incident identifier
    - **risk_level**: Severity level (critical/high/medium/low)
    """
    try:
        result = await rotation_service.rotate_key(
            iam_user=request.iam_user,
            access_key_id=request.access_key_id,
            incident_id=request.incident_id,
            risk_level=request.risk_level
        )
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=result.get("message", result.get("reason", "Rotation failed"))
            )
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Rotation failed: {str(e)}"
        )


@router.get("/audit/{incident_id}")
async def get_audit_log(incident_id: str):
    """Get audit log for a specific incident"""
    incident = rotation_service.audit_service.get_incident(incident_id)
    
    if not incident:
        raise HTTPException(
            status_code=404,
            detail=f"Audit log not found for incident: {incident_id}"
        )
    
    return JSONResponse(content=incident)


@router.get("/audit")
async def get_all_audit_logs():
    """Get all audit logs"""
    logs = rotation_service.audit_service.get_all_incidents()
    return JSONResponse(content={
        "total": len(logs),
        "incidents": logs
    })


@router.get("/user/{iam_user}/audit")
async def get_user_audit_logs(iam_user: str):
    """Get all audit logs for a specific IAM user"""
    logs = rotation_service.audit_service.get_user_incidents(iam_user)
    return JSONResponse(content={
        "iam_user": iam_user,
        "total": len(logs),
        "incidents": logs
    })


@router.get("/user/{iam_user}/keys")
async def analyze_user_keys(iam_user: str):
    """Analyze access keys for a specific IAM user"""
    return {
        "iam_user": iam_user,
        "status": "not_implemented",
        "message": "Key analysis not yet implemented"
    }


# ============================================================================
# Secret Management Endpoints
# ============================================================================

@router.post("/secrets/store")
async def store_secret(request: SecretStoreRequest):
    """
    Store a secret in AWS Secrets Manager with automatic classification.
    
    The system automatically detects whether the secret is JSON or a simple string
    and stores accordingly with proper metadata.
    
    - **secret_id**: Unique identifier (e.g., "codeguard/gemini/project-x")
    - **secret_value**: The secret (can be JSON or simple string)
    - **service_name**: Service providing the secret
    - **environment**: Environment context (dev/staging/production)
    - **description**: Optional description
    - **tags**: Optional tags for organization
    """
    try:
        result = secrets_service.store_secret(
            secret_id=request.secret_id,
            secret_value=request.secret_value,
            service_name=request.service_name,
            environment=request.environment,
            description=request.description,
            tags=request.tags
        )
        return JSONResponse(content=result)
    except SecretStorageError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Secret storage failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/secrets/{secret_id}")
async def retrieve_secret(secret_id: str, auto_parse: bool = True):
    """
    Retrieve a secret from AWS Secrets Manager.
    
    Automatically detects and parses JSON secrets, returns simple strings as-is.
    
    - **secret_id**: The secret identifier
    - **auto_parse**: Whether to automatically parse JSON secrets
    
    Returns:
    - **value**: The actual secret value (parsed if JSON)
    - **secret_type**: "json" or "simple"
    - **metadata**: Service, timestamp, environment info
    """
    try:
        result = secrets_service.retrieve_secret(
            secret_id=secret_id,
            auto_parse=auto_parse
        )
        return JSONResponse(content=result)
    except SecretRetrievalError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Secret retrieval failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.delete("/secrets/{secret_id}")
async def delete_secret(secret_id: str, force_delete: bool = False, recovery_days: int = 7):
    """
    Delete a secret from AWS Secrets Manager.
    
    By default, schedules deletion after recovery period.
    Use force_delete=true for immediate deletion without recovery option.
    
    - **secret_id**: The secret identifier
    - **force_delete**: If true, immediately delete (no recovery)
    - **recovery_days**: Days before deletion takes effect
    """
    try:
        result = secrets_service.delete_secret(
            secret_id=secret_id,
            force_delete=force_delete,
            recovery_days=recovery_days
        )
        return JSONResponse(content=result)
    except SecretStorageError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Secret deletion failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/secrets")
async def list_secrets(service_filter: str = None):
    """
    List all secrets, optionally filtered by service.
    
    - **service_filter**: Optional service name to filter by
    
    Returns list of secrets with metadata (name, ARN, creation date, tags)
    """
    try:
        result = secrets_service.list_secrets(service_filter=service_filter)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list secrets: {str(e)}"
        )


@router.post("/secrets/classify")
async def classify_secret(secret_value: str):
    """
    Classify a secret to determine if it's JSON or a simple string.
    
    Useful for validation before storing secrets.
    
    - **secret_value**: The secret value to classify
    
    Returns:
    - **secret_type**: "json" or "simple"
    - **is_json**: Boolean indicating JSON format
    """
    try:
        secret_type, parsed_value = classifier.classify_secret(secret_value)
        return JSONResponse(content={
            "status": "success",
            "secret_type": secret_type,
            "is_json": secret_type == "json",
            "message": f"Secret classified as {secret_type}"
        })
    except SecretClassificationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Classification failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/secrets/generate-code")
async def generate_access_code(request: CodeGenerationRequest):
    """
    Generate language-specific code to retrieve a secret.
    
    Supports multiple programming languages:
    - **python** (py)
    - **javascript** (js, node)
    - **go**
    - **java**
    - **php**
    - **csharp** (cs)
    
    Returns ready-to-use code snippet that can be copied directly into your application.
    
    Args:
        - **secret_id**: Secret identifier (e.g., "codeguard/gemini/production")
        - **language**: Programming language (default: python)
        - **region**: AWS region (default: us-east-1)
    
    Returns:
        Generated code snippet for the specified language
    """
    try:
        gen = SecretCodeGenerator()
        
        code = gen.generate_code(
            secret_id=request.secret_id,
            language=request.language or "python",
            region=request.region or "us-east-1"
        )
        
        return JSONResponse(content={
            "status": "success",
            "secret_id": request.secret_id,
            "language": request.language or "python",
            "code": code,
            "message": f"Code snippet generated for {request.language or 'python'}"
        })
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate code: {str(e)}"
        )


@router.post("/secrets/store-and-generate-code")
async def store_secret_and_generate_code(request: SecretStoreAndGenerateRequest):
    """
    Store a secret in AWS Secrets Manager AND generate retrieval code in one action.
    
    This combines two operations:
    1. Store the secret securely with automatic format detection
    2. Generate language-specific code snippet for retrieving the secret
    
    Supported languages: python, javascript, go, java, php, csharp
    
    Args:
        - **secret_id**: Unique secret identifier (e.g., "codeguard/openai/production")
        - **secret_value**: The secret value to store (JSON or simple string)
        - **service_name**: Service name (openai, gemini, stripe, etc.)
        - **language**: Language for code generation (default: python)
        - **environment**: Environment context (dev, staging, production)
        - **description**: Optional description
    
    Returns:
        Combined response with storage result AND generated code snippet
    """
    try:
        from datetime import datetime
        
        # Step 1: Store the secret
        store_result = secrets_service.store_secret(
            secret_id=request.secret_id,
            secret_value=request.secret_value,
            service_name=request.service_name,
            environment=request.environment,
            description=request.description
        )
        
        # Step 2: Generate code for the secret
        gen = SecretCodeGenerator()
        code = gen.generate_code(
            secret_id=request.secret_id,
            language=request.language or "python",
            region=settings.aws_region
        )
        
        # Step 3: Return combined response
        return JSONResponse(content={
            "status": "success",
            "secret_id": request.secret_id,
            "secret_type": store_result.get("secret_type", "unknown"),
            "version_id": store_result.get("version_id"),
            "operation": "store_and_generate",
            "storage_message": store_result.get("message", "Secret stored successfully"),
            "language": request.language or "python",
            "code": code,
            "code_message": f"Code snippet generated for {request.language or 'python'}",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except SecretStorageError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Secret storage failed: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Code generation failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Operation failed: {str(e)}"
        )

