"""
API routes for Cloud Key Rotation Engine
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.api.schemas import RotationRequest
from app.services.rotation_service import RotationService

router = APIRouter(prefix="/api/v1", tags=["rotation"])

rotation_service = RotationService()


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
