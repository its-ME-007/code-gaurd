# ☁️ Cloud Key Rotation Engine

Automated AWS IAM Access Key Lifecycle Manager.

This service receives a detected AWS access key exposure, validates the key, rotates it securely, classifies IAM privilege level, and returns structured remediation data for downstream systems (Compliance Engine + Mobile Dashboard).

---

# 🎯 Purpose

This module acts as the remediation backbone of the system.

When an AWS key is exposed:

1. Validate the IAM user
2. Inspect attached policies
3. Create a new access key
4. Deactivate old key
5. Delete old key
6. Return structured audit response

No AI is used for execution logic — this is deterministic cloud automation.

---

# 🧰 Tech Stack

- Python 3.9+
- FastAPI
- boto3
- AWS IAM

---

# 📦 Installation

## 1️⃣ Clone Repository

```bash
git clone <repo-url>
cd cloud-rotation-engine
```

---

## 2️⃣ Create Virtual Environment

Mac/Linux:
```bash
python -m venv venv
source venv/bin/activate
```

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔐 AWS CONSOLE SETUP (FULL STEPS)

You must create:

- 1 IAM user to act as rotation service
- 1 IAM demo user whose keys will be rotated

---

# ✅ PART A — Create Rotation Service User

This user performs key rotation.

---

## Step 1 — Log in to AWS

Go to:

https://console.aws.amazon.com/

---

## Step 2 — Open IAM

- Search "IAM"
- Click IAM

---

## Step 3 — Create User

1. Click **Users**
2. Click **Create user**
3. Username:

```
rotation-service-user
```

4. Select:
   - ✅ Programmatic access

Click **Next**

---

## Step 4 — Attach Permissions

Choose:

Attach policies directly

For hackathon simplicity:
- Attach: IAMFullAccess

OR (Recommended Minimal Permissions):

Create custom policy with:

- iam:CreateAccessKey
- iam:DeleteAccessKey
- iam:UpdateAccessKey
- iam:ListAccessKeys
- iam:ListAttachedUserPolicies
- iam:ListUserPolicies
- iam:GetUser

Attach that custom policy.

Click **Next → Create user**

---

## Step 5 — Create Access Keys

After creation:

1. Click the user
2. Go to **Security credentials**
3. Click **Create access key**
4. Choose:
   - Application running outside AWS
5. Create key
6. Copy:

AWS_ACCESS_KEY_ID  
AWS_SECRET_ACCESS_KEY  

⚠️ Save them securely — you won’t see secret again.

---

# ✅ PART B — Create Demo IAM User (Target User)

This user simulates compromised credentials.

---

## Step 1 — Create User

1. Go to IAM → Users
2. Click **Create user**
3. Username:

```
demo-user
```

4. Select:
   - Programmatic access

Click Next

---

## Step 2 — Attach Policy

For strong demo impact:

Attach:
- AdministratorAccess

OR
- PowerUserAccess

Click Create user.

---

## Step 3 — Create Access Key for Demo User

1. Open demo-user
2. Security credentials
3. Create access key
4. Save:

DEMO_ACCESS_KEY_ID  
DEMO_SECRET_ACCESS_KEY  

This key will be “detected” and rotated.

---

# 🔑 Environment Configuration

Create a `.env` file in project root:

```
AWS_ACCESS_KEY_ID=<rotation_service_user_key>
AWS_SECRET_ACCESS_KEY=<rotation_service_secret>
AWS_REGION=us-east-1
DRY_RUN=false
```

---

# 🛡 Demo Safe Mode

To simulate rotation without deleting keys:

```
DRY_RUN=true
```

In this mode:

- No key is deleted
- Rotation is simulated
- Response is still returned
- Safe for live demo

---

# ▶️ Running the Service

Start server:

```bash
uvicorn app.main:app --reload
```

Server runs at:

http://127.0.0.1:8000

---

# 🩺 Health Check

GET /health

Expected:

```json
{
  "status": "ok"
}
```

---

# 🔄 Rotation API

## Endpoint

POST /rotate

---

## Sample Request

```json
{
  "iam_user": "demo-user",
  "access_key_id": "AKIAxxxxxxxx",
  "incident_id": "inc-123",
  "risk_level": "critical"
}
```

---

## Sample Successful Response

```json
{
  "status": "success",
  "rotation_completed": true,
  "iam_user": "demo-user",
  "old_key_deactivated": true,
  "new_key_id": "AKIAyyyyyyyy",
  "policy_level": "AdministratorAccess",
  "rotation_time_ms": 472
}
```

---

# 🧪 Test Using cURL

```bash
curl -X POST http://127.0.0.1:8000/rotate \
-H "Content-Type: application/json" \
-d '{
  "iam_user": "demo-user",
  "access_key_id": "AKIAxxxxxxxx",
  "incident_id": "inc-123",
  "risk_level": "critical"
}'
```

---

# 📊 Privilege Classification Logic

Policy levels are determined deterministically:

- AdministratorAccess → CRITICAL
- PowerUserAccess → HIGH
- Custom policies → MEDIUM

---

# 🔥 End-to-End Flow

1. Secret Detection Engine detects exposed AWS key  
2. Rotation Engine receives incident  
3. IAM user validated  
4. New key created  
5. Old key deactivated + deleted  
6. Policy classified  
7. Structured response returned  
8. Compliance engine + dashboard updated  

---

# ⚠️ Important Security Notes

- Never use root account credentials  
- Always use dedicated IAM users  
- Enable DRY_RUN during development  
- Limit IAM permissions where possible  
- Rotate demo keys after hackathon  

---