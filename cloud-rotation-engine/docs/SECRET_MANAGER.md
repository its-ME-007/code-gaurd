# Secret Manager Service Documentation

## Overview

The Secret Manager service provides a comprehensive layer for secure storage and retrieval of credentials in AWS Secrets Manager. It automatically classifies secrets (JSON or simple strings) and handles both types appropriately.

**Location:** `app/services/secret_manager.py`

## Features

✅ **Automatic Secret Classification** - Detects JSON vs simple string format  
✅ **Secure Storage** - Stores secrets with metadata and version tracking  
✅ **Flexible Retrieval** - Automatically parses JSON or returns simple strings  
✅ **Metadata Management** - Tracks service, environment, timestamp, and custom tags  
✅ **Error Handling** - Rich exception hierarchy for proper error management  
✅ **AWS Integration** - Full AWS Secrets Manager API support  

## Architecture

### Components

#### 1. `DetectedSecretClassifier`

Classifies secrets into JSON or simple string format.

```python
from app.services.secret_manager import DetectedSecretClassifier

classifier = DetectedSecretClassifier()

# Check if secret is JSON
is_json = classifier.is_json_secret('{"api_key": "..."}')  # True
is_json = classifier.is_json_secret('sk-abc123')            # False

# Classify and parse
secret_type, value = classifier.classify_secret(secret_value)
# Returns: ('json', dict) or ('simple', str)
```

#### 2. `SecretsManagerService`

Main service for storing and retrieving secrets from AWS.

```python
from app.services.secret_manager import SecretsManagerService

service = SecretsManagerService()

# Store a secret
result = service.store_secret(
    secret_id="codeguard/gemini/project-x",
    secret_value='{"api_key": "AIza..."}',
    service_name="gemini"
)

# Retrieve a secret
result = service.retrieve_secret("codeguard/gemini/project-x")
api_key = result["value"]["api_key"]  # Automatically parsed
```

#### 3. Convenience Functions

Quick-access functions for common use cases:

- `store_api_key()` - Store simple API keys
- `retrieve_api_key()` - Retrieve simple API keys
- `store_credentials_json()` - Store JSON credentials
- `retrieve_credentials_json()` - Retrieve JSON credentials

## Usage Patterns

### Pattern 1: Simple API Key Storage

For single-value API keys (OpenAI, Gemini Token, etc.):

```python
from app.services import store_api_key, retrieve_api_key

# Store
result = store_api_key(
    service_name="openai",
    api_key="sk-proj-1234567890abcdefghijklmnop",
    environment="production"
)

# Retrieve
api_key = retrieve_api_key("openai", "production")
```

**Secret ID Format:** `codeguard/{service_name}/{environment}`  
**Example:** `codeguard/openai/production`

### Pattern 2: Complex JSON Credentials

For multi-field credentials (Stripe, AWS rotated keys, etc.):

```python
from app.services import store_credentials_json, retrieve_credentials_json
import json

credentials = {
    "access_key_id": "AKIA...",
    "secret_access_key": "wJalrXUtnFEMI/K7MDENG+...",
    "session_token": "FwoGZXIvYXdzEBaaD...",
    "expiration": "2026-03-09T10:30:00Z"
}

# Store
result = store_credentials_json(
    service_name="aws",
    credentials_dict=credentials,
    environment="production"
)

# Retrieve
creds = retrieve_credentials_json("aws", "production")
access_key = creds["access_key_id"]
```

### Pattern 3: Direct Service Usage

For advanced scenarios with custom metadata:

```python
from app.services.secret_manager import SecretsManagerService
import json

service = SecretsManagerService()

# Store with custom tags
result = service.store_secret(
    secret_id="codeguard/stripe/backend",
    secret_value=json.dumps({
        "publishable_key": "pk_live_...",
        "secret_key": "sk_live_...",
        "webhook_signing_secret": "whsec_..."
    }),
    service_name="stripe",
    environment="production",
    description="Stripe API credentials for payment processing",
    tags={
        "project": "payment-system",
        "sensitivity": "critical",
        "owner": "payments-team"
    }
)

# Retrieve with automatic parsing
result = service.retrieve_secret("codeguard/stripe/backend")
# result["value"] is automatically a dict
publish_key = result["value"]["publishable_key"]
```

## Secret Classification

