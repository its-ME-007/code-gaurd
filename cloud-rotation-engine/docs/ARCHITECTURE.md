# Secret Manager Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CLIENT LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐   │
│  │  Python Code        │  │   REST API Clients   │  │  CI/CD Pipeline  │   │
│  │                     │  │   (cURL, JS, etc.)   │  │                  │   │
│  │  from app.services  │  │                      │  │  POST /secrets   │   │
│  │  import store_api_key│ │  POST /secrets/store │  │  GET /secrets    │   │
│  └──────────┬──────────┘  └──────────┬───────────┘  └─────────┬────────┘   │
│             │                        │                         │             │
└─────────────┼────────────────────────┼─────────────────────────┼─────────────┘
              │                        │                         │
              └────────────┬───────────┴─────────────┬───────────┘
                           │                         │
┌──────────────────────────┼─────────────────────────┼────────────────────────┐
│                    API GATEWAY LAYER (FastAPI)    │                         │
├──────────────────────────┼─────────────────────────┼────────────────────────┤
│                          ▼                         ▼                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Routes (/api/v1/secrets/*)                                  │  │
│  │  ├─ POST   /secrets/store      → SecretStoreRequest Validation       │  │
│  │  ├─ GET    /secrets/{id}       → SecretRetrieveResponse              │  │
│  │  ├─ DELETE /secrets/{id}       → Deletion handling                   │  │
│  │  ├─ GET    /secrets            → List with filtering                 │  │
│  │  └─ POST   /secrets/classify   → Classification endpoint             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└──────────┬───────────────────────────────────────────────────────────────────┘
           │
┌──────────┴───────────────────────────────────────────────────────────────────┐
│          SERVICE LAYER (app/services/secret_manager.py)                      │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │               SecretsManagerService                                    │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │  │
│  │  │  store_secret()                                                  │ │  │
│  │  │    ├─ Classify secret (JSON vs simple)                           │ │  │
│  │  │    ├─ Add metadata                                               │ │  │
│  │  │    ├─ Create/Update in AWS                                       │ │  │
│  │  │    └─ Return result with version_id                             │ │  │
│  │  └──────────────────────────────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │  │
│  │  │  retrieve_secret()                                               │ │  │
│  │  │    ├─ Fetch from AWS                                             │ │  │
│  │  │    ├─ Parse metadata                                             │ │  │
│  │  │    ├─ Auto-parse JSON if needed                                  │ │  │
│  │  │    └─ Return value + metadata                                    │ │  │
│  │  └──────────────────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                                │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │          DetectedSecretClassifier                                      │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │  │
│  │  │  is_json_secret(value) → bool                                    │ │  │
│  │  └──────────────────────────────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │  │
│  │  │  classify_secret(value) → ('json'|'simple', parsed_value)       │ │  │
│  │  │    ├─ Check if valid JSON                                        │ │  │
│  │  │    ├─ Parse if JSON                                              │ │  │
│  │  │    └─ Return type + value                                        │ │  │
│  │  └──────────────────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                                │
│  Utility Functions:                                                            │
│    ├─ store_api_key()            → Simple key storage                         │
│    ├─ retrieve_api_key()         → Simple key retrieval                       │
│    ├─ store_credentials_json()   → JSON credentials storage                   │
│    └─ retrieve_credentials_json()→ JSON credentials retrieval                 │
│                                                                                │
└──────────────┬───────────────────────────────────────────────────────────────┘
               │
               │ boto3.client('secretsmanager')
               │
┌──────────────┴───────────────────────────────────────────────────────────────┐
│              AWS LAYER (External Services)                                    │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  AWS Secrets Manager                                                    │ │
│  │  ┌────────────────────────────────────────────────────────────────┐   │ │
│  │  │ AWS SDKs (Encryption, Versioning, Access Control)            │   │ │
│  │  ├─ Encrypted at rest (KMS)                                     │   │ │
│  │  ├─ Version history                                             │   │ │
│  │  ├─ Tags and metadata                                           │   │ │
│  │  ├─ IAM-based access control                                    │   │ │
│  │  └─ Recovery periods for deletion                               │   │ │
│  │  └────────────────────────────────────────────────────────────────┘   │ │
│  │  ┌────────────────────────────────────────────────────────────────┐   │ │
│  │  │  Secret Storage                                                │   │ │
│  │  │  {                                                             │   │ │
│  │  │    "value": "actual_secret",                                 │   │ │
│  │  │    "metadata": {                                             │   │ │
│  │  │      "service": "gemini",                                    │   │ │
│  │  │      "type": "json|simple",                                  │   │ │
│  │  │      "environment": "production",                            │   │ │
│  │  │      "timestamp": "...",                                     │   │ │
│  │  │      "managed_by": "codeguard-rotation-engine"               │   │ │
│  │  │    }                                                          │   │ │
│  │  │  }                                                            │   │ │
│  │  └────────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

### Store Operation Flow

```
┌────────────────────────────┐
│  receive_secret_value()    │
│  e.g., "sk-abc123..." or   │
│        '{"key": "..."}'    │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  DetectedSecretClassifier  │
│  .classify_secret()        │
│                            │
│  Is JSON? ──┬──── YES─────▶ Parse JSON
│             │              Return ('json', dict)
│             │
│             └────NO──────▶ Keep as string
│                           Return ('simple', str)
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Build metadata            │
│  {                         │
│    "service": "...",      │
│    "type": "...",         │
│    "environment": "...",  │
│    "timestamp": "...",    │
│    "managed_by": "..."    │
│  }                        │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Wrap in storage format    │
│  {                         │
│    "value": "...",        │
│    "metadata": {...}      │
│  }                        │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  boto3 Secrets Manager     │
│  create_secret() OR        │
│  update_secret()           │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  AWS Secrets Manager       │
│  ├─ Encrypt with KMS      │
│  ├─ Store                 │
│  ├─ Create version        │
│  └─ Apply tags            │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Return response           │
│  {                         │
│    "status": "success",    │
│    "version_id": "...",    │
│    "timestamp": "..."      │
│  }                        │
└────────────────────────────┘
```

### Retrieve Operation Flow

```
┌────────────────────────────┐
│  retrieve_secret()         │
│  secret_id: string         │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  boto3 Secrets Manager     │
│  get_secret_value()        │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  AWS Secrets Manager       │
│  ├─ Authenticate           │
│  ├─ Authorize access       │
│  ├─ Decrypt with KMS       │
│  └─ Return SecretString    │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Parse response            │
│  {                         │
│    "value": "...",        │
│    "metadata": {...}      │
│  }                        │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐      ┌──────────────┐
│  Check secret_type        │      │   return     │
│  from metadata            │      │   raw string │
└────────┬──────────┬───────┘      └──────────────┘
         │          │
         │ simple   └─ json
         │                │
         │                ▼
         │         ┌────────────────────┐
         │         │ Parse JSON         │
         │         │ return dict        │
         │         └────────────────────┘
         │                │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────────────────┐
         │  Return result             │
         │  {                         │
         │    "status": "success",    │
         │    "value": ...,           │
         │    "secret_type": "...",   │
         │    "metadata": {...}       │
         │  }                        │
         └────────────────────────────┘
```

---

## Classification Logic

```
Secret Value Input
        │
        ▼
┌─────────────────────────┐
│ Is it a string?         │
├─────────────────────────┤
│ NO  → Classification    │
│       fails             │
│       (error)           │
│                         │
│ YES → Continue          │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Strip whitespace        │
│ Check first char        │
├─────────────────────────┤
│ Starts with { or [ ?    │
│ NO  → Type: "simple" ✓  │
│ YES → Try JSON parse    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ JSON Parse              │
├─────────────────────────┤
│ SUCCESS → Type: "json"  │
│           Return dict   │
│                         │
│ FAIL    → Type: "simple"│
│           Return string │
└─────────────────────────┘
```

---

## Exception Hierarchy

```
Exception
│
├─ SecretClassificationError
│  └─ Raised when secret cannot be classified
│     (invalid format, parse error)
│
├─ SecretStorageError
│  └─ Raised when store/delete operations fail
│     (AWS error, permissions, invalid secret_id)
│
└─ SecretRetrievalError
   └─ Raised when retrieval fails
      (secret not found, AWS error, format error)
```

---

## Module Dependencies

```
secret_manager.py
│
├─ boto3
│  └─ AWS SDK for Python
│
├─ json
│  └─ Standard library
│
├─ typing
│  └─ Type hints
│
├─ datetime
│  └─ Timestamp handling
│
├─ botocore.exceptions
│  └─ AWS error handling
│
├─ app.core.config
│  └─ AWS credentials
│
└─ app.core.logging_config
   └─ Logger setup
```

---

## Integration Points

### 1. Rotation Service Integration

```
┌────────────────────────────────────┐
│  RotationService                   │
│  .rotate_key(iam_user, key_id...)  │
└────────────────┬───────────────────┘
                 │
                 ▼ New credentials
        ┌────────────────────┐
        │ Store in Secrets   │
        │ Manager            │
        └────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
  store_credentials_json  (post-rotation)
  service="aws"
  environment="production"
```

### 2. API Route Integration

```
REST Client
    │
    ├─ POST /api/v1/secrets/store
    │   └─ FastAPI route
    │       └─ SecretsManagerService.store_secret()
    │
    ├─ GET /api/v1/secrets/{secret_id}
    │   └─ FastAPI route
    │       └─ SecretsManagerService.retrieve_secret()
    │
    └─ DELETE /api/v1/secrets/{secret_id}
        └─ FastAPI route
            └─ SecretsManagerService.delete_secret()
```

### 3. Direct Import Integration

```
from app.services import store_api_key

store_api_key("service", "secret_value", "env")
    │
    └─ SecretsManagerService.store_secret()
        └─ AWS Secrets Manager API
```

---

## Storage Structure

```
AWS Secrets Manager
│
└─ Secret: "codeguard/gemini/production"
   │
   ├─ Encrypted Metadata
   │  ├─ name: "codeguard/gemini/production"
   │  ├─ arn: "arn:aws:secretsmanager:..."
   │  ├─ created_date: "2026-03-08T10:30:45Z"
   │  ├─ last_updated: "2026-03-08T10:30:45Z"
   │  └─ tags:
   │     ├─ ManagedBy: "codeguard-rotation-engine"
   │     ├─ Service: "gemini"
   │     ├─ Environment: "production"
   │     └─ SecretType: "json"
   │
   └─ Encrypted Secret String
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

---

## Environment Variables

```
.env
├─ AWS_REGION=us-east-1
├─ AWS_ACCESS_KEY_ID=AKIA...
└─ AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG+...
```

Loaded by:
```python
app/core/config.py
├─ settings.aws_region
├─ settings.aws_access_key_id
└─ settings.aws_secret_access_key
```

Used by:
```python
SecretsManagerService.__init__()
└─ boto3.client('secretsmanager', ...)
```

---

## Summary

This architecture provides:

1. **Separation of Concerns** - Classification, storage, and retrieval are separate
2. **Automatic Format Detection** - JSON vs simple strings handled transparently
3. **Secure Storage** - AWS encryption and IAM controls
4. **Multiple Integration Points** - Python SDK, REST API, direct functions
5. **Rich Metadata** - Service, environment, timestamps for audit trails
6. **Error Handling** - Specific exception types for proper error management
7. **Scalability** - Supports unlimited secrets across multiple services
