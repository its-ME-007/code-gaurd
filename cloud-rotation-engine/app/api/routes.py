"""
API routes for Cloud Key Rotation Engine
"""
from fastapi import APIRouter, HTTPException, status
from datetime import datetime

from app.api.schemas import RotationRequest, RotationResponse, ErrorResponse
from app.services.rotation_service import RotationService
from app.core.logging_config import setup_logging


router = APIRouter(prefix="/api/v1", tags=["rotation"])
logger = setup_logging()
rotation_service = RotationService()


@router.post("/rotate", response_model=RotationResponse)
async def rotate_access_key(request: RotationRequest):
    """
    Rotate a compromised AWS IAM access key.
    
    This endpoint:
    1. Validates the access key exists
    2. Fetches and classifies attached IAM policies
    3. Creates a new access key
    4. Deactivates the old key
    5. Deletes the old key
    6. Logs all metadata for audit trail
    """
    try:
        logger.info(
            f"Rotation request received for user={request.iam_user}, "
            f"incident_id={request.incident_id}"
        )
        
        # Execute rotation
        result = await rotation_service.rotate_key(request)
        
        logger.info(
            f"✅ Rotation completed: incident_id={request.incident_id}, "
            f"new_key={result.new_key_id}"
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        logger.error(f"❌ Permission error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient IAM permissions"
        )
    except Exception as e:
        logger.error(f"❌ Rotation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rotation failed: {str(e)}"
        )


@router.get("/audit/{incident_id}")
async def get_audit_log(incident_id: str):
    """
    Retrieve audit log for a specific incident.
    """
    try:
        log = await rotation_service.get_audit_log(incident_id)
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No audit log found for incident {incident_id}"
            )
        return log
    except Exception as e:
        logger.error(f"❌ Failed to retrieve audit log: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/user/{iam_user}/keys")
async def get_user_keys(iam_user: str):
    """
    Get all access keys for a specific IAM user (with age analysis).
    """
    try:
        keys_info = await rotation_service.analyze_user_keys(iam_user)
        return keys_info
    except Exception as e:
        logger.error(f"❌ Failed to analyze user keys: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
