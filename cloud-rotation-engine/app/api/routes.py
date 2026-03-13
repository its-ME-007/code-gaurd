"""
API routes for CodeGuard - Client-Driven Secret Management

Single endpoint for generating storage and retrieval code for secrets.
Backend ONLY generates code - no secrets are stored on the backend.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.api.schemas import DetectedSecretItem, SecretIngestionRequest
from app.services.audit_service import AuditService
from app.services.remediation_script_generator import RemediationScriptGenerator
from app.core.config import settings
from datetime import datetime
import time

router = APIRouter(prefix="/api/v1", tags=["secrets"])

audit_service = AuditService()
remediation_generator = RemediationScriptGenerator()


@router.post("/detected-secrets/ingest")
async def ingest_detected_secrets_storage_only(
    request: SecretIngestionRequest,
    repo_name: str = "unknown",
    environment: str = "default"
):
    """
    Generate a single master storage script for all secrets.
    
    All secrets are combined into one Python script.
    User runs it locally to store all secrets in AWS at once.
    
    **Request Body**: SecretIngestionRequest object with array of secrets and global retrieval language
    ```json
    {
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
    ```
    
    **Query Parameters**:
    - `repo_name`: Repository name for secret organization (default: "unknown")
    - `environment`: Environment context (dev, staging, production) (default: "default")
    
    **Response**: Single combined save_script with all secrets
    
    **Important**: 
    - Secrets never touch the backend
    - User runs the save_script locally to store all secrets in their AWS account
    """
    try:
        start_time = time.time()
        failed_count = 0
        storage_scripts = []  # Collect generated storage scripts
        
        remediation_gen = RemediationScriptGenerator()
        
        for idx, secret in enumerate(request.secrets):
            try:
                # Generate secret name for AWS Secrets Manager
                secret_name = f"codeguard/{secret.type}/{repo_name}/{environment}"
                
                # Generate storage script in user-specified language
                gen_result = remediation_gen.generate_remediation_scripts(
                    incident_id=f"ingest_{idx}",
                    secret_value=secret.secret_value,
                    secret_type=secret.type,
                    service_name=secret.type,
                    language=request.retrieval_language,  # Use specified language for storage
                    environment=environment,
                    region=settings.aws_region
                )
                
                if gen_result["status"] != "success":
                    raise Exception(gen_result.get("message", "Code generation failed"))
                
                # Store the generated storage script
                storage_scripts.append({
                    "type": secret.type,
                    "script": gen_result.get("storage_script", ""),
                    "secret_name": secret_name
                })
                
                # Log the code generation (audit trail of what was generated)
                audit_service.log_secret_operation({
                    "secret_id": secret_name,
                    "service_name": secret.type,
                    "environment": environment,
                    "operation_type": "storage_code_generation",
                    "operation_status": "success",
                    "code_language": request.retrieval_language,
                    "code_generated": True,
                    "repository": repo_name,
                    "operation_time_ms": int((time.time() - start_time) * 1000)
                })
                
            except Exception as item_error:
                failed_count += 1
                audit_service.log_secret_operation({
                    "secret_name": f"codeguard/{secret.type}/{repo_name}/{environment}",
                    "service_name": secret.type,
                    "environment": environment,
                    "operation_type": "storage_code_generation",
                    "operation_status": "failed",
                    "error_message": str(item_error),
                    "repository": repo_name,
                    "operation_time_ms": int((time.time() - start_time) * 1000)
                })
        
        # Combine all generated storage scripts into one master script
        master_script = "\n\n# ============================================================================\n"
        master_script += "# GENERATED STORAGE SCRIPTS FOR ALL SECRETS\n"
        master_script += "# ============================================================================\n"
        master_script += f"# Language: {request.retrieval_language.upper()}\n"
        master_script += f"# Total Secrets: {len(storage_scripts)}\n"
        master_script += "# Run these scripts locally to store all secrets in AWS\n"
        master_script += "# ============================================================================\n\n"
        
        for idx, script_info in enumerate(storage_scripts, 1):
            master_script += f"\n# Secret {idx}: {script_info['type']} ({script_info['secret_name']})\n"
            master_script += "# " + "="*70 + "\n"
            master_script += script_info['script'].replace("\n", "\n# ") + "\n"
        
        # Return combined response
        return JSONResponse(content={
            "status": "success" if failed_count == 0 else "partial_success",
            "total_secrets": len(request.secrets),
            "successful": len(request.secrets) - failed_count,
            "failed": failed_count,
            "save_script": master_script,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Master script combines all secrets. Run locally to save all secrets in AWS."
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Code generation failed: {str(e)}"
        )


@router.post("/detected-secrets/ingest-with-retrieval")
async def ingest_detected_secrets_with_retrieval(
    request: SecretIngestionRequest,
    repo_name: str = "unknown",
    environment: str = "default"
):
    """
    Generate a single master script with storage AND retrieval code examples.
    
    All secrets combined into one Python script.
    Global `retrieval_language` field specifies the language for all retrieval code examples.
    
    **Request Body**: SecretIngestionRequest object with array of secrets and global retrieval language
    ```json
    {
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
      "retrieval_language": "go"
    }
    ```
    
    **Query Parameters**:
    - `repo_name`: Repository name for secret organization (default: "unknown")
    - `environment`: Environment context (dev, staging, production) (default: "default")
    
    **Response**: Single combined save_script with storage and retrieval code examples in specified language
    """
    try:
        start_time = time.time()
        failed_count = 0
        secret_configs = []
        retrieval_examples = {}
        
        remediation_gen = RemediationScriptGenerator()
        
        for idx, secret in enumerate(request.secrets):
            try:
                # Generate secret name for AWS Secrets Manager
                secret_name = f"codeguard/{secret.type}/{repo_name}/{environment}"
                
                # Generate storage script in user-specified language
                storage_result = remediation_gen.generate_remediation_scripts(
                    incident_id=f"ingest_{idx}",
                    secret_value=secret.secret_value,
                    secret_type=secret.type,
                    service_name=secret.type,
                    language=request.retrieval_language,  # Use specified language for storage
                    environment=environment,
                    region=settings.aws_region
                )
                
                if storage_result["status"] != "success":
                    raise Exception(storage_result.get("message", "Storage code generation failed"))
                
                # Generate retrieval code for specified language
                retrieval_result = remediation_gen.generate_remediation_scripts(
                    incident_id=f"ingest_{idx}_retrieval",
                    secret_value=secret.secret_value,
                    secret_type=secret.type,
                    service_name=secret.type,
                    language=request.retrieval_language,  # User-specified language
                    environment=environment,
                    region=settings.aws_region
                )
                
                if retrieval_result["status"] != "success":
                    raise Exception(retrieval_result.get("message", "Retrieval code generation failed"))
                
                # Store retrieval examples
                retrieval_examples[secret_name] = {
                    "language": request.retrieval_language,
                    "code": retrieval_result.get("retrieval_code", "")
                }
                
                # Log the code generation (audit trail of what was generated)
                audit_service.log_secret_operation({
                    "secret_id": secret_name,
                    "service_name": secret.type,
                    "environment": environment,
                    "operation_type": "storage_and_retrieval_code_generation",
                    "operation_status": "success",
                    "code_language": request.retrieval_language,
                    "retrieval_language": request.retrieval_language,
                    "code_generated": True,
                    "repository": repo_name,
                    "operation_time_ms": int((time.time() - start_time) * 1000)
                })
                
            except Exception as item_error:
                failed_count += 1
                audit_service.log_secret_operation({
                    "secret_id": f"codeguard/{secret.type}/{repo_name}/{environment}",
                    "service_name": secret.type,
                    "environment": environment,
                    "operation_type": "storage_and_retrieval_code_generation",
                    "operation_status": "failed",
                    "error_message": str(item_error),
                    "repository": repo_name,
                    "operation_time_ms": int((time.time() - start_time) * 1000)
                })
        
        # Combine all generated storage scripts into one master script
        master_script = "\n\n# ============================================================================\n"
        master_script += "# GENERATED STORAGE SCRIPTS FOR ALL SECRETS\n"
        master_script += "# ============================================================================\n"
        master_script += f"# Language: {request.retrieval_language.upper()}\n"
        master_script += f"# Total Secrets: {len(storage_scripts)}\n"
        master_script += "# Run these scripts locally to store all secrets in AWS\n"
        master_script += "# ============================================================================\n\n"
        
        for idx, script_info in enumerate(storage_scripts, 1):
            master_script += f"\n# Secret {idx}: {script_info['type']} ({script_info['secret_name']})\n"
            master_script += "# " + "="*70 + "\n"
            master_script += script_info['script'].replace("\n", "\n# ") + "\n"
        
        # Build retrieval examples section
        retrieval_section = "\n\n# ============================================================================\n# RETRIEVAL CODE EXAMPLES\n# ============================================================================\n"
        for secret_name, example in retrieval_examples.items():
            retrieval_section += f"\n# For {secret_name} ({example['language'].upper()}):\n"
            retrieval_section += "# " + example['code'].replace("\n", "\n# ") + "\n"
        
        master_script += retrieval_section
        
        # Return combined response
        return JSONResponse(content={
            "status": "success" if failed_count == 0 else "partial_success",
            "total_secrets": len(request.secrets),
            "successful": len(request.secrets) - failed_count,
            "failed": failed_count,
            "save_script": master_script,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Master script combines all secrets with retrieval examples. Run storage locally, integrate retrieval code into your app."
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Code generation failed: {str(e)}"
        )
