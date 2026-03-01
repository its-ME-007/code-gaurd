"""
IAM validation service - confirms key ownership and retrieves policies
"""
import boto3
from typing import List, Optional

from app.services.policy_classifier import PolicyClassifier
from app.core.logging_config import setup_logging


logger = setup_logging()


class IAMValidator:
    """Validates IAM keys and retrieves policy information"""
    
    def __init__(self):
        self.iam_client = boto3.client("iam")
        self.classifier = PolicyClassifier()
    
    async def validate_key(self, iam_user: str, access_key_id: str) -> bool:
        """
        Confirm that access key exists and belongs to IAM user.
        
        Uses: iam.list_access_keys()
        """
        try:
            response = self.iam_client.list_access_keys(UserName=iam_user)
            keys = response.get("AccessKeyMetadata", [])
            
            for key in keys:
                if key["AccessKeyId"] == access_key_id:
                    logger.info(f"✅ Key {access_key_id} validated for user {iam_user}")
                    return True
            
            logger.warning(f"❌ Key {access_key_id} not found for user {iam_user}")
            return False
            
        except self.iam_client.exceptions.NoSuchEntityException:
            logger.error(f"❌ User {iam_user} does not exist")
            raise ValueError(f"IAM user {iam_user} not found")
        except Exception as e:
            logger.error(f"❌ Validation error: {str(e)}")
            raise
    
    async def get_policy_level(self, iam_user: str) -> str:
        """
        Fetch attached policies and determine privilege level.
        
        Uses:
        - iam.list_attached_user_policies()
        - iam.list_user_policies()
        
        Returns: One of [AdministratorAccess, PowerUserAccess, Custom, Unknown]
        """
        try:
            # Fetch attached managed policies
            attached_response = self.iam_client.list_attached_user_policies(
                UserName=iam_user
            )
            attached_policies = attached_response.get("AttachedPolicies", [])
            
            # Fetch inline policies
            inline_response = self.iam_client.list_user_policies(UserName=iam_user)
            inline_policies = inline_response.get("PolicyNames", [])
            
            # Classify based on attached policies first
            for policy in attached_policies:
                policy_name = policy.get("PolicyName", "")
                level = self.classifier.classify_policy(policy_name)
                if level != "Unknown":
                    logger.info(
                        f"📊 User {iam_user} has policy: {policy_name} "
                        f"-> Risk Level: {level}"
                    )
                    return level
            
            # If no managed policy matches, check inline
            if inline_policies:
                logger.info(
                    f"📊 User {iam_user} has {len(inline_policies)} inline policies"
                )
                return "Custom"
            
            # Default unknown
            logger.warning(f"⚠️ Could not classify policy level for {iam_user}")
            return "Unknown"
            
        except Exception as e:
            logger.error(f"❌ Error fetching policies: {str(e)}")
            raise
    
    async def get_attached_policies(self, iam_user: str) -> List[dict]:
        """Get all attached policies for a user"""
        try:
            response = self.iam_client.list_attached_user_policies(
                UserName=iam_user
            )
            return response.get("AttachedPolicies", [])
        except Exception as e:
            logger.error(f"❌ Error retrieving attached policies: {str(e)}")
            raise
