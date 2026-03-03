"""
Core rotation service - orchestrates the key rotation workflow
"""
import time
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError
from app.core.config import settings
from app.services.iam_validator import IAMValidator
from app.services.policy_classifier import PolicyClassifier
from app.services.audit_service import AuditService
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
        self.audit_service = AuditService()
    
    def _update_env_file(self, new_key_id: str, new_secret_key: str):
        """Automatically update .env file with new credentials"""
        # Get the project root directory (where .env is located)
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        
        print(f"🔍 Looking for .env at: {env_path}")
        
        try:
            # Read existing .env
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            print(f"📄 Read {len(lines)} lines from .env")
            
            # Update credentials
            updated_lines = []
            demo_key_updated = False
            demo_secret_updated = False
            
            for line in lines:
                if line.startswith('DEMO_ACCESS_KEY_ID='):
                    updated_lines.append(f'DEMO_ACCESS_KEY_ID={new_key_id}\n')
                    demo_key_updated = True
                    print(f"✅ Updated DEMO_ACCESS_KEY_ID")
                elif line.startswith('DEMO_SECRET_ACCESS_KEY='):
                    updated_lines.append(f'DEMO_SECRET_ACCESS_KEY={new_secret_key}\n')
                    demo_secret_updated = True
                    print(f"✅ Updated DEMO_SECRET_ACCESS_KEY")
                else:
                    updated_lines.append(line)
            
            # Write back to .env
            with open(env_path, 'w') as f:
                f.writelines(updated_lines)
            
            print(f"💾 Saved updated .env file")
            print(f"   Key updated: {demo_key_updated}")
            print(f"   Secret updated: {demo_secret_updated}")
            
            return demo_key_updated and demo_secret_updated
            
        except FileNotFoundError:
            print(f"❌ .env file not found at {env_path}")
            return False
        except Exception as e:
            print(f"❌ Failed to update .env: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def rotate_key(self, iam_user: str, access_key_id: str, incident_id: str, risk_level: str) -> dict:
        """Execute deterministic 4-step key rotation"""
        
        rotation_start = datetime.utcnow()
        timestamp = rotation_start.isoformat()
        
        # Log incident start
        if settings.audit_logging_enabled:
            self.audit_service.log_incident({
                "incident_id": incident_id,
                "iam_user": iam_user,
                "access_key_id": mask_key(access_key_id),
                "risk_level": risk_level,
                "rotation_status": "started",
                "policy_level": "pending",
                "timestamp": timestamp
            })
        
        try:
            # Step 1: Validate key exists
            validation = await self.validator.validate_key(iam_user, access_key_id)
            if not validation.get("valid"):
                if settings.audit_logging_enabled:
                    self.audit_service.log_incident({
                        "incident_id": incident_id,
                        "iam_user": iam_user,
                        "access_key_id": mask_key(access_key_id),
                        "risk_level": risk_level,
                        "rotation_status": "failed",
                        "policy_level": "unknown",
                        "timestamp": timestamp,
                        "error_message": validation.get("error")
                    })
                
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
                if settings.audit_logging_enabled:
                    self.audit_service.log_incident({
                        "incident_id": incident_id,
                        "iam_user": iam_user,
                        "access_key_id": mask_key(access_key_id),
                        "risk_level": risk_level,
                        "rotation_status": "dry_run",
                        "policy_level": policy_level,
                        "timestamp": timestamp
                    })
                
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
            
            print(f"🔄 Starting rotation for {iam_user}...")
            
            # Step 3: Create new access key
            print(f"📝 Creating new access key...")
            new_key_response = self.iam_client.create_access_key(UserName=iam_user)
            new_key_id = new_key_response['AccessKey']['AccessKeyId']
            new_secret_key = new_key_response['AccessKey']['SecretAccessKey']
            print(f"✅ Created new key: {new_key_id}")
            
            # Step 4: Deactivate old key
            print(f"🔒 Deactivating old key: {access_key_id}")
            self.iam_client.update_access_key(
                UserName=iam_user,
                AccessKeyId=access_key_id,
                Status='Inactive'
            )
            print(f"✅ Old key deactivated")
            
            # Step 5: Delete old key
            print(f"🗑️  Deleting old key: {access_key_id}")
            self.iam_client.delete_access_key(
                UserName=iam_user,
                AccessKeyId=access_key_id
            )
            print(f"✅ Old key deleted")
            
            # Step 6: Auto-save new credentials to .env 🔥
            print(f"💾 Saving new credentials to .env...")
            env_updated = self._update_env_file(new_key_id, new_secret_key)
            
            rotation_time_ms = int((datetime.utcnow() - rotation_start).total_seconds() * 1000)
            
            # Log successful rotation
            if settings.audit_logging_enabled:
                self.audit_service.log_incident({
                    "incident_id": incident_id,
                    "iam_user": iam_user,
                    "access_key_id": mask_key(access_key_id),
                    "risk_level": risk_level,
                    "rotation_status": "completed",
                    "policy_level": policy_level,
                    "timestamp": timestamp,
                    "rotation_time_ms": rotation_time_ms,
                    "old_key_deactivated": True,
                    "new_key_id": mask_key(new_key_id)
                })
            
            response = {
                "status": "success",
                "rotation_completed": True,
                "iam_user": iam_user,
                "old_key_id": mask_key(access_key_id),
                "old_key_deactivated": True,
                "new_key_id": new_key_id,  # Full key ID (unmasked)
                "new_secret_key": new_secret_key[:10] + "***" + new_secret_key[-4:],  # Partially masked
                "credentials_saved": env_updated,
                "saved_location": ".env file" if env_updated else "manual_save_required",
                "policy_level": policy_level,
                "rotation_time_ms": rotation_time_ms,
                "incident_id": incident_id,
                "risk_level": risk_level,
                "timestamp": timestamp,
                "message": "✅ Rotation complete! New credentials saved to .env" if env_updated else "⚠️ Rotation complete but .env update failed"
            }
            
            print(f"🎉 Rotation completed successfully!")
            return response
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            print(f"❌ AWS Error: {error_code} - {error_msg}")
            
            if settings.audit_logging_enabled:
                self.audit_service.log_incident({
                    "incident_id": incident_id,
                    "iam_user": iam_user,
                    "access_key_id": mask_key(access_key_id),
                    "risk_level": risk_level,
                    "rotation_status": "failed",
                    "policy_level": "unknown",
                    "timestamp": timestamp,
                    "error_message": f"{error_code}: {error_msg}"
                })
            
            return {
                "status": "error",
                "rotation_completed": False,
                "reason": error_code,
                "message": error_msg,
                "incident_id": incident_id
            }
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            
            if settings.audit_logging_enabled:
                self.audit_service.log_incident({
                    "incident_id": incident_id,
                    "iam_user": iam_user,
                    "access_key_id": mask_key(access_key_id),
                    "risk_level": risk_level,
                    "rotation_status": "failed",
                    "policy_level": "unknown",
                    "timestamp": timestamp,
                    "error_message": str(e)
                })
            
            return {
                "status": "error",
                "rotation_completed": False,
                "reason": "unexpected_error",
                "message": str(e),
                "incident_id": incident_id
            }
