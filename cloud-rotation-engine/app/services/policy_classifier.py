"""
Policy classifier - determines privilege level from IAM policies
"""
from typing import Literal
from app.core.logging_config import setup_logging


logger = setup_logging()


class PolicyClassifier:
    """Deterministically classifies IAM privilege levels"""
    
    # Policy name mappings to privilege levels
    POLICY_MAPPINGS = {
        "AdministratorAccess": "AdministratorAccess",
        "PowerUserAccess": "PowerUserAccess",
        "SecurityAudit": "Custom",
        "ReadOnlyAccess": "Custom",
    }
    
    RISK_MAPPING = {
        "AdministratorAccess": "Critical",
        "PowerUserAccess": "High",
        "Custom": "Medium",
        "Unknown": "Low"
    }
    
    def classify_policy(self, policy_name: str) -> str:
        """
        Classify a policy name to privilege level.
        
        Returns one of:
        - AdministratorAccess (Risk: Critical)
        - PowerUserAccess (Risk: High)
        - Custom (Risk: Medium)
        - Unknown (Risk: Low)
        """
        # Direct match
        if policy_name in self.POLICY_MAPPINGS:
            return self.POLICY_MAPPINGS[policy_name]
        
        # Keyword matching
        policy_lower = policy_name.lower()
        
        if "admin" in policy_lower:
            return "AdministratorAccess"
        elif "poweruser" in policy_lower:
            return "PowerUserAccess"
        elif any(keyword in policy_lower for keyword in ["custom", "inline"]):
            return "Custom"
        
        return "Unknown"
    
    def get_risk_level(self, policy_level: str) -> str:
        """Get risk level from privilege level"""
        return self.RISK_MAPPING.get(policy_level, "Low")
    
    def should_rotate(self, policy_level: str, reported_risk: str) -> bool:
        """
        Determine if key should be rotated based on policy level
        and reported risk level.
        
        Always rotates if:
        - Policy level is AdministratorAccess
        - Policy level is PowerUserAccess
        - Reported risk is critical or high
        """
        risk_score = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }
        
        policy_risk_score = {
            "AdministratorAccess": 4,
            "PowerUserAccess": 3,
            "Custom": 2,
            "Unknown": 1
        }
        
        reported_score = risk_score.get(reported_risk.lower(), 1)
        policy_score = policy_risk_score.get(policy_level, 1)
        
        # Rotate if either score is high enough
        return max(reported_score, policy_score) >= 3
