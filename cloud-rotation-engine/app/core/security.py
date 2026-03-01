"""
Security utilities for Cloud Key Rotation Engine
"""
import hashlib
import hmac
from typing import Optional

from app.core.config import settings
from app.core.logging_config import setup_logging


logger = setup_logging()


def verify_api_key(provided_key: Optional[str]) -> bool:
    """
    Verify provided API key against configured key.
    
    Returns True if key is valid, False otherwise.
    """
    if not settings.API_KEY_ENABLED:
        return True
    
    if not provided_key:
        logger.warning("❌ API key missing from request")
        return False
    
    # Constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(provided_key, settings.API_KEY)
    
    if not is_valid:
        logger.warning("❌ Invalid API key provided")
    
    return is_valid


def hash_secret(secret: str) -> str:
    """
    Hash a secret value (e.g., AWS secret key for storage).
    
    Never store actual secrets - use this for audit logs.
    """
    return hashlib.sha256(secret.encode()).hexdigest()


def mask_key(key: str, show_chars: int = 4) -> str:
    """
    Mask an access key for display purposes.
    
    Example: AKIA... -> AKIA***...***XYZW
    """
    if len(key) <= show_chars * 2:
        return key
    
    return f"{key[:show_chars]}***...***{key[-show_chars:]}"
