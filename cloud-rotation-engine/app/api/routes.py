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
    SecretStoreAndGenerateResponse,
    BatchSecretItem,
    BatchStoreAndGenerateRequest,
    BatchSecretProcessResult,
    BatchStoreAndGenerateResponse
)
from app.services.rotation_service import RotationService
from app.services.audit_service import AuditService
from app.services.secret_manager import (
    SecretsManagerService,
    DetectedSecretClassifier,
    SecretStorageError,
    SecretRetrievalError,
    SecretClassificationError
)
from app.services.secret_code_generator import SecretCodeGenerator
from app.core.config import settings
from datetime import datetime
import time

router = APIRouter(prefix="/api/v1", tags=["rotation"])

rotation_service = RotationService()
audit_service = AuditService()
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
    start_time = time.time()
    operation_status = "failed"
    error_msg = None
    secret_type = None
    version_id = None
    
    try:
        result = secrets_service.store_secret(
            secret_id=request.secret_id,
            secret_value=request.secret_value,
            service_name=request.service_name,
            environment=request.environment,
            description=request.description,
            tags=request.tags
        )
        
        # Track successful operation
        operation_status = "success"
        secret_type = result.get("secret_type", "unknown")
        version_id = result.get("version_id")
        
        # Log the operation to audit table
        audit_service.log_secret_operation({
            "secret_id": request.secret_id,
            "service_name": request.service_name,
            "environment": request.environment,
            "operation_type": "store",
            "operation_status": operation_status,
            "secret_type": secret_type,
            "version_id": version_id,
            "description": request.description,
            "operation_time_ms": int((time.time() - start_time) * 1000),
            "code_generated": False
        })
        
        return JSONResponse(content=result)
    except SecretStorageError as e:
        error_msg = str(e)
        # Log failed operation
        audit_service.log_secret_operation({
            "secret_id": request.secret_id,
            "service_name": request.service_name,
            "environment": request.environment,
            "operation_type": "store",
            "operation_status": "failed",
            "error_message": error_msg,
            "operation_time_ms": int((time.time() - start_time) * 1000)
        })
        raise HTTPException(
            status_code=400,
            detail=f"Secret storage failed: {error_msg}"
        )
    except Exception as e:
        error_msg = str(e)
        # Log failed operation
        audit_service.log_secret_operation({
            "secret_id": request.secret_id,
            "service_name": request.service_name,
            "environment": request.environment,
            "operation_type": "store",
            "operation_status": "failed",
            "error_message": error_msg,
            "operation_time_ms": int((time.time() - start_time) * 1000)
        })
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {error_msg}"
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
    start_time = time.time()
    operation_status = "failed"
    error_msg = None
    secret_type = None
    version_id = None
    code_language = request.language or "python"
    
    try:
        # Step 1: Store the secret
        store_result = secrets_service.store_secret(
            secret_id=request.secret_id,
            secret_value=request.secret_value,
            service_name=request.service_name,
            environment=request.environment,
            description=request.description
        )
        
        secret_type = store_result.get("secret_type", "unknown")
        version_id = store_result.get("version_id")
        
        # Step 2: Generate code for the secret
        gen = SecretCodeGenerator()
        code = gen.generate_code(
            secret_id=request.secret_id,
            language=code_language,
            region=settings.aws_region
        )
        
        # Track successful operation
        operation_status = "success"
        
        # Step 3: Log the combined operation to audit table
        audit_service.log_secret_operation({
            "secret_id": request.secret_id,
            "service_name": request.service_name,
            "environment": request.environment,
            "operation_type": "store_and_generate",
            "operation_status": operation_status,
            "code_language": code_language,
            "code_generated": True,
            "secret_type": secret_type,
            "version_id": version_id,
            "description": request.description,
            "operation_time_ms": int((time.time() - start_time) * 1000)
        })
        
        # Step 4: Return combined response
        return JSONResponse(content={
            "status": "success",
            "secret_id": request.secret_id,
            "secret_type": secret_type,
            "version_id": version_id,
            "operation": "store_and_generate",
            "storage_message": store_result.get("message", "Secret stored successfully"),
            "language": code_language,
            "code": code,
            "code_message": f"Code snippet generated for {code_language}",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except SecretStorageError as e:
        error_msg = str(e)
        # Log failed operation
        audit_service.log_secret_operation({
            "secret_id": request.secret_id,
            "service_name": request.service_name,
            "environment": request.environment,
            "operation_type": "store_and_generate",
            "operation_status": "failed",
            "code_language": code_language,
            "code_generated": False,
            "error_message": error_msg,
            "operation_time_ms": int((time.time() - start_time) * 1000)
        })
        raise HTTPException(
            status_code=400,
            detail=f"Secret storage failed: {error_msg}"
        )
    except ValueError as e:
        error_msg = str(e)
        # Log failed operation (storage may have succeeded)
        audit_service.log_secret_operation({
            "secret_id": request.secret_id,
            "service_name": request.service_name,
            "environment": request.environment,
            "operation_type": "store_and_generate",
            "operation_status": "partial_failure",
            "code_language": code_language,
            "code_generated": False,
            "error_message": f"Code generation failed: {error_msg}",
            "operation_time_ms": int((time.time() - start_time) * 1000)
        })
        raise HTTPException(
            status_code=400,
            detail=f"Code generation failed: {error_msg}"
        )
    except Exception as e:
        error_msg = str(e)
        # Log failed operation
        audit_service.log_secret_operation({
            "secret_id": request.secret_id,
            "service_name": request.service_name,
            "environment": request.environment,
            "operation_type": "store_and_generate",
            "operation_status": "failed",
            "code_language": code_language,
            "code_generated": False,
            "error_message": error_msg,
            "operation_time_ms": int((time.time() - start_time) * 1000)
        })
        raise HTTPException(
            status_code=500,
            detail=f"Operation failed: {error_msg}"
        )


@router.post("/secrets/store-and-generate-batch")
async def store_batch_secrets_and_generate_code(request: BatchStoreAndGenerateRequest):
    """
    Store multiple secrets in batch AND generate unified retrieval code.
    
    This endpoint:
    1. Stores each secret individually in AWS Secrets Manager (isolated error handling)
    2. Tracks per-secret success/failure
    3. Generates a single unified code snippet in the specified language that retrieves all secrets
    
    The 'language' field in each secret is stored as metadata for reference/auditing.
    The 'retrieval_language' determines the language of the unified code output.
    
    Args:
        - **secrets**: Array of secret objects, each with:
            - type: Secret type/provider (e.g., "openai", "stripe")
            - language: Language context (stored as metadata)
            - secret_value: The secret value (JSON or simple string)
        - **retrieval_language**: Language for the unified code (python, javascript, go, java, php, csharp)
        - **region**: AWS region (default: us-east-1)
    
    Returns:
        - **status**: "success" (all stored), "partial_success" (some stored), or "error" (validation failed)
        - **operation_summary**: Dict with total, succeeded, failed counts
        - **processed_secrets**: Array with per-secret result details
        - **retrieval_code**: Unified code snippet for retrieving all secrets
        - **language**: Language of the retrieval code
        - **timestamp**: Operation timestamp
    
    HTTP Status Codes:
        - 201: All secrets stored successfully
        - 207: Partial success (some succeeded, some failed)
        - 400: Validation error or all failed
    """
    from app.services.secret_code_generator import SecretCodeGeneratorBatch
    import uuid
    
    start_time = time.time()
    batch_operation_id = f"batch_{uuid.uuid4()}"
    retrieval_language = request.retrieval_language or "python"
    region = request.region or settings.aws_region
    
    try:
        # Validate retrieval language
        retrieval_lang_lower = retrieval_language.lower()
        if retrieval_lang_lower not in SecretCodeGenerator.SUPPORTED_LANGUAGES:
            supported = ', '.join(SecretCodeGenerator.SUPPORTED_LANGUAGES.keys())
            raise ValueError(f"Unsupported retrieval language: {retrieval_language}. Supported: {supported}")
        
        # Validate secrets array is not empty
        if not request.secrets or len(request.secrets) == 0:
            raise ValueError("secrets array cannot be empty")
        
        # Step 1: Store all secrets with individual error handling
        batch_items = [
            {
                "type": secret.type,
                "language": secret.language,
                "secret_value": secret.secret_value
            }
            for secret in request.secrets
        ]
        
        process_results = secrets_service.store_batch_secrets(batch_items)
        
        # Separate successful and failed results
        successful_results = [r for r in process_results if r["status"] == "success"]
        failed_results = [r for r in process_results if r["status"] == "error"]
        
        # Step 2: If no secrets were stored successfully, return error
        if len(successful_results) == 0:
            error_details = [f"{r['type']}: {r['error_message']}" for r in failed_results]
            
            # Log failed batch operation
            audit_service.log_secret_operation({
                "secret_id": batch_operation_id,
                "operation_type": "batch_store_and_generate",
                "operation_status": "failed",
                "batch_size": len(request.secrets),
                "succeeded": 0,
                "failed": len(failed_results),
                "code_generated": False,
                "error_message": f"All secrets failed: {'; '.join(error_details)}",
                "operation_time_ms": int((time.time() - start_time) * 1000)
            })
            
            raise HTTPException(
                status_code=400,
                detail=f"Batch operation failed: {'; '.join(error_details)}"
            )
        
        # Step 3: Generate unified code for all successful secrets
        successful_secret_ids = [r["secret_id"] for r in successful_results]
        
        try:
            retrieval_code = SecretCodeGeneratorBatch.generate_batch_code(
                secret_ids=successful_secret_ids,
                language=retrieval_language,
                region=region
            )
        except ValueError as e:
            # Log failed code generation
            audit_service.log_secret_operation({
                "secret_id": batch_operation_id,
                "operation_type": "batch_store_and_generate",
                "operation_status": "partial_failure",
                "batch_size": len(request.secrets),
                "succeeded": len(successful_results),
                "failed": len(failed_results),
                "code_generated": False,
                "error_message": f"Code generation failed: {str(e)}",
                "operation_time_ms": int((time.time() - start_time) * 1000)
            })
            raise HTTPException(
                status_code=400,
                detail=f"Code generation failed: {str(e)}"
            )
        
        # Step 4: Determine overall status
        overall_status = "success" if len(failed_results) == 0 else "partial_success"
        http_status_code = 201 if len(failed_results) == 0 else 207
        
        # Step 5: Log successful batch operation
        audit_service.log_secret_operation({
            "secret_id": batch_operation_id,
            "operation_type": "batch_store_and_generate",
            "operation_status": overall_status,
            "batch_size": len(request.secrets),
            "succeeded": len(successful_results),
            "failed": len(failed_results),
            "retrieval_language": retrieval_language,
            "code_generated": True,
            "operation_time_ms": int((time.time() - start_time) * 1000)
        })
        
        # Step 6: Build response
        response_content = {
            "status": overall_status,
            "operation_summary": {
                "total": len(request.secrets),
                "succeeded": len(successful_results),
                "failed": len(failed_results)
            },
            "processed_secrets": process_results,
            "retrieval_code": retrieval_code,
            "language": retrieval_language,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=response_content, status_code=http_status_code)
        
    except ValueError as e:
        # Validation error
        audit_service.log_secret_operation({
            "secret_id": batch_operation_id,
            "operation_type": "batch_store_and_generate",
            "operation_status": "failed",
            "error_message": f"Validation error: {str(e)}",
            "operation_time_ms": int((time.time() - start_time) * 1000)
        })
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}"
        )
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        # Unexpected error
        error_msg = str(e)
        audit_service.log_secret_operation({
            "secret_id": batch_operation_id,
            "operation_type": "batch_store_and_generate",
            "operation_status": "failed",
            "error_message": f"Unexpected error: {error_msg}",
            "operation_time_ms": int((time.time() - start_time) * 1000)
        })
        raise HTTPException(
            status_code=500,
            detail=f"Batch operation failed: {error_msg}"
        )


# ============================================================================
# Secret Audit Endpoints
# ============================================================================

@router.get("/secrets-audit/all")
async def get_all_secret_audits(limit: int = None):
    """
    Get all secret storage and retrieval operations.
    
    Optional parameters:
    - **limit**: Maximum number of records to return (default: all)
    
    Returns complete audit trail of secret operations
    """
    operations = audit_service.get_all_secret_operations(limit=limit)
    
    return JSONResponse(content={
        "total": len(operations),
        "operations": operations
    })
