"""
Utility module for hashing secrets for audit purposes.
Implements SHA256 hashing to create secure identifiers for secrets
without storing the raw credential values.
"""
import hashlib
from typing import Optional


def hash_secret(secret_value: str, salt: Optional[str] = None) -> str:
    """
    Generate a SHA256 hash of a secret value for audit logging.
    
    The hash is used to:
    - Detect repeated leaks
    - Correlate incidents
    - Track remediation progress
    
    WITHOUT storing the raw secret.
    
    Args:
        secret_value: The raw secret to hash
        salt: Optional salt to add uniqueness (recommend using repo name or project id)
        
    Returns:
        Hexadecimal SHA256 hash of the secret
        
    Example:
        >>> secret = "my-secret-api-key-12345"
        >>> hash_value = hash_secret(secret, salt="project-alpha")
        >>> print(hash_value)
        "a1b2c3d4e5f6..."
    """
    if not secret_value:
        raise ValueError("Secret value cannot be empty")
    
    combined = secret_value
    if salt:
        combined = f"{salt}:{secret_value}"
    
    return hashlib.sha256(combined.encode()).hexdigest()


def hash_secret_with_repo(secret_value: str, repo_name: str) -> str:
    """
    Generate a hash using repo name as salt for better incident correlation.
    
    Args:
        secret_value: The raw secret to hash
        repo_name: Repository name to use as salt
        
    Returns:
        Hexadecimal SHA256 hash
    """
    return hash_secret(secret_value, salt=repo_name)


def verify_secret_hash(secret_value: str, secret_hash: str, salt: Optional[str] = None) -> bool:
    """
    Verify that a secret matches a given hash.
    
    Args:
        secret_value: The raw secret to verify
        secret_hash: The hash to check against
        salt: Optional salt (must match original)
        
    Returns:
        True if secret matches the hash, False otherwise
    """
    computed_hash = hash_secret(secret_value, salt=salt)
    return computed_hash == secret_hash
