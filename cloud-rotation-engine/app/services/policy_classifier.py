"""
Policy classifier - determines privilege level from IAM policies
"""
from typing import List


class PolicyClassifier:
    """Deterministically classifies IAM privilege levels"""
    
    def __init__(self):
        """Initialize policy classifier with risk mappings"""
        # Critical policies
        self.critical_policies = [
            "AdministratorAccess",
            "IAMFullAccess",
            "SecurityAudit"
        ]
        
        # High risk policies
        self.high_risk_policies = [
            "PowerUserAccess",
            "EC2FullAccess",
            "RDSFullAccess",
            "S3FullAccess"
        ]
        
        # Medium risk policies
        self.medium_risk_policies = [
            "ReadOnlyAccess",
            "CloudWatchLogsFullAccess"
        ]
        
        # Risk level mapping
        self.risk_mapping = {
            "AdministratorAccess": "critical",
            "PowerUserAccess": "high",
            "Custom": "medium",
            "None": "low"
        }
    
    def classify_policies(self, attached_policies: List[str]) -> str:
        """
        Classify IAM privilege level based on attached policies
        
        Returns: "AdministratorAccess", "PowerUserAccess", "Custom", or "None"
        """
        if not attached_policies:
            return "None"
        
        # Check for critical policies
        for policy in attached_policies:
            if policy in self.critical_policies:
                return "AdministratorAccess"
        
        # Check for high-risk policies
        for policy in attached_policies:
            if policy in self.high_risk_policies:
                return "PowerUserAccess"
        
        # Check for medium-risk or custom policies
        for policy in attached_policies:
            if policy in self.medium_risk_policies or not policy.startswith("AWS"):
                return "Custom"
        
        return "Custom"
    
    def get_risk_level(self, policy_level: str) -> str:
        """Map policy level to risk level"""
        return self.risk_mapping.get(policy_level, "medium")
    
    def should_rotate(self, policy_level: str, reported_risk: str) -> bool:
        """
        Determine if key should be rotated based on policy level
        and reported risk level.
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
            "None": 1
        }
        
        reported_score = risk_score.get(reported_risk.lower(), 1)
        policy_score = policy_risk_score.get(policy_level, 1)
        
        # Rotate if either score is high enough
        return max(reported_score, policy_score) >= 3