The system automatically detects whether a secret is JSON or a simple string.

### Classification Logic

```
Secret Input
    │
    ├─ Is it valid JSON?
    │   ├── YES → Type: "json"
    │   └── NO  → Type: "simple"
    │
    └─ Store with metadata including type
```

### Examples

| Input | Classified As |
|-------|---------------|
| `sk-abc123def456` | simple |
| `AIzaSyB_1234567890...` | simple |
| `{"api_key": "..."}` | json |
| `[{"id": 1}, {"id": 2}]` | json |
| `{invalid json}` | simple (not valid JSON) |

## API Endpoints

### REST API Endpoints

All endpoints are under `/api/v1/secrets`.

#### 1. Store Secret
```
POST /api/v1/secrets/store
Content-Type: application/json

{
  "secret_id": "codeguard/gemini/project-alpha",
  "secret_value": "{\"api_key\": \"AIza...\"}",
  "service_name": "gemini",
  "environment": "production",
  "description": "Google Gemini API credentials"
}
```

**Response:**
```json
{
  "status": "success",
  "operation": "created",
  "secret_id": "codeguard/gemini/project-alpha",
  "secret_type": "json",
  "version_id": "abc123...",
  "timestamp": "2026-03-08T10:30:45.123456",
  "message": "Secret created successfully in AWS Secrets Manager"
}
```

#### 2. Retrieve Secret
```
GET /api/v1/secrets/{secret_id}?auto_parse=true
```

**Response:**
```json
{
  "status": "success",
  "secret_id": "codeguard/gemini/project-alpha",
  "value": {
    "api_key": "AIza...",
    "project_id": "my-project-123"
  },
  "secret_type": "json",
  "metadata": {
    "service": "gemini",
    "environment": "production",
    "managed_by": "codeguard-rotation-engine",
    "timestamp": "2026-03-08T10:30:45.123456"
  },
  "version_id": "abc123...",
  "message": "Secret retrieved successfully"
}
```

#### 3. Delete Secret
```
DELETE /api/v1/secrets/{secret_id}?force_delete=false&recovery_days=7
```

**Response:**
```json
{
  "status": "success",
  "secret_id": "codeguard/gemini/project-alpha",
  "deletion_date": "2026-03-15T10:30:45Z",
  "message": "Secret scheduled for deletion"
}
```

#### 4. List Secrets
```
GET /api/v1/secrets?service_filter=gemini
```

**Response:**
```json
{
  "status": "success",
  "count": 2,
  "secrets": [
    {
      "name": "codeguard/gemini/project-alpha",
      "arn": "arn:aws:secretsmanager:us-east-1:123456789:secret:codeguard/gemini/project-alpha-XXX",
      "created_date": "2026-03-08T10:30:45Z",
      "last_updated": "2026-03-08T10:30:45Z",
      "tags": [...]
    }
  ]
}
```

#### 5. Classify Secret
```
POST /api/v1/secrets/classify
Content-Type: application/json

{
  "secret_value": "{\"api_key\": \"AIza...\"}"
}
```

**Response:**
```json
{
  "status": "success",
  "secret_type": "json",
  "is_json": true,
  "message": "Secret classified as json"
}
```

## Integration with Rotation Service

After rotating an AWS IAM key, store the new credentials:

```python
from app.services.secret_manager import SecretsManagerService
from datetime import datetime
import json

service = SecretsManagerService()

rotated_credentials = {
    "access_key_id": "AKIA_NEW_KEY_12345678",
    "secret_access_key": "new_secret_access_key_abcdefghijklmnop",
    "previous_key_id": "AKIA_OLD_KEY_12345678",
    "rotation_datetime": datetime.utcnow().isoformat(),
    "iam_user": "demo-user",
    "incident_id": "550e8400-e29b-41d4-a716-446655440000"
}

result = service.store_secret(
    secret_id="codeguard/aws/demo-user",
    secret_value=json.dumps(rotated_credentials),
    service_name="aws",
    environment="production",
    description="AWS credentials after key rotation"
)
```

## Error Handling

### Exception Hierarchy

```
Exception
├── SecretClassificationError
├── SecretStorageError
└── SecretRetrievalError
```

### Example Error Handling

