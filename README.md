# Cloud Key Rotation Engine + Secret Manager

**Date:** March 8, 2026 | **Status:** ✅ Production Ready

A deterministic AWS IAM Access Key Lifecycle Manager that automates the rotation of compromised credentials while maintaining audit compliance, operational safety, and **secure secret storage**.

**Positioning:** Transforms secret detection from passive identification into active remediation through autonomous, auditable credential lifecycle management + secure centralized secret storage.

---

## 📚 Documentation Structure

This project has two main documented components:

### 🔄 Cloud Key Rotation Engine
- **Location:** `cloud-rotation-engine/`
- **Docs:** [cloud-rotation-engine/docs/README.md](cloud-rotation-engine/docs/README.md)
- **Purpose:** Automated AWS IAM key rotation with audit compliance

### 🔐 Secret Manager
- **Location:** `cloud-rotation-engine/app/services/secret_manager.py`
- **Quick Start:** [cloud-rotation-engine/docs/README_QUICK_START.md](cloud-rotation-engine/docs/README_QUICK_START.md)
- **Complete Guide:** [cloud-rotation-engine/docs/README.md](cloud-rotation-engine/docs/README.md) (Secret Manager section)
- **Purpose:** AWS Secrets Manager integration with automatic JSON/simple string classification

---

## 🚀 Project Overview

### Rotation Engine Features

- **Access Key Validation** – Confirms key ownership and retrieves attached IAM policies
- **Deterministic Rotation** – Creates new keys, deactivates old ones, and maintains immutable audit trails
- **Policy Risk Classification** – Maps privilege levels (Administrator, PowerUser, Custom) to risk ratings
- **Structured APIs** – Clean integration hooks for compliance engines and downstream systems
- **Safety Constraints** – Scoped IAM permissions, no policy modifications, no multi-cloud support
- **Graceful Error Handling** – Well-defined error contracts for system resilience
- **Key Age Analysis** – Tracks credential age and rotation history

### Secret Manager Features

- **Automatic Secret Classification** – Detects JSON vs simple string format automatically
- **Secure Storage** – AWS Secrets Manager integration with encryption at rest
- **Smart Retrieval** – Auto-parses JSON, returns simple strings as-is
- **REST API** – 5 endpoints for store, retrieve, delete, list, classify
- **Multiple Integration Points** – Convenience functions, service class, REST API, direct imports
- **Environment Segmentation** – Separate secrets by dev/staging/production
- **Error Handling** – Custom exceptions for proper error management

---

## Design Philosophy

🛡️ **Deterministic > AI** – Pure cloud automation, no ML decision-making  
🏗️ **Safe Automation > Aggressive Automation** – Controlled IAM scope, no destructive surprises  
📝 **Observable & Auditable** – Every action logged with incident correlation  
🔐 **Controlled IAM Scope** – Least-privilege permissions, no policy editing  
💾 **Centralized Secrets** – All credentials securely stored in AWS Secrets Manager  

---

## 🎯 Quick Start

### Prerequisites

- Python 3.9+
- AWS credentials configured (with appropriate IAM permissions)
- `pip` package manager

### Installation

```bash
git clone <repo-url>
cd cloud-rotation-engine
pip install -r requirements.txt
```

