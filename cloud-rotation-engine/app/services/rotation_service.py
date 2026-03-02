"""
Core rotation service - orchestrates the key rotation workflow
"""
import time
import boto3
from datetime import datetime
from botocore.exceptions import ClientError
from app.core.config import settings
from app.services.iam_validator import IAMValidator
from app.services.policy_classifier import PolicyClassifier
from app.core.security import mask_key


class RotationService:
    def __init__(self):
        """Initialize rotation service with explicit AWS credentials"""
        self.iam_client = boto3.client(
            'iam',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        self.validator = IAMValidator()
        self.classifier = PolicyClassifier()
    
    async def rotate_key(self, iam_user: str, access_key_id: str, incident_id: str, risk_level: str) -> dict:
        """Execute deterministic 4-step key rotation"""
        
        rotation_start = datetime.utcnow()
        
        try:
            # Step 1: Validate key exists
            validation = await self.validator.validate_key(iam_user, access_key_id)
            if not validation.get("valid"):
                return {
                    "status": "error",
                    "rotation_completed": False,
                    "reason": validation.get("error", "Key validation failed")
                }
            
            # Step 2: Get user policies
            policies_info = await self.validator.get_user_policies(iam_user)
            policy_level = self.classifier.classify_policies(
                policies_info.get("attached_policies", [])
            )
            
            if settings.dry_run:
                return {
                    "status": "success",
                    "rotation_completed": False,
                    "mode": "DRY_RUN",
                    "iam_user": iam_user,
                    "old_key": mask_key(access_key_id),
                    "policy_level": policy_level,
                    "incident_id": incident_id,
                    "message": "Dry run mode - no actual rotation performed"
                }
            
            # Step 3: Create new access key
            new_key_response = self.iam_client.create_access_key(UserName=iam_user)
            new_key_id = new_key_response['AccessKey']['AccessKeyId']
            
            # Step 4: Deactivate old key
            self.iam_client.update_access_key(
                UserName=iam_user,
                AccessKeyId=access_key_id,
                Status='Inactive'
            )
            
            # Step 5: Delete old key
            self.iam_client.delete_access_key(
                UserName=iam_user,
                AccessKeyId=access_key_id
            )
            
            rotation_time_ms = int((datetime.utcnow() - rotation_start).total_seconds() * 1000)
            
            return {
                "status": "success",
                "rotation_completed": True,
                "iam_user": iam_user,
                "old_key_deactivated": True,
                "new_key_id": mask_key(new_key_id),
                "policy_level": policy_level,
                "rotation_time_ms": rotation_time_ms,
                "incident_id": incident_id,
                "risk_level": risk_level
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            
            return {
                "status": "error",
                "rotation_completed": False,
                "reason": error_code,
                "message": error_msg,
                "incident_id": incident_id
            }
        except Exception as e:
            return {
                "status": "error",
                "rotation_completed": False,
                "reason": "unexpected_error",
                "message": str(e),
                "incident_id": incident_id
            }