```python
from app.services.secret_manager import (
    SecretsManagerService,
    SecretStorageError,
    SecretRetrievalError
)

service = SecretsManagerService()

# Handle retrieval errors
try:
    result = service.retrieve_secret("codeguard/nonexistent/secret")
except SecretRetrievalError as e:
    print(f"Secret not found or retrieval failed: {e}")

# Handle storage errors
try:
    result = service.store_secret(...)
except SecretStorageError as e:
    print(f"Failed to store secret: {e}")
```

## AWS Configuration

### Required IAM Permissions

The service requires `SecretsManagerReadWrite` AWS managed policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:CreateSecret",
        "secretsmanager:GetSecretValue",
        "secretsmanager:PutSecretValue",
        "secretsmanager:UpdateSecret",
        "secretsmanager:DeleteSecret",
        "secretsmanager:ListSecrets",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "*"
    }
  ]
}
```

### Environment Variables

Ensure these are set in `.env`:

```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG+...
```

## Secret Storage Structure

Secrets are stored with a wrapper that includes metadata:

```json
{
  "value": "actual_secret_value_or_json",
  "metadata": {
    "service": "gemini",
    "type": "json",
    "environment": "production",
    "managed_by": "codeguard-rotation-engine",
    "timestamp": "2026-03-08T10:30:45.123456",
    "original_format": "json"
  }
}
```

## Best Practices

### 1. Secret Naming Convention

Use the pattern: `codeguard/{service_name}/{environment}`

- ✅ `codeguard/gemini/production`
- ✅ `codeguard/stripe/staging`
- ✅ `codeguard/aws/dev`
- ❌ `gemini_api_key`
- ❌ `AmazingSecretKey123`

### 2. Environment Segmentation

Store different environments separately:

```python
# Production
store_api_key("openai", key, environment="production")

# Staging
store_api_key("openai", key, environment="staging")

# Development
store_api_key("openai", key, environment="dev")
```

### 3. Metadata Usage

Always include service name and environment for better organization:

```python
service.store_secret(
    secret_id="codeguard/stripe/production",
    service_name="stripe",  # Always specify
    environment="production",  # Always specify
    description="Stripe payment processing keys"
)
```

### 4. Error Recovery

Implement proper error handling around secret operations:

```python
try:
    result = service.retrieve_secret(secret_id)
except SecretRetrievalError:
    # Log error, alert team, use fallback
    logger.error(f"Failed to retrieve secret {secret_id}")
    # Use cached/fallback credentials if available
```

## Troubleshooting

### Issue: "ResourceNotFoundException"
**Cause:** Secret doesn't exist in AWS Secrets Manager  
**Solution:** Check secret_id spelling, ensure secret was created in correct region

### Issue: "AWS API error: AccessDenied"
**Cause:** Insufficient IAM permissions  
**Solution:** Verify `SecretsManagerReadWrite` policy is attached

### Issue: "Failed to parse secret data: JSONDecodeError"
**Cause:** Corrupted secret data or invalid JSON  
**Solution:** Delete and recreate the secret with valid JSON

### Issue: "Secret classified as json but parse failed"
**Cause:** Secret looks like JSON but isn't valid  
**Solution:** Check secret format, use classification endpoint to validate

## Examples

See `app/services/secret_manager_examples.py` for comprehensive examples including:
- Simple API key storage
- Complex JSON credentials
- Multiple provider support (Stripe, Gemini, AWS)
- Error handling patterns
- Integration with rotation service

Run examples:
```bash
python -m app.services.secret_manager_examples
```

## Performance Considerations

- **Caching:** Consider caching frequently accessed secrets (they change infrequently)
- **Batch Operations:** For retrieving multiple secrets, consider parallelizing requests
- **Version Management:** AWS Secrets Manager keeps version history; old versions can be accessed if needed

## Security Notes

✅ Secrets are encrypted at rest in AWS  
✅ All communication uses AWS SDK with TLS  
✅ Metadata includes creation timestamp and service info  
✅ Supports environment segmentation for access control  
✅ Delete operations support recovery periods  
✅ Tags allow fine-grained access control via IAM policies  

## Future Enhancements

- Automatic secret rotation scheduling
- Secret expiration alerts
- Audit trail for all secret access
- Integration with CI/CD for automated credential injection
- Cross-region replication for disaster recovery
- Secret change notifications/webhooks
