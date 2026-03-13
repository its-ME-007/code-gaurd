"""
AWS Secrets Manager service for secure secret storage and retrieval.

This module provides a centralized interface for:
- Storing secrets (JSON or simple string format) in AWS Secrets Manager
- Retrieving secrets with automatic format detection
- Managing secret metadata and versioning
- Classifying secret types (JSON vs simple key/token)
"""

import json
import boto3
from typing import Any, Dict, Optional, Union, Tuple
from datetime import datetime
from botocore.exceptions import ClientError, BotoCoreError
from app.core.config import settings


# Logging disabled for module testing


class SecretClassificationError(Exception):
    """Raised when secret classification fails"""
    pass


class SecretStorageError(Exception):
    """Raised when secret storage operations fail"""
    pass


class SecretRetrievalError(Exception):
    """Raised when secret retrieval operations fail"""
    pass


class DetectedSecretClassifier:
    """
    Classifies secrets into JSON or simple string format.
    Handles validation and type detection.
    """
    
    @staticmethod
    def is_json_secret(secret_value: str) -> bool:
        """
        Detect if secret is valid JSON.
        
        Args:
            secret_value: The secret value to classify
            
        Returns:
            bool: True if valid JSON, False otherwise
        """
        if not isinstance(secret_value, str):
            return False
        
        secret_value = secret_value.strip()
        
        # Check if it looks like JSON
        if not (secret_value.startswith('{') or secret_value.startswith('[')):
            return False
        
        try:
            json.loads(secret_value)
            return True
        except (json.JSONDecodeError, ValueError):
            return False
    
    @staticmethod
    def classify_secret(secret_value: str) -> Tuple[str, Any]:
        """
        Classify and parse secret into its appropriate format.
        
        Args:
            secret_value: The secret value to classify
            
        Returns:
            Tuple[str, Any]: (classification_type, parsed_value)
                            classification_type: 'json' or 'simple'
                            parsed_value: Original string or parsed JSON dict
                            
        Raises:
            SecretClassificationError: If classification fails
        """
        try:
            if DetectedSecretClassifier.is_json_secret(secret_value):
                parsed = json.loads(secret_value.strip())
                return ('json', parsed)
            else:
                return ('simple', secret_value.strip())
        except Exception as e:
            raise SecretClassificationError(
                f"Failed to classify secret: {str(e)}"
            )