### Configuration

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Configure AWS credentials (either in `.env` or via environment):

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key_id
AWS_SECRET_ACCESS_KEY=your_secret_key
LOG_LEVEL=INFO
```

### Running the Service

```bash
python app/main.py
```

The API will be available at `http://localhost:8000`.

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "cloud-key-rotation-engine"
}
```

## API Documentation

### 1. Trigger Key Rotation

**Endpoint:** `POST /api/v1/rotate`

**Request Body:**
```json
{
  "iam_user": "dev-user",
  "access_key_id": "AKIA...",
  "incident_id": "550e8400-e29b-41d4-a716-446655440000",
  "risk_level": "critical"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "rotation_completed": true,
  "iam_user": "dev-user",
  "old_key_deactivated": true,
  "new_key_id": "AKIA...",
  "policy_level": "AdministratorAccess",
  "rotation_time_ms": 482
}
```

**Response (Error):**
```json
{
  "status": "error",
  "reason": "AccessDenied",
  "rotation_completed": false,
  "details": "User does not have permission to perform: iam:DeleteAccessKey"
}
```

### 2. Retrieve Audit Log

**Endpoint:** `GET /api/v1/audit/{incident_id}`

**Response:**
```json
{
  "incident_id": "550e8400-e29b-41d4-a716-446655440000",
  "old_key": "AKIA...",
  "new_key": "AKIA...",
  "rotation_timestamp": "2024-03-02T10:30:45.123456",
  "iam_user": "dev-user",
  "policy_level": "AdministratorAccess",
  "rotation_time_ms": 482,
  "status": "success"
}
```

### 3. Analyze User Keys

**Endpoint:** `GET /api/v1/user/{iam_user}/keys`

**Response:**
```json
{
  "iam_user": "dev-user",
  "total_keys": 2,
  "keys": [
    {
      "access_key_id": "AKIA...",
      "status": "Active",
      "create_date": "2024-01-15T10:30:00",
      "age_days": 47
    }
  ]
}
```

## Rotation Workflow

```
1. Incident Intake
   ├─ Validate key exists and belongs to user
   ├─ Fetch attached IAM policies
   └─ Classify privilege level (Admin/PowerUser/Custom)

2. Key Rotation (Deterministic Lifecycle)
   ├─ Create new access key
   ├─ Deactivate old key
   ├─ Delete old key
   └─ Log metadata for audit trail

3. Response
   └─ Return structured result with new key ID and metrics
```

## IAM Permissions Required

The rotation service requires these IAM permissions on the **demo IAM user** it manages:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateAccessKey",
        "iam:DeleteAccessKey",
        "iam:UpdateAccessKey",
        "iam:ListAccessKeys",
        "iam:ListAttachedUserPolicies",
        "iam:ListUserPolicies"
      ],
      "Resource": "arn:aws:iam::*:user/dev-*"
    }
  ]
}
```

**Important Safety Notes:**
- ❌ Do NOT modify IAM policies
- ❌ Do NOT rotate roles
- ❌ Do NOT touch root account
- ❌ Do NOT handle MFA

## Policy Risk Mapping

| Attached Policy | Risk Level | Action |
|---|---|---|
| `AdministratorAccess` | 🔴 Critical | Always rotate |
| `PowerUserAccess` | 🟠 High | Always rotate |
| Custom/Inline | 🟡 Medium | Rotate if risk >= High |
| Unknown | 🟢 Low | Rotate if explicitly requested |

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run specific test:

```bash
pytest tests/test_rotation.py::test_rotate_key_success -v
```

With coverage:

```bash
pytest tests/ --cov=app --cov-report=html
```

## Architecture

```
cloud-rotation-engine/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── routes.py          # API endpoints
│   │   └── schemas.py         # Request/response models
│   ├── services/
│   │   ├── rotation_service.py    # Orchestration layer
│   │   ├── iam_validator.py       # Key validation
│   │   └── policy_classifier.py   # Policy classification
│   ├── core/
│   │   ├── config.py          # Settings management
│   │   ├── logging_config.py  # Logging setup
│   │   └── security.py        # Security utilities
│   ├── models/
│   │   └── incident_model.py  # Data models
│   └── utils/
│       ├── time_utils.py      # Time utilities
│       └── error_handlers.py  # Error handling
├── tests/
│   ├── test_rotation.py       # Rotation tests
│   └── test_validator.py      # Validator tests
├── requirements.txt           # Python dependencies
├── .env                       # Environment configuration
└── README.md                  # This file
```

## Logging

Logs are written to both console and file (`logs/rotation.log`):

```
2024-03-02 10:30:45,123 - app.api.routes - INFO - Rotation request received for user=dev-user, incident_id=550e8400-e29b-41d4-a716-446655440000
2024-03-02 10:30:45,234 - app.services.rotation_service - INFO - 🔍 Validating key AKIA...
2024-03-02 10:30:45,345 - app.services.rotation_service - INFO - ✅ Key AKIA... validated for user dev-user
...
```

## Operational Checklist

Before going to production:

- [ ] Create dedicated demo IAM user (e.g., `rotation-demo-user`)
- [ ] Attach required IAM permissions (see above)
- [ ] Configure AWS credentials in environment
- [ ] Run health check: `curl http://localhost:8000/health`
- [ ] Test rotation with demo user
- [ ] Verify audit logs are created
- [ ] Set up log aggregation
- [ ] Configure API key if needed

