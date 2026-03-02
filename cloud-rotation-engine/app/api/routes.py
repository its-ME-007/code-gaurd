"""
API routes for Cloud Key Rotation Engine
"""
from fastapi import APIRouter, HTTPException
from app.api.schemas import RotationRequest, RotationResponse
from app.services.rotation_service import RotationService

router = APIRouter(prefix="/api/v1", tags=["rotation"])

rotation_service = RotationService()


@router.post("/rotate", response_model=RotationResponse)
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
        
        return result
        
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
    return {
        "incident_id": incident_id,
        "status": "not_implemented",
        "message": "Audit log retrieval not yet implemented"
    }


@router.get("/user/{iam_user}/keys")
async def analyze_user_keys(iam_user: str):
    """Analyze access keys for a specific IAM user"""
    return {
        "iam_user": iam_user,
        "status": "not_implemented",
        "message": "Key analysis not yet implemented"
    }
