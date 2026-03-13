"""
Examples and test cases for the Secret Manager service.

This file demonstrates all the functionality of the secret management layer:
- Storing simple API keys
- Storing complex JSON credentials
- Retrieving and using secrets
- Automatic classification and parsing
"""

from app.services.secret_manager import (
    SecretsManagerService,
    DetectedSecretClassifier,
    store_api_key,
    retrieve_api_key,
    store_credentials_json,
    retrieve_credentials_json,
    SecretStorageError,
    SecretRetrievalError
)
import json


# ============================================================================
# EXAMPLE 1: Simple API Key Storage and Retrieval
# ============================================================================

def example_simple_api_key():
    """Store and retrieve a simple API key (string format)"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Simple API Key Storage")
    print("="*70)
    
    service = SecretsManagerService()
    
    # Store a simple API key
    api_key = "sk-proj-1234567890abcdefghijklmnop"
    
    result = service.store_secret(
        secret_id="codeguard/openai/production",
        secret_value=api_key,
        service_name="openai",
        environment="production",
        description="OpenAI API key for production",
        tags={"project": "codeguard", "tier": "critical"}
    )
    
    print(f"\n✓ Storage Result:")
    print(f"  Status: {result['status']}")
    print(f"  Type: {result['secret_type']}")
    print(f"  Version: {result['version_id']}")
    
    # Retrieve the secret
    retrieved = service.retrieve_secret("codeguard/openai/production")
    
    print(f"\n✓ Retrieval Result:")
    print(f"  Secret Type: {retrieved['secret_type']}")
    print(f"  Value: {retrieved['value'][:20]}...")
    print(f"  Service: {retrieved['metadata']['service']}")
    print(f"  Environment: {retrieved['metadata']['environment']}")


# ============================================================================
# EXAMPLE 2: Complex JSON Credentials Storage
# ============================================================================

def example_json_credentials():
    """Store and retrieve complex JSON credentials"""
    print("\n" + "="*70)
    print("EXAMPLE 2: JSON Credentials Storage")
    print("="*70)
    
    service = SecretsManagerService()
    
    # Complex JSON credentials
    gemini_credentials = {
        "api_key": "AIzaSyB_1234567890abcdefghijklmnop",
        "project_id": "my-project-123",
        "client_email": "service@my-project-123.iam.gserviceaccount.com",
        "client_id": "1234567890",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
    }
    
    credentials_json = json.dumps(gemini_credentials, indent=2)
    
    result = service.store_secret(
        secret_id="codeguard/gemini/project-alpha",
        secret_value=credentials_json,
        service_name="gemini",
        environment="production",
        description="Google Gemini API credentials",
        tags={"project": "alpha", "sensitivity": "high"}
    )
    
    print(f"\n✓ Storage Result:")
    print(f"  Status: {result['status']}")
    print(f"  Type: {result['secret_type']}")  # Will be 'json'
    
    # Retrieve the secret - automatically parsed as JSON
    retrieved = service.retrieve_secret("codeguard/gemini/project-alpha")
    
    print(f"\n✓ Retrieval Result:")
    print(f"  Secret Type: {retrieved['secret_type']}")
    print(f"  API Key: {retrieved['value']['api_key'][:20]}...")
    print(f"  Project ID: {retrieved['value']['project_id']}")
    print(f"  Timestamp: {retrieved['metadata']['timestamp']}")


# ============================================================================
# EXAMPLE 3: Stripe API Credentials (Multiple keys)
# ============================================================================

def example_stripe_credentials():
    """Store Stripe API credentials with multiple keys"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Stripe Credentials Storage")
    print("="*70)
    
    stripe_creds = {
        "publishable_key": "pk_live_abcd1234567890",
        "secret_key": "sk_live_abcd1234567890",
        "webhook_signing_secret": "whsec_test_secret",
        "account_id": "acct_1234567890",
        "api_version": "2023-10-16"
    }
    
    # Using convenience function
    result = store_credentials_json(
        service_name="stripe",
        credentials_dict=stripe_creds,
        environment="production"
    )
    
    print(f"\n✓ Storage Result: {result['status']}")
    print(f"  Secret Type: {result['secret_type']}")
    
    # Retrieve using convenience function
    retrieved_creds = retrieve_credentials_json("stripe", "production")
    
    print(f"\n✓ Retrieved Credentials:")
    print(f"  Secret Key: {retrieved_creds['secret_key']}")
    print(f"  Webhook Secret: {retrieved_creds['webhook_signing_secret']}")


# ============================================================================
# EXAMPLE 4: AWS Credentials (Multiple access keys scenario)
# ============================================================================

