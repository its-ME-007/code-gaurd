# Secret Storage & Multi-API Key Handling

## Overview

The rotation and remediation layer supports **secure storage and management of multiple API keys** using **AWS Secrets Manager**.

While AWS IAM keys can be **rotated automatically**, external API keys (such as Gemini, Stripe, or other third-party services) can be **securely stored and retrieved**, but their rotation depends on the respective provider's API.

This module provides a **centralized secret storage interface** that allows the system to safely manage credentials detected by the secret detection engine.

---

# Supported Secret Types

The system currently supports handling of the following credential categories:

| Secret Type                              | Handling Strategy                     |
| ---------------------------------------- | ------------------------------------- |
| AWS IAM Access Keys                      | Automatic rotation via IAM APIs       |
| External API Keys (Gemini, Stripe, etc.) | Secure storage in AWS Secrets Manager |
| Application Credentials                  | Secure storage and retrieval          |

---

# AWS Permissions Required

The rotation engine requires permissions to both:

1. **Rotate AWS IAM credentials**
2. **Store and manage secrets**

### IAM Rotation Permissions

```json
iam:CreateAccessKey
iam:DeleteAccessKey
iam:UpdateAccessKey
iam:ListAccessKeys
iam:ListAttachedUserPolicies
iam:ListUserPolicies
```

### Secrets Manager Permissions

```json
secretsmanager:CreateSecret
secretsmanager:PutSecretValue
secretsmanager:UpdateSecret
secretsmanager:GetSecretValue
```

Alternatively, the AWS managed policy can be used:

```
SecretsManagerReadWrite
```

---

# Secret Storage Model

Secrets are stored using **namespaced identifiers** to organize credentials by service.

Example structure:

```
codeguard/aws/dev-user
codeguard/gemini/project-x
codeguard/stripe/backend
```

Each secret contains a structured JSON payload.

Example:

```json
{
  "service": "gemini",
  "api_key": "AIza...",
  "managed_by": "codeguard-rotation-engine",
  "timestamp": "2026-03-07"
}
```

---

# Handling Multiple API Keys

AWS Secrets Manager supports:

* multiple secrets
* secret versioning
* secret updates

This allows the system to manage credentials for multiple services simultaneously.

Example services supported:

```
AWS IAM
Google Gemini
Stripe
SendGrid
Custom API credentials
```

---

# Secret Retrieval

Applications can retrieve stored secrets using **boto3**.

Example:

```python
import boto3
import json

client = boto3.client("secretsmanager")

response = client.get_secret_value(
    SecretId="codeguard/gemini/project-x"
)

secret = json.loads(response["SecretString"])
print(secret["api_key"])
```

---

# Credential Handling Workflow

The system processes detected secrets using the following pipeline:

```
Detection Engine
      │
      ▼
Secret Classification Layer
      │
      ├── AWS IAM Keys
      │        │
      │        ▼
      │   Rotate via IAM API
      │        │
      │        ▼
      │   Store rotated key in Secrets Manager
      │
      └── External API Keys
               │
               ▼
        Store securely in Secrets Manager
               │
               ▼
        Suggest provider-side rotation
```

---

# Important Notes

* **AWS IAM keys can be rotated automatically** using AWS APIs.
* **External API keys cannot be rotated automatically** unless their provider exposes a rotation API.
* Secrets Manager is used as the **central secure storage layer** for all detected credentials.

---

# Security Considerations

The system follows the **principle of least privilege** and avoids granting unnecessary IAM permissions.

Best practices implemented:

* Compromised keys are **not stored permanently**
* Only **new rotated keys** are saved
* Secrets are **namespaced per service**
* Access is controlled through **AWS IAM policies**

---

# Future Improvements

Planned enhancements include:

* automatic integration with CI/CD pipelines
* secret age analysis
* secret risk scoring
* automated remediation workflows
* cross-service secret rotation where provider APIs allow it

---