class SecretsManagerService:
    """
    Service for storing and retrieving secrets from AWS Secrets Manager.
    
    Features:
    - Automatic secret classification (JSON vs simple)
    - Secure storage with metadata
    - Version tracking
    - Automatic format handling during retrieval
    """
    
    def __init__(self):
        """Initialize Secrets Manager client with AWS credentials"""
        try:
            self.client = boto3.client(
                'secretsmanager',
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
            print("✓ Secrets Manager client initialized")
        except Exception as e:
            print(f"✗ Failed to initialize Secrets Manager client: {e}")
            raise
    
    def store_secret(
        self,
        secret_id: str,
        secret_value: str,
        service_name: str,
        environment: str = "default",
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Store a secret in AWS Secrets Manager with automatic classification.
        
        The method automatically detects if the secret is JSON or a simple string
        and stores accordingly with proper metadata.
        
        Args:
            secret_id: Unique identifier for the secret (e.g., "codeguard/gemini/project-x")
            secret_value: The secret value (can be JSON or simple string)
            service_name: Name of the service (e.g., "gemini", "stripe", "aws")
            environment: Environment context (default: "default")
            description: Optional description of the secret
            tags: Optional dict of tags for organization
            
        Returns:
            Dict with keys:
                - status: "success" or "error"
                - secret_id: The stored secret ID
                - secret_type: "json" or "simple"
                - version_id: AWS secret version ID
                - timestamp: Storage timestamp
                - message: Descriptive message
                
        Raises:
            SecretStorageError: If storage operation fails
            
        Example:
            >>> service = SecretsManagerService()
            >>> result = service.store_secret(
            ...     secret_id="codeguard/gemini/project-x",
            ...     secret_value='{"api_key": "AIza...", "project_id": "xyz"}',
            ...     service_name="gemini"
            ... )
        """
        try:
            # Classify the secret
            secret_type, parsed_value = DetectedSecretClassifier.classify_secret(
                secret_value
            )
            print(f"🔍 Secret classified as: {secret_type}")
            
            # Build metadata
            metadata = {
                "service": service_name,
                "type": secret_type,
                "environment": environment,
                "managed_by": "codeguard-rotation-engine",
                "timestamp": datetime.utcnow().isoformat(),
                "original_format": secret_type
            }
            
            # Prepare the stored secret with metadata
            stored_secret = {
                "value": secret_value,  # Store original value as-is
                "metadata": metadata
            }
            
            secret_string = json.dumps(stored_secret, indent=2)
            
            # Prepare tags
            tags_list = [
                {"Key": "ManagedBy", "Value": "codeguard-rotation-engine"},
                {"Key": "Service", "Value": service_name},
                {"Key": "Environment", "Value": environment},
                {"Key": "SecretType", "Value": secret_type}
            ]
            
            if tags:
                for key, value in tags.items():
                    tags_list.append({"Key": key, "Value": value})
            
            # Try to update existing secret, create if doesn't exist
            try:
                response = self.client.update_secret(
                    SecretId=secret_id,
                    SecretString=secret_string,
                    Description=description or f"Managed secret for {service_name}"
                )
                operation = "updated"
                print(f"✓ Secret updated: {secret_id}")
            except self.client.exceptions.ResourceNotFoundException:
                response = self.client.create_secret(
                    Name=secret_id,
                    SecretString=secret_string,
                    Description=description or f"Managed secret for {service_name}",
                    Tags=tags_list
                )
                operation = "created"
                print(f"✓ Secret created: {secret_id}")
            
            return {
                "status": "success",
                "operation": operation,
                "secret_id": secret_id,
                "secret_type": secret_type,
                "version_id": response.get("VersionId"),
                "timestamp": metadata["timestamp"],
                "message": f"Secret {operation} successfully in AWS Secrets Manager"
            }
            
        except SecretClassificationError as e:
            print(f"✗ Secret classification error: {e}")
            raise SecretStorageError(f"Classification failed: {str(e)}")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            error_msg = e.response.get('Error', {}).get('Message')
            print(f"✗ AWS error ({error_code}): {error_msg}")
            raise SecretStorageError(f"AWS operation failed: {error_msg}")
        except Exception as e:
            print(f"✗ Unexpected error storing secret: {e}")
            raise SecretStorageError(f"Unexpected error: {str(e)}")
    
    def retrieve_secret(
        self,
        secret_id: str,
        auto_parse: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve a secret from AWS Secrets Manager with automatic format handling.
        
        Automatically detects and parses JSON secrets, returns simple strings as-is.
        
        Args:
            secret_id: The secret identifier
            auto_parse: If True, automatically parse JSON secrets (default: True)
            
        Returns:
            Dict with keys:
                - status: "success" or "error"
                - secret_id: The retrieved secret ID
                - value: The actual secret value (parsed if JSON)
                - secret_type: "json" or "simple"
                - metadata: Dict with service, timestamp, environment info
                - version_id: AWS version ID
                
        Raises:
            SecretRetrievalError: If retrieval fails
            
        Example:
            >>> service = SecretsManagerService()
            >>> result = service.retrieve_secret("codeguard/gemini/project-x")
            >>> api_key = result["value"]["api_key"]  # For JSON
            >>> token = result["value"]  # For simple string
        """
        try:
            response = self.client.get_secret_value(SecretId=secret_id)
            print(f"✓ Secret retrieved: {secret_id}")
            
            # Parse the stored secret (which includes metadata)
            secret_string = response.get("SecretString")
            stored_secret = json.loads(secret_string)
            
            secret_value = stored_secret.get("value")
            metadata = stored_secret.get("metadata", {})
            secret_type = metadata.get("type", "simple")
            
            # Parse if JSON and auto_parse is enabled
            if auto_parse and secret_type == "json":
                try:
                    parsed_value = json.loads(secret_value)
                except json.JSONDecodeError:
                    print(f"⚠ Failed to parse JSON for {secret_id}, returning raw")
                    parsed_value = secret_value
            else:
                parsed_value = secret_value
            
            return {
                "status": "success",
                "secret_id": secret_id,
                "value": parsed_value,
                "secret_type": secret_type,
                "metadata": metadata,
                "version_id": response.get("VersionId"),
                "message": "Secret retrieved successfully"
            }
            
        except self.client.exceptions.ResourceNotFoundException:
            error_msg = f"Secret not found: {secret_id}"
            print(f"✗ {error_msg}")
            raise SecretRetrievalError(error_msg)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            error_msg = e.response.get('Error', {}).get('Message')
            print(f"✗ AWS error ({error_code}): {error_msg}")
            raise SecretRetrievalError(f"AWS operation failed: {error_msg}")
        except json.JSONDecodeError as e:
            print(f"✗ Failed to parse secret data: {e}")
            raise SecretRetrievalError(f"Invalid secret format: {str(e)}")
        except Exception as e:
            print(f"✗ Unexpected error retrieving secret: {e}")
            raise SecretRetrievalError(f"Unexpected error: {str(e)}")
    
    def delete_secret(
        self,
        secret_id: str,
        force_delete: bool = False,
        recovery_days: int = 7
    ) -> Dict[str, Any]:
        """
        Delete a secret from AWS Secrets Manager.
        
        By default, schedules deletion after recovery period. Use force_delete=True
        to immediately delete without recovery option.
        
        Args:
            secret_id: The secret identifier
            force_delete: If True, immediately delete (no recovery period)
            recovery_days: Days before deletion takes effect (ignored if force_delete=True)
            
        Returns:
            Dict with deletion status and details
            
        Raises:
            SecretStorageError: If deletion fails
        """
        try:
            response = self.client.delete_secret(
                SecretId=secret_id,
                ForceDeleteWithoutRecovery=force_delete,
                RecoveryWindowInDays=recovery_days if not force_delete else None
            )
            print(f"✓ Secret scheduled for deletion: {secret_id}")
            
            return {
                "status": "success",
                "secret_id": secret_id,
                "deletion_date": response.get("DeletionDate"),
                "message": "Secret scheduled for deletion" if not force_delete else "Secret deleted immediately"
            }
        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message')
            print(f"✗ Failed to delete secret: {error_msg}")
            raise SecretStorageError(f"Deletion failed: {error_msg}")
    
    def list_secrets(self, service_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        List all secrets, optionally filtered by service.
        
        Args:
            service_filter: Optional service name to filter by
            
        Returns:
            Dict with list of secret metadata
        """
        try:
            response = self.client.list_secrets()
            secrets = response.get("SecretList", [])
            
            filtered_secrets = []
            for secret in secrets:
                # Try to get tags to filter by service
                if service_filter:
                    tags = {tag["Key"]: tag["Value"] for tag in secret.get("Tags", [])}
                    if tags.get("Service") != service_filter:
                        continue
                
                # Convert datetime objects to ISO format strings for JSON serialization
                created_date = secret.get("CreatedDate")
                last_updated = secret.get("LastUpdatedDate")

                if created_date:
                    created_date = created_date.isoformat() if hasattr(created_date, 'isoformat') else str(created_date)
                if last_updated:
                    last_updated = last_updated.isoformat() if hasattr(last_updated, 'isoformat') else str(last_updated)

                filtered_secrets.append({
                    "name": secret.get("Name"),
                    "arn": secret.get("ARN"),
                    "created_date": created_date,
                    "last_updated": last_updated,
                    "tags": secret.get("Tags", [])
                })
            
            return {
                "status": "success",
                "count": len(filtered_secrets),
                "secrets": filtered_secrets
            }
        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message')
            print(f"✗ Failed to list secrets: {error_msg}")
            return {
                "status": "error",
                "message": error_msg
            }


# Utility functions for direct usage

def store_api_key(
    service_name: str,
    api_key: str,
    environment: str = "default",
    additional_metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Convenience function to store an API key.
    
    Args:
        service_name: Service providing the key (e.g., "gemini", "stripe")
        api_key: The API key to store
        environment: Environment context
        additional_metadata: Extra tags/metadata
        
    Returns:
        Storage operation result
        
    Example:
        >>> result = store_api_key("gemini", "AIza...")
    """
    service = SecretsManagerService()
    secret_id = f"codeguard/{service_name}/{environment}"
    return service.store_secret(
        secret_id=secret_id,
        secret_value=api_key,
        service_name=service_name,
        environment=environment,
        tags=additional_metadata
    )


def retrieve_api_key(
    service_name: str,
    environment: str = "default"
) -> str:
    """
    Convenience function to retrieve a stored API key.
    
    Args:
        service_name: Service name
        environment: Environment context
        
    Returns:
        The API key value
        
    Raises:
        SecretRetrievalError: If retrieval fails
        
    Example:
        >>> api_key = retrieve_api_key("gemini")
    """
    service = SecretsManagerService()
    secret_id = f"codeguard/{service_name}/{environment}"
    result = service.retrieve_secret(secret_id)
    return result["value"]


def store_credentials_json(
    service_name: str,
    credentials_dict: Dict[str, Any],
    environment: str = "default"
) -> Dict[str, Any]:
    """
    Convenience function to store credentials as JSON.
    
    Args:
        service_name: Service name
        credentials_dict: Dict of credentials to store
        environment: Environment context
        
    Returns:
        Storage operation result
        
    Example:
        >>> creds = {"api_key": "...", "api_secret": "..."}
        >>> result = store_credentials_json("stripe", creds)
    """
    service = SecretsManagerService()
    secret_id = f"codeguard/{service_name}/{environment}"
    credentials_json = json.dumps(credentials_dict)
    return service.store_secret(
        secret_id=secret_id,
        secret_value=credentials_json,
        service_name=service_name,
        environment=environment
    )


def retrieve_credentials_json(
    service_name: str,
    environment: str = "default"
) -> Dict[str, Any]:
    """
    Convenience function to retrieve credentials stored as JSON.
    
    Args:
        service_name: Service name
        environment: Environment context
        
    Returns:
        Dict of credentials
        
    Raises:
        SecretRetrievalError: If retrieval fails
        
    Example:
        >>> creds = retrieve_credentials_json("stripe")
        >>> api_secret = creds["api_secret"]
    """
    service = SecretsManagerService()
    secret_id = f"codeguard/{service_name}/{environment}"
    result = service.retrieve_secret(secret_id)
    return result["value"]