## Troubleshooting

### "AccessDenied" Error

**Cause:** Service role lacks required IAM permissions

**Solution:**
```bash
# Verify attached policies
aws iam list-attached-user-policies --user-name dev-user

# Verify inline policies
aws iam list-user-policies --user-name dev-user
```

### "Key Not Found" Error

**Cause:** Access key doesn't exist or belongs to different user

**Solution:**
```bash
# List keys for user
aws iam list-access-keys --user-name dev-user
```

### "Rate Limit" Error

**Cause:** AWS API throttling

**Solution:** Implement exponential backoff or increase interval between rotations

## Performance Metrics

- **Average Rotation Time:** ~200-500ms
- **Key Creation:** ~100ms
- **Key Deactivation:** ~50ms
- **Key Deletion:** ~75ms
- **Policy Retrieval:** ~100-150ms

---

# Secret Manager Integration

## Overview

A comprehensive AWS Secrets Manager integration layer that automatically classifies, stores, and retrieves secrets with full support for both JSON and simple string formats.

**Features:**
- ✅ Automatic secret classification (JSON detection)
- ✅ Secure storage with AWS encryption
- ✅ Smart retrieval with auto-parsing
- ✅ REST API endpoints (store, retrieve, delete, list, classify)
- ✅ Multiple integration points (Python SDK, REST, convenience functions)
- ✅ Environment segmentation (dev/staging/production)
- ✅ Comprehensive error handling

## Quick Usage

### Store a Secret
```python
from app.services import store_api_key
store_api_key("openai", "sk-abc123...", "production")
```

### Retrieve a Secret
```python
from app.services import retrieve_api_key
api_key = retrieve_api_key("openai", "production")
```

### Use REST API
```bash
# Store
curl -X POST http://localhost:8000/api/v1/secrets/store \
  -H "Content-Type: application/json" \
  -d '{
    "secret_id": "codeguard/gemini/prod",
    "secret_value": "{\"api_key\": \"AIza...\"}",
    "service_name": "gemini"
  }'

# Retrieve
curl http://localhost:8000/api/v1/secrets/codeguard/gemini/prod

# List secrets
curl http://localhost:8000/api/v1/secrets?service_filter=gemini
```

## Integration with Rotation Service

After rotating an AWS key:

```python
from app.services import store_credentials_json

rotated_credentials = {
    "access_key_id": "AKIA_NEW_...",
    "secret_access_key": "...",
    "rotation_datetime": "2026-03-08T10:30:00Z"
}

store_credentials_json("aws", rotated_credentials, "production")
```

## Secret Naming Convention

All secrets use: `codeguard/{service_name}/{environment}`

**Examples:**
- `codeguard/openai/production`
- `codeguard/stripe/staging`
- `codeguard/gemini/dev`
- `codeguard/aws/production`

## REST API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/secrets/store` | Store a secret |
| GET | `/api/v1/secrets/{secret_id}` | Retrieve a secret |
| DELETE | `/api/v1/secrets/{secret_id}` | Delete a secret |
| GET | `/api/v1/secrets` | List secrets (filterable) |
| POST | `/api/v1/secrets/classify` | Classify secret format |

## Secret Classification

The system automatically detects format:

```python
from app.services import DetectedSecretClassifier

classifier = DetectedSecretClassifier()

# Check format
is_json = classifier.is_json_secret('{"key": "value"}')  # True
is_json = classifier.is_json_secret('sk-abc123')          # False
```

| Format | Example | Handled As |
|--------|---------|-----------|
| simple | `sk-abc123def456` | String |
| simple | `AIzaSyB_1234567890...` | String |
| json | `{"api_key": "..."}` | Dict (auto-parsed) |
| json | `[{"id": 1}]` | List (auto-parsed) |

## Supported Services

✅ OpenAI  
✅ Google Gemini  
✅ Stripe  
✅ AWS IAM  
✅ SendGrid  
✅ Any custom API  

## Error Handling

```python
from app.services.secret_manager import SecretRetrievalError

try:
    api_key = retrieve_api_key("openai", "production")
except SecretRetrievalError as e:
    print(f"Failed: {e}")
```

## AWS Configuration

### IAM Permissions