def example_aws_credentials():
    """Store rotated AWS credentials"""
    print("\n" + "="*70)
    print("EXAMPLE 4: AWS Credentials Storage (Post-Rotation)")
    print("="*70)
    
    service = SecretsManagerService()
    
    rotated_aws_creds = {
        "access_key_id": "AKIA5NEWKEY123456789",
        "secret_access_key": "wJalrXUtnFEMI/K7MDENG+newSecretKey/7EnG789",
        "session_token": None,
        "rotation_timestamp": "2026-03-08T10:30:00Z",
        "previous_key_deactivated": True,
        "iam_user": "service-account-prod"
    }
    
    result = store_credentials_json(
        service_name="aws",
        credentials_dict=rotated_aws_creds,
        environment="production"
    )
    
    print(f"\n✓ AWS Key Stored After Rotation")
    print(f"  Status: {result['status']}")
    print(f"  Timestamp: {result['timestamp']}")


# ============================================================================
# EXAMPLE 5: Secret Classification Demonstration
# ============================================================================

def example_classification():
    """Demonstrate secret classification"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Secret Classification")
    print("="*70)
    
    classifier = DetectedSecretClassifier()
    
    # Test 1: Simple string
    simple_key = "sk-abc123def456"
    secret_type, value = classifier.classify_secret(simple_key)
    print(f"\nSimple Key Classification:")
    print(f"  Input: {simple_key}")
    print(f"  Type: {secret_type}")
    print(f"  Value: {value}")
    
    # Test 2: JSON string
    json_secret = json.dumps({
        "username": "admin",
        "password": "secure_pass_123",
        "host": "db.example.com"
    })
    secret_type, value = classifier.classify_secret(json_secret)
    print(f"\nJSON Secret Classification:")
    print(f"  Input: {json_secret[:40]}...")
    print(f"  Type: {secret_type}")
    print(f"  Parsed: {value}")
    
    # Test 3: Invalid JSON that looks like it might be (should return 'simple')
    almost_json = "{not actually json}"
    secret_type, value = classifier.classify_secret(almost_json)
    print(f"\nAlmost-JSON Classification:")
    print(f"  Input: {almost_json}")
    print(f"  Type: {secret_type}")


# ============================================================================
# EXAMPLE 6: Error Handling
# ============================================================================

def example_error_handling():
    """Demonstrate error handling"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Error Handling")
    print("="*70)
    
    service = SecretsManagerService()
    
    # Try to retrieve non-existent secret
    try:
        result = service.retrieve_secret("codeguard/nonexistent/secret")
    except SecretRetrievalError as e:
        print(f"\n✓ Caught expected error when retrieving non-existent secret:")
        print(f"  Error: {str(e)}")
    
    # Try to store invalid secret
    try:
        result = service.store_secret(
            secret_id="test/secret",
            secret_value="",  # Empty secret
            service_name="test"
        )
        print(f"✓ Empty secret stored (validation depends on AWS)")
    except SecretStorageError as e:
        print(f"✓ Caught error when storing invalid secret: {str(e)}")


# ============================================================================
# EXAMPLE 7: Listing Secrets by Service
# ============================================================================

def example_list_secrets():
    """Demonstrate listing and filtering secrets"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Listing Secrets")
    print("="*70)
    
    service = SecretsManagerService()
    
    # List all secrets
    all_secrets = service.list_secrets()
    print(f"\n✓ Total Secrets: {all_secrets['count']}")
    
    # List secrets for specific service
    gemini_secrets = service.list_secrets(service_filter="gemini")
    print(f"✓ Gemini Secrets: {gemini_secrets['count']}")
    
    for secret in gemini_secrets.get('secrets', [])[:3]:
        print(f"  - {secret['name']}")


# ============================================================================
# EXAMPLE 8: Integration with Rotation Service
# ============================================================================

def example_rotation_integration():
    """
    Example of how to integrate with the rotation service.
    After rotating an AWS key, store the new credentials.
    """
    print("\n" + "="*70)
    print("EXAMPLE 8: Integration with Rotation Service")
    print("="*70)
    
    # This is how the rotation service would use the secret manager
    # after successfully rotating an IAM key:
    
    from app.services.secret_manager import SecretsManagerService
    
    rotated_credentials = {
        "access_key_id": "AKIA_NEW_KEY_12345678",
        "secret_access_key": "new_secret_access_key_abcdefghijklmnop",
        "previous_key_id": "AKIA_OLD_KEY_12345678",
        "rotation_datetime": "2026-03-08T15:30:45Z",
        "iam_user": "demo-user",
        "incident_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    
    service = SecretsManagerService()
    
    result = service.store_secret(
        secret_id="codeguard/aws/demo-user",
        secret_value=json.dumps(rotated_credentials),
        service_name="aws",
        environment="production",
        description="AWS credentials after key rotation"
    )
    
    print(f"\n✓ Post-Rotation Credentials Stored")
    print(f"  Status: {result['status']}")
    print(f"  User: demo-user")
    print(f"  Incident ID: 550e8400-e29b-41d4-a716-446655440000")


# ============================================================================
# Main Runner
# ============================================================================

def run_all_examples():
    """Run all examples"""
    try:
        example_classification()
        example_simple_api_key()
        example_json_credentials()
        example_stripe_credentials()
        example_aws_credentials()
        example_error_handling()
        example_list_secrets()
        example_rotation_integration()
        
        print("\n" + "="*70)
        print("✓ All examples completed successfully!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        raise


if __name__ == "__main__":
    run_all_examples()
