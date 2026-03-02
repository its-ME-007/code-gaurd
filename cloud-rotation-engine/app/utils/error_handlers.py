"""
Error handling utilities
"""
from typing import Dict, Any, Optional

# from app.core.logging_config import setup_logging


# logger = setup_logging()


class RotationError(Exception):
    """Base exception for rotation errors"""
    pass


class ValidationError(RotationError):
    """Raised when validation fails"""
    pass


class PermissionError(RotationError):
    """Raised when IAM permissions are insufficient"""
    pass


class KeyNotFoundError(RotationError):
    """Raised when key cannot be found"""
    pass


def create_error_response(
    reason: str,
    details: Optional[str] = None,
    error_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create structured error response.
    
    Args:
        reason: Human-readable error reason
        details: Additional technical details
        error_code: AWS error code if applicable
    
    Returns:
        Dictionary suitable for API response
    """
    response = {
        "status": "error",
        "reason": reason,
        "rotation_completed": False,
    }
    
    if details:
        response["details"] = details
    
    if error_code:
        response["error_code"] = error_code
    
    return response


def handle_aws_error(aws_error: Exception) -> Dict[str, Any]:
    """
    Handle AWS boto3 exceptions and create appropriate error response.
    
    Args:
        aws_error: Exception from boto3
    
    Returns:
        Structured error response
    """
    error_code = aws_error.response.get("Error", {}).get("Code", "Unknown") if hasattr(aws_error, "response") else "Unknown"
    error_message = str(aws_error)
    
    # logger.error(f"AWS Error [{error_code}]: {error_message}")
    
    # Map AWS errors to appropriate responses
    error_map = {
        "NoSuchEntity": ("User or key not found", "KEY_NOT_FOUND"),
        "AccessDenied": ("Insufficient IAM permissions", "ACCESS_DENIED"),
        "InvalidInput": ("Invalid parameter provided", "INVALID_INPUT"),
        "ServiceFailure": ("AWS service is unavailable", "SERVICE_FAILURE"),
        "Throttling": ("Rate limit exceeded, please retry", "RATE_LIMIT"),
    }
    
    reason, mapped_code = error_map.get(error_code, (error_message, error_code))
    
    return create_error_response(
        reason=reason,
        details=error_message,
        error_code=mapped_code
    )
