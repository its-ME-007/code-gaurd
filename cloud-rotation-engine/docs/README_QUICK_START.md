# Secret Manager - Quick Start Guide

Get started with the Secret Manager in 5 minutes! This guide covers the most common operations.

---

## Installation & Setup

```python
# Import the service
from app.services import SecretsManagerService

# Initialize
service = SecretsManagerService()
```

---

## 3 Ways to Use the Secret Manager

### 1️⃣ Simplest: Convenience Functions

**Store a simple API key:**
```python
from app.services import store_api_key

store_api_key(
    service_name="openai",
    api_key="sk-abc123...",
    environment="production"
)
```

**Retrieve it:**
```python
from app.services import retrieve_api_key

api_key = retrieve_api_key("openai", "production")
print(api_key)
```

**Secret ID created:** `codeguard/openai/production`

---

### 2️⃣ JSON Credentials

**Store credentials:**
```python
from app.services import store_credentials_json

creds = {
    "api_key": "AIza...",
    "project_id": "my-project",
    "endpoint": "https://api.example.com"
}

store_credentials_json(
    service_name="gemini",
    credentials_dict=creds,
    environment="production"
)
```

**Retrieve them:**
```python
from app.services import retrieve_credentials_json

creds = retrieve_credentials_json("gemini", "production")
print(creds["api_key"])
```

**Secret ID created:** `codeguard/gemini/production`

---

### 3️⃣ Advanced: Direct Service Usage

```python
from app.services.secret_manager import SecretsManagerService
import json

service = SecretsManagerService()

# Store with custom metadata
result = service.store_secret(
    secret_id="codeguard/custom/prod",
    secret_value=json.dumps({"key": "value"}),
    service_name="custom",
    environment="production",
    tags={"owner": "team-x"}
)

# Retrieve and use
result = service.retrieve_secret("codeguard/custom/prod")
value = result["value"]  # Automatically parsed if JSON
```

---

## REST API Endpoints

Start the server and use these endpoints:

### Store a Secret
```bash
curl -X POST http://localhost:8000/api/v1/secrets/store \
  -H "Content-Type: application/json" \
  -d '{
    "secret_id": "codeguard/gemini/prod",
    "secret_value": "{\"api_key\": \"AIza...\"}",
    "service_name": "gemini",
    "environment": "production"
  }'
```

### Retrieve a Secret
```bash
curl http://localhost:8000/api/v1/secrets/codeguard/gemini/prod
```

### List Secrets
```bash
curl http://localhost:8000/api/v1/secrets

# Filter by service
curl http://localhost:8000/api/v1/secrets?service_filter=gemini
```

### Delete a Secret
```bash
curl -X DELETE http://localhost:8000/api/v1/secrets/codeguard/gemini/prod
```

### Classify a Secret (Check Format)
```bash
curl -X POST http://localhost:8000/api/v1/secrets/classify \
  -H "Content-Type: application/json" \
  -d '{"secret_value": "{\"key\": \"value\"}"}'
```

---

## Secret Naming Convention

All secrets use this pattern:

```
codeguard/{service_name}/{environment}
```

**Examples:**
- `codeguard/openai/production`
- `codeguard/stripe/staging`
- `codeguard/gemini/dev`
- `codeguard/aws/production`

---

## Supported Services

✅ OpenAI  
✅ Google Gemini  
✅ Stripe  
✅ AWS IAM  
✅ SendGrid  
✅ Any custom API  

---

## Common Operations by Service

### OpenAI
```python
store_api_key("openai", "sk-proj-abc123...", "production")
api_key = retrieve_api_key("openai", "production")
```

### Stripe
```python
store_credentials_json("stripe", {
    "publishable_key": "pk_live_...",
    "secret_key": "sk_live_..."
}, "production")
```

### Google Gemini
```python
store_credentials_json("gemini", {
    "api_key": "AIza...",
    "project_id": "..."
}, "production")
```

### AWS IAM (Post-Rotation)
```python
store_credentials_json("aws", {
    "access_key_id": "AKIA_NEW_...",
    "secret_access_key": "...",
    "rotation_datetime": "2026-03-08T10:30:00Z"
}, "production")
```

---

## Automatic Format Detection

The system automatically detects and handles both formats:

```python
from app.services import DetectedSecretClassifier

classifier = DetectedSecretClassifier()

# Check if JSON
is_json = classifier.is_json_secret('{"key": "value"}')  # True
is_json = classifier.is_json_secret('sk-abc123')          # False

# Classify and parse
secret_type, value = classifier.classify_secret(secret_value)
# Returns: ('json', dict) or ('simple', str)
```

| Format | Example | Handled As |
|--------|---------|-----------|
| simple | `sk-abc123def456` | String |
| simple | `AIzaSyB_1234567890...` | String |
| json | `{"api_key": "..."}` | Dict (auto-parsed) |
| json | `[{"id": 1}]` | List (auto-parsed) |

---

## Error Handling

```python
from app.services.secret_manager import (
    SecretRetrievalError,
    SecretStorageError
)

try:
    api_key = retrieve_api_key("openai", "production")
except SecretRetrievalError as e:
    print(f"Failed to retrieve: {e}")
    # Use fallback or alert
```

---

## Expected Responses

### Store Response
```json
{
  "status": "success",
  "operation": "created",
  "secret_id": "codeguard/gemini/prod",
  "secret_type": "json",
  "version_id": "abc123xyz",
  "timestamp": "2026-03-08T10:30:45Z",
  "message": "Secret created successfully"
}
```

### Retrieve Response
```json
{
  "status": "success",
  "secret_id": "codeguard/gemini/prod",
  "value": {
    "api_key": "AIza...",
    "project_id": "my-project"
  },
  "secret_type": "json",
  "metadata": {
    "service": "gemini",
    "environment": "production",
    "timestamp": "2026-03-08T10:30:45Z"
  },
  "version_id": "abc123xyz",
  "message": "Secret retrieved successfully"
}
```

---

## Quick Troubleshooting

| Error | Solution |
|-------|----------|
| `ResourceNotFoundException` | Secret doesn't exist - check secret_id spelling |
| `AccessDenied` | Add `SecretsManagerReadWrite` IAM policy |
| `JSONDecodeError` | Invalid secret format - use classify endpoint |
| `Timeout` | AWS unavailable - retry operation |

---

## Testing

Run the examples:

```bash
cd d:\code-gaurd\cloud-rotation-engine
.venv\Scripts\Activate.ps1
python -m app.services.secret_manager_examples
```

---

## AWS Configuration

### Required IAM Policy
Attach: **`SecretsManagerReadWrite`** (AWS managed)

### Environment Variables
```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG+...
```

---

## Need More Details?

- **Full Documentation:** See `README.md`
- **Architecture Diagrams:** See `ARCHITECTURE.md`
- **Code Examples:** See `app/services/secret_manager_examples.py`

---

## Features at a Glance

✅ Automatic JSON detection  
✅ Secure AWS storage  
✅ Multiple service support  
✅ Environment segmentation  
✅ Metadata tracking  
✅ Version history  
✅ Error recovery  
✅ REST API endpoints  

---

**Ready to use!** 🚀