Attach: **`SecretsManagerReadWrite`** (AWS managed policy)

### Environment Variables

```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG+...
```

---

## Documentation Files

### Root Level
- **README.md** - This file (project overview)

### In `cloud-rotation-engine/docs/`
- **README.md** - Complete Secret Manager implementation guide
- **README_QUICK_START.md** - 5-minute quick start guide
- **ARCHITECTURE.md** - System architecture with diagrams
- **SECRET_MANAGER.md** - Detailed API reference

## Security Features

### Rotation Engine
✅ Least-privilege IAM scope  
✅ Immutable audit trails  
✅ No policy modifications  
✅ Deterministic workflows  

### Secret Manager
✅ AWS encryption at rest  
✅ TLS for all communications  
✅ IAM-based access control  
✅ Version history tracking  
✅ Recovery periods for deletion  
✅ Tag-based access policies  

---

## Implementation Statistics

| Component | Metric | Value |
|-----------|--------|-------|
| **Rotation Engine** | API Endpoints | 3 |
| | Pydantic Models | 3 |
| | Exception Classes | Custom types |
| **Secret Manager** | Main Service | 570 lines |
| | API Endpoints | 5 |
| | Pydantic Models | 5 |
| | Exception Classes | 3 |
| | Utility Functions | 4 |
| | Examples | 8 |
| | Documentation | 1,200+ lines |
| **Total** | Combined Code | 1,300+ lines |

---

## Optional Enhancements (Future)

### Rotation Engine
- [ ] Batch rotation for multiple compromised keys
- [ ] Key age-based rotation policies
- [ ] MFA-protected rotation (requires MFA device)
- [ ] Rotation latency dashboard
- [ ] Slack/email notifications on rotation
- [ ] Cross-account key rotation
- [ ] CloudTrail integration

### Secret Manager
- [ ] Automatic secret rotation scheduling
- [ ] Secret expiration alerts
- [ ] Real-time access audit logging
- [ ] Slack/email notifications
- [ ] Cross-region replication

---

## Project Structure

```
code-gaurd/
├── README.md                          # This file (project overview)
├── requirements.txt                   # Python dependencies
├── .env                               # Environment configuration
│
└── cloud-rotation-engine/
    ├── app/
    │   ├── main.py                    # FastAPI entry point
    │   ├── api/
    │   │   ├── routes.py              # All API endpoints
    │   │   └── schemas.py             # Pydantic models
    │   ├── services/
    │   │   ├── rotation_service.py    # Rotation orchestration
    │   │   ├── secret_manager.py      # Secret management (NEW)
    │   │   ├── secret_manager_examples.py  # Examples (NEW)
    │   │   ├── iam_validator.py       # Key validation
    │   │   ├── policy_classifier.py   # Policy classification
    │   │   └── audit_service.py       # Audit logging
    │   ├── core/
    │   │   ├── config.py              # Settings
    │   │   ├── logging_config.py      # Logging setup
    │   │   └── security.py            # Security utilities
    │   ├── models/
    │   │   └── incident_model.py      # Data models
    │   └── utils/
    │       ├── time_utils.py          # Time utilities
    │       └── error_handlers.py      # Error handling
    ├── tests/
    │   ├── test_rotation.py           # Rotation tests
    │   ├── test_validator.py          # Validator tests
    │   └── test_credentials.py        # Credential tests
    └── docs/
        ├── README.md                  # Secret Manager complete guide
        ├── README_QUICK_START.md      # Quick start (5 min)
        ├── ARCHITECTURE.md            # Architecture diagrams
        ├── SECRET_MANAGER.md          # Detailed API reference
        └── AWS_setup.md               # AWS configuration
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT

## Support

For issues and questions:

**Rotation Engine:**
1. Check logs in `cloud-rotation-engine/logs/rotation.log`
2. Review rotation troubleshooting in [cloud-rotation-engine/docs/README.md](cloud-rotation-engine/docs/README.md)

**Secret Manager:**
1. Check AWS connectivity: `python -c "import boto3; print(boto3.__version__)"`
2. Review [cloud-rotation-engine/docs/README_QUICK_START.md](cloud-rotation-engine/docs/README_QUICK_START.md)
3. File an issue with error details and AWS region

---

**Built with:** FastAPI • Boto3 • Pydantic • Pytest • AWS Secrets Manager
