"""
Mapping of SecretLens detection rule IDs to service names and categories.
Used to classify and route detected secrets through the remediation engine.
"""
from typing import Dict, Optional
from enum import Enum


class SecretCategory(str, Enum):
    """Categories of detected secrets"""
    CLOUD_PROVIDER = "cloud_provider"  # AWS, GCP, Azure
    API_KEY = "api_key"  # Third-party service keys
    CRYPTO_KEY = "crypto_key"  # Encryption keys, tokens
    PASSWORD = "password"  # Generic passwords
    DEPENDENCY = "dependency"  # Package manager tokens
    CODE_EXECUTION = "code_execution"  # Dangerous code patterns
    PERFORMANCE_ISSUE = "performance_issue"  # Code quality


# Comprehensive mapping of rule IDs from SecretLens
RULE_ID_MAPPING: Dict[str, Dict[str, str]] = {
    # Cloud Providers - CRITICAL
    "SEC-001": {
        "service": "aws",
        "display_name": "AWS Access Key",
        "category": SecretCategory.CLOUD_PROVIDER,
        "risk_level": "critical",
    },
    "SEC-017": {
        "service": "aws",
        "display_name": "AWS Secret Access Key",
        "category": SecretCategory.CLOUD_PROVIDER,
        "risk_level": "critical",
    },
    
    # Generic API Keys - HIGH
    "SEC-002": {
        "service": "generic_api",
        "display_name": "Generic API Key",
        "category": SecretCategory.API_KEY,
        "risk_level": "high",
    },
    "SEC-003": {
        "service": "generic_api",
        "display_name": "API Key Pattern",
        "category": SecretCategory.API_KEY,
        "risk_level": "high",
    },
    
    # Third-Party Services - HIGH
    "SEC-004": {
        "service": "google",
        "display_name": "Google API Key",
        "category": SecretCategory.API_KEY,
        "risk_level": "high",
    },
    "SEC-005": {
        "service": "stripe",
        "display_name": "Stripe API Key",
        "category": SecretCategory.API_KEY,
        "risk_level": "high",
    },
    "SEC-006": {
        "service": "sendgrid",
        "display_name": "SendGrid API Key",
        "category": SecretCategory.API_KEY,
        "risk_level": "high",
    },
    "SEC-007": {
        "service": "slack",
        "display_name": "Slack Webhook",
        "category": SecretCategory.API_KEY,
        "risk_level": "high",
    },
    "SEC-008": {
        "service": "twilio",
        "display_name": "Twilio API Key",
        "category": SecretCategory.API_KEY,
        "risk_level": "high",
    },
    "SEC-009": {
        "service": "cloudflare",
        "display_name": "Cloudflare API Key",
        "category": SecretCategory.API_KEY,
        "risk_level": "high",
    },
    "SEC-010": {
        "service": "github",
        "display_name": "GitHub Token",
        "category": SecretCategory.CRYPTO_KEY,
        "risk_level": "high",
    },
    "SEC-011": {
        "service": "openai",
        "display_name": "OpenAI API Key",
        "category": SecretCategory.API_KEY,
        "risk_level": "high",
    },
    "SEC-012": {
        "service": "anthropic",
        "display_name": "Anthropic API Key",
        "category": SecretCategory.API_KEY,
        "risk_level": "high",
    },
    
    # Passwords - HIGH
    "SEC-013": {
        "service": "password",
        "display_name": "Hardcoded Password",
        "category": SecretCategory.PASSWORD,
        "risk_level": "high",
    },
    
    # Cryptographic Keys - CRITICAL
    "SEC-014": {
        "service": "private_key",
        "display_name": "Private Key (RSA/EC/OpenSSH)",
        "category": SecretCategory.CRYPTO_KEY,
        "risk_level": "critical",
    },
    "SEC-015": {
        "service": "jwt_token",
        "display_name": "JWT Token",
        "category": SecretCategory.CRYPTO_KEY,
        "risk_level": "high",
    },
    
    # SQL and Security Patterns - CRITICAL
    "SEC-016": {
        "service": "sql_injection",
        "display_name": "SQL Injection Pattern",
        "category": SecretCategory.CODE_EXECUTION,
        "risk_level": "critical",
    },
    
    # Code Execution - CRITICAL
    "AST-001": {
        "service": "python_eval",
        "display_name": "Python eval() Usage",
        "category": SecretCategory.CODE_EXECUTION,
        "risk_level": "critical",
    },
    "AST-002": {
        "service": "python_exec",
        "display_name": "Python exec() Usage",
        "category": SecretCategory.CODE_EXECUTION,
        "risk_level": "critical",
    },
    "AST-003": {
        "service": "javascript_eval",
        "display_name": "JavaScript eval() Usage",
        "category": SecretCategory.CODE_EXECUTION,
        "risk_level": "critical",
    },
    
    # Weak Cryptography - MEDIUM
    "AST-004": {
        "service": "weak_crypto",
        "display_name": "Weak Cryptographic Algorithm",
        "category": SecretCategory.CRYPTO_KEY,
        "risk_level": "medium",
    },
    
    # Performance Issues - LOW
    "PERF-001": {
        "service": "performance",
        "display_name": "Synchronous File Operations",
        "category": SecretCategory.PERFORMANCE_ISSUE,
        "risk_level": "low",
    },
}


def get_service_from_rule(rule_id: str) -> Optional[str]:
    """
    Get the service type from a rule ID.
    
    Args:
        rule_id: The SecretLens rule ID (e.g., "SEC-001")
        
    Returns:
        Service name string, or None if rule not found
        
    Example:
        >>> get_service_from_rule("SEC-001")
        "aws"
    """
    if rule_id in RULE_ID_MAPPING:
        return RULE_ID_MAPPING[rule_id]["service"]
    return None


def get_risk_level_from_rule(rule_id: str) -> str:
    """
    Get the risk level from a rule ID.
    
    Args:
        rule_id: The SecretLens rule ID
        
    Returns:
        Risk level string (critical, high, medium, low)
    """
    if rule_id in RULE_ID_MAPPING:
        return RULE_ID_MAPPING[rule_id]["risk_level"]
    return "medium"  # Default if unknown


def get_display_name(rule_id: str) -> str:
    """
    Get the human-readable display name for a rule.
    
    Args:
        rule_id: The SecretLens rule ID
        
    Returns:
        Display name string
    """
    if rule_id in RULE_ID_MAPPING:
        return RULE_ID_MAPPING[rule_id]["display_name"]
    return f"Unknown Secret Type ({rule_id})"


def get_category(rule_id: str) -> SecretCategory:
    """
    Get the category of a secret type.
    
    Args:
        rule_id: The SecretLens rule ID
        
    Returns:
        SecretCategory enum value
    """
    if rule_id in RULE_ID_MAPPING:
        return RULE_ID_MAPPING[rule_id]["category"]
    return SecretCategory.API_KEY  # Default


def is_critical_secret(rule_id: str) -> bool:
    """
    Check if a detected secret is critical severity.
    
    Args:
        rule_id: The SecretLens rule ID
        
    Returns:
        True if risk level is critical or code execution
    """
    risk_level = get_risk_level_from_rule(rule_id)
    category = get_category(rule_id)
    return risk_level == "critical" or category == SecretCategory.CODE_EXECUTION
