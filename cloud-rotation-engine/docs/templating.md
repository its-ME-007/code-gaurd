# Secret Ingestion & Retrieval Template Pipeline

## Overview

This module implements a **secure secret ingestion pipeline** that accepts detected credentials from the detection engine, stores them securely in **AWS Secrets Manager**, and returns **language-specific code snippets** that developers can use to retrieve the stored secret safely.

The goal is to **replace hardcoded credentials in source code** with secure runtime retrieval from a managed secret store.

---

# Pipeline Flow

The pipeline executes the following steps:

```text
Detection Engine
      │
      ▼
Secret Ingestion API
      │
      ▼
Secret Storage Job (AWS Secrets Manager)
      │
      ▼
Language Template Generator
      │
      ▼
Developer Retrieval Snippet
```

---

# Step 1 — API Receives Secret Payload

The middleware exposes an API endpoint that accepts:

* detected secret
* service metadata
* source language of the user’s code

### Example Request

```json
{
  "secret_value": "AIzaSy...",
  "service": "gemini",
  "language": "py",
  "project_id": "project-alpha"
}
```

### Field Definitions

| Field          | Description                                |
| -------------- | ------------------------------------------ |
| `secret_value` | The detected API key or credential         |
| `service`      | The service associated with the credential |
| `language`     | Abbreviated language identifier            |
| `project_id`   | Project or repository identifier           |

---

# Step 2 — Secret Storage Job

The API invokes the **secret storage job**, which securely persists the credential in **AWS Secrets Manager**.

Example secret name structure:

```
codeguard/{service}/{project}
```

Example:

```
codeguard/gemini/project-alpha
```

### boto3 Storage Example

```python
client.create_secret(
    Name="codeguard/gemini/project-alpha",
    SecretString=json.dumps({
        "api_key": "AIzaSy..."
    })
)
```

Secrets are encrypted automatically using **AWS KMS**.

---

# Step 3 — Retrieval Template Generation

After the secret is stored successfully, the system generates a **language-specific code snippet** that developers can use to access the secret at runtime.

The snippet is generated using **predefined language templates**.

The template system maps language abbreviations to supported runtimes.

| Language Abbreviation | Runtime |
| --------------------- | ------- |
| `py`                  | Python  |
| `js`                  | Node.js |
| `go`                  | Go      |
| `java`                | Java    |
| `php`                 | PHP     |
| `cs`                  | C#      |

---

# Step 4 — Code Snippet Generation

The secret name is injected into the corresponding template.

Example Python template:

```python
import boto3
import json

client = boto3.client("secretsmanager")

response = client.get_secret_value(
    SecretId="codeguard/gemini/project-alpha"
)

secret = json.loads(response["SecretString"])
print(secret["api_key"])
```

Example Node.js template:

```javascript
const AWS = require("aws-sdk")

const client = new AWS.SecretsManager()

async function getSecret() {
  const response = await client.getSecretValue({
    SecretId: "codeguard/gemini/project-alpha"
  }).promise()

  const secret = JSON.parse(response.SecretString)
  console.log(secret.api_key)
}
```

---

# Step 5 — API Response

The API returns the generated snippet to the caller.

### Example Response

```json
{
  "status": "stored",
  "secret_name": "codeguard/gemini/project-alpha",
  "language": "python",
  "retrieval_snippet": "import boto3..."
}
```

---

# Secret Naming Convention

Secrets follow a **namespaced structure** for easier management.

```
codeguard/{service}/{project}
```

Examples:

```
codeguard/gemini/project-alpha
codeguard/firebase/backend
codeguard/stripe/payment-service
```

---

# Security Considerations

The system follows several security principles:

* Hardcoded credentials are **never returned**
* Only **secure retrieval snippets** are generated
* Secrets are encrypted using **AWS KMS**
* The pipeline prevents **direct exposure of stored credentials**

---

# Supported Secret Types

The system can store and manage various credential types:

```
AWS Access Keys
Gemini API Keys
Firebase Service Account JSON
Stripe API Keys
Database Credentials
```

All secrets are stored in **AWS Secrets Manager**.

---

# Future Enhancements

Planned improvements include:

* automatic IAM key rotation
* incident tracking
* secret risk scoring
* automated secret replacement in source code
* CI/CD pipeline integration
