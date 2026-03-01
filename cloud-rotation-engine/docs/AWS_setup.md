# ☁️ Cloud Key Rotation Engine

Automated AWS IAM Access Key Lifecycle Manager.

This service receives a detected secret incident, validates the exposed AWS access key, rotates it securely, and returns structured remediation data for downstream systems (compliance engine + mobile dashboard).

---

# 🚀 Features

- AWS IAM Access Key validation
- Automated key rotation (create → deactivate → delete)
- Policy privilege classification
- Structured remediation response
- DRY_RUN mode for safe demo
- FastAPI-based microservice

---

# 🏗 Architecture Overview

Secret Detection Engine  
        ↓  
Cloud Key Rotation Engine  
        ↓  
Compliance Engine  
        ↓  
Mobile Dashboard  

This service is deterministic and does not rely on AI for execution logic.

---

# 🧰 Tech Stack

- Python
- FastAPI
- boto3
- AWS IAM

---

# 📦 Installation

## 1. Clone Repository

```bash
git clone <repo-url>
cd cloud-rotation-engine