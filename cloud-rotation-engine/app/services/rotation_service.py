"""
Core rotation service - orchestrates the key rotation workflow
"""
import time
import boto3
from datetime import datetime
from typing import Dict, Any

from app.api.schemas import RotationRequest, RotationResponse, RotationAuditLog
from app.services.iam_validator import IAMValidator
from app.services.policy_classifier import PolicyClassifier
from app.core.logging_config import setup_logging


logger = setup_logging()


class RotationService:
    """Manages deterministic key rotation lifecycle"""
    
    def __init__(self):
        self.iam_client = boto3.client("iam")
        self.validator = IAMValidator()
        self.classifier = PolicyClassifier()
        self.audit_logs: Dict[str, RotationAuditLog] = {}
    
    async def rotate_key(self, request: RotationRequest) -> RotationResponse:
        """
        Execute deterministic key rotation workflow.
        
        Steps:
        1. Validate key exists and belongs to user
        2. Fetch and classify attached policies
        3. Create new access key
        4. Deactivate old key
        5. Delete old key
        6. Log audit metadata
        """
        start_time = time.time()
        
        try:
            # Step 1: Validate key
            logger.info(f"🔍 Validating key {request.access_key_id}...")
            is_valid = await self.validator.validate_key(
                request.iam_user,
                request.access_key_id
            )
            if not is_valid:
                raise ValueError(f"Key {request.access_key_id} not found for user {request.iam_user}")
            
            # Step 2: Fetch and classify policies
            logger.info(f"📋 Fetching policies for {request.iam_user}...")
            policy_level = await self.validator.get_policy_level(request.iam_user)
            
            # Step 3: Create new access key
            logger.info(f"🔐 Creating new access key for {request.iam_user}...")
            new_key_response = self.iam_client.create_access_key(
                UserName=request.iam_user
            )
            new_key_id = new_key_response["AccessKey"]["AccessKeyId"]
            new_key_secret = new_key_response["AccessKey"]["SecretAccessKey"]
            logger.info(f"✅ New key created: {new_key_id}")
            
            # Step 4: Deactivate old key
            logger.info(f"⏸️ Deactivating old key {request.access_key_id}...")
            self.iam_client.update_access_key(
                UserName=request.iam_user,
                AccessKeyId=request.access_key_id,
                Status="Inactive"
            )
            logger.info(f"✅ Old key deactivated")
            
            # Step 5: Delete old key
            logger.info(f"🗑️ Deleting old key {request.access_key_id}...")
            self.iam_client.delete_access_key(
                UserName=request.iam_user,
                AccessKeyId=request.access_key_id
            )
            logger.info(f"✅ Old key deleted")
            
            # Calculate rotation time
            rotation_time_ms = int((time.time() - start_time) * 1000)
            
            # Step 6: Log audit metadata
            audit_log = RotationAuditLog(
                incident_id=request.incident_id,
                old_key=request.access_key_id,
                new_key=new_key_id,
                rotation_timestamp=datetime.utcnow(),
                iam_user=request.iam_user,
                policy_level=policy_level,
                rotation_time_ms=rotation_time_ms,
                status="success"
            )
            self.audit_logs[request.incident_id] = audit_log
            logger.info(f"📝 Audit log recorded for {request.incident_id}")
            
            # Return response
            return RotationResponse(
                status="success",
                rotation_completed=True,
                iam_user=request.iam_user,
                old_key_deactivated=True,
                new_key_id=new_key_id,
                policy_level=policy_level,
                rotation_time_ms=rotation_time_ms
            )
            
        except Exception as e:
            logger.error(f"❌ Rotation failed: {str(e)}")
            raise
    
    async def get_audit_log(self, incident_id: str) -> RotationAuditLog:
        """Retrieve audit log by incident ID"""
        return self.audit_logs.get(incident_id)
    
    async def analyze_user_keys(self, iam_user: str) -> Dict[str, Any]:
        """Analyze all keys for a user, including age"""
        try:
            response = self.iam_client.list_access_keys(UserName=iam_user)
            keys = response.get("AccessKeyMetadata", [])
            
            now = datetime.utcnow()
            keys_analysis = []
            
            for key in keys:
                age_days = (now - key["CreateDate"].replace(tzinfo=None)).days
                keys_analysis.append({
                    "access_key_id": key["AccessKeyId"],
                    "status": key["Status"],
                    "create_date": key["CreateDate"].isoformat(),
                    "age_days": age_days
                })
            
            return {
                "iam_user": iam_user,
                "total_keys": len(keys),
                "keys": keys_analysis
            }
        except Exception as e:
            logger.error(f"❌ Failed to analyze keys: {str(e)}")
            raise
