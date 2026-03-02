"""
IAM validation service - confirms key ownership and retrieves policies
"""
import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError
from app.core.config import settings
from app.core.security import mask_key

class IAMValidator:
    def __init__(self):
        """Initialize IAM client with explicit credentials from settings"""
        self.iam_client = boto3.client(
            'iam',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
    
    async def validate_key(self, iam_user: str, access_key_id: str) -> dict:
        """Validate that access key exists and belongs to IAM user"""
        try:
            # First, verify the user exists
            try:
                self.iam_client.get_user(UserName=iam_user)
            except self.iam_client.exceptions.NoSuchEntityException:
                return {
                    "valid": False,
                    "error": f"IAM user '{iam_user}' does not exist"
                }
            
            # List all access keys for the user
            response = self.iam_client.list_access_keys(UserName=iam_user)
            
            # AWS returns AccessKeyMetadata, not AccessKeys
            access_keys = response.get('AccessKeyMetadata', [])
            
            if not access_keys:
                return {
                    "valid": False,
                    "error": f"No access keys found for user {iam_user}"
                }
            
            # Check if the key exists
            key_exists = any(
                key['AccessKeyId'] == access_key_id 
                for key in access_keys
            )
            
            if not key_exists:
                return {
                    "valid": False,
                    "error": f"Access key {mask_key(access_key_id)} not found for user {iam_user}"
                }
            
            # Get key status
            key_status = next(
                (key['Status'] for key in access_keys if key['AccessKeyId'] == access_key_id),
                None
            )
            
            return {
                "valid": True,
                "iam_user": iam_user,
                "access_key_id": access_key_id,
                "key_status": key_status
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            return {
                "valid": False,
                "error": f"AWS Error ({error_code}): {error_msg}"
            }
        except NoCredentialsError:
            return {
                "valid": False,
                "error": "AWS credentials not configured"
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }
    
    async def get_user_policies(self, iam_user: str) -> dict:
        """Get attached policies for IAM user"""
        try:
            attached_policies = self.iam_client.list_attached_user_policies(UserName=iam_user)
            inline_policies = self.iam_client.list_user_policies(UserName=iam_user)
            
            return {
                "attached_policies": [p['PolicyName'] for p in attached_policies.get('AttachedPolicies', [])],
                "inline_policies": inline_policies.get('PolicyNames', [])
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            return {
                "error": f"AWS Error ({error_code}): {error_msg}",
                "attached_policies": [],
                "inline_policies": []
            }
        except Exception as e:
            return {
                "error": f"Error retrieving policies: {str(e)}",
                "attached_policies": [],
                "inline_policies": []
            }
