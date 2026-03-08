#!/usr/bin/env python3
"""
Examples: Combined Store & Generate Code Endpoint

Shows how to store a secret and immediately get back retrieval code in one action.
"""

import json
import requests

API_URL = "http://localhost:8000/api/v1"

print("=" * 80)
print("EXAMPLE 1: Store Secret + Generate Python Code (One Action)")
print("=" * 80)

payload = {
    "secret_id": "codeguard/openai/production",
    "secret_value": "sk-proj-abc123def456ghi789",
    "service_name": "openai",
    "language": "python",
    "environment": "production",
    "description": "OpenAI API key for production"
}

print(f"\nRequest Payload:\n{json.dumps(payload, indent=2)}")

try:
    response = requests.post(
        f"{API_URL}/secrets/store-and-generate-code",
        json=payload,
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Success!")
        print(f"\nStorage Result:")
        print(f"  Secret ID: {result['secret_id']}")
        print(f"  Secret Type: {result['secret_type']}")
        print(f"  Message: {result['storage_message']}")
        print(f"\nGenerated Code ({result['language']}):")
        print(result['code'])
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.json())
except requests.exceptions.ConnectionError:
    print("✗ Cannot connect to API. Is uvicorn running?")


print("\n" + "=" * 80)
print("EXAMPLE 2: Store Credentials + Generate JavaScript Code")
print("=" * 80)

credentials_json = json.dumps({
    "api_key": "AIzaSyDJk8JkEFnBmhWEpI802c1HgfGHQE2az",
    "project_id": "my-project-123"
})

payload = {
    "secret_id": "codeguard/gemini/production",
    "secret_value": credentials_json,
    "service_name": "gemini",
    "language": "javascript",
    "environment": "production"
}

print(f"\nRequest Payload:\n{json.dumps(payload, indent=2)}")

try:
    response = requests.post(
        f"{API_URL}/secrets/store-and-generate-code",
        json=payload,
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Success!")
        print(f"\nStorage Result:")
        print(f"  Secret ID: {result['secret_id']}")
        print(f"  Secret Type: {result['secret_type']}")
        print(f"\nGenerated Code ({result['language']}):")
        print(result['code'][:300] + "...")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.json())
except requests.exceptions.ConnectionError:
    print("✗ Cannot connect to API")


print("\n" + "=" * 80)
print("EXAMPLE 3: Store Secret + Generate Go Code")
print("=" * 80)

payload = {
    "secret_id": "codeguard/stripe/production",
    "secret_value": "sk_live_4eC39HqLyjWDarht6zqp5pr7",
    "service_name": "stripe",
    "language": "go",
    "environment": "production"
}

print(f"\nRequest Payload:\n{json.dumps(payload, indent=2)}")

try:
    response = requests.post(
        f"{API_URL}/secrets/store-and-generate-code",
        json=payload,
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Success!")
        print(f"\nGenerated Code ({result['language']}):")
        print(result['code'][:300] + "...")
    else:
        print(f"✗ Error: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("✗ Cannot connect to API")


print("\n" + "=" * 80)
print("WORKFLOW COMPARISON")
print("=" * 80)

print("""
❌ OLD WORKFLOW (2 API calls):
   1. POST /api/v1/secrets/store
      → Returns: storage_id, version_id
   
   2. POST /api/v1/secrets/generate-code
      → Returns: code snippet
   
   Problem: Two separate API calls needed

✅ NEW WORKFLOW (1 API call):
   1. POST /api/v1/secrets/store-and-generate-code
      → Returns: storage_id, version_id, AND code snippet
   
   Advantage: Single atomic operation, instant code ready to use!
""")


print("\n" + "=" * 80)
print("SUPPORTED LANGUAGES")
print("=" * 80)

languages = [
    ("python", "py"),
    ("javascript", "js, node"),
    ("go", "go"),
    ("java", "java"),
    ("php", "php"),
    ("csharp", "cs"),
]

for lang, aliases in languages:
    payload = {
        "secret_id": "codeguard/test/prod",
        "secret_value": "test-secret-123",
        "service_name": "test",
        "language": lang,
        "environment": "production"
    }
    
    print(f"  • {lang.upper():12} ({aliases})")


print("\n" + "=" * 80)
print("CURL EXAMPLES")
print("=" * 80)

print("""
1. Python Code:
   curl -X POST http://localhost:8000/api/v1/secrets/store-and-generate-code \\
     -H "Content-Type: application/json" \\
     -d '{
       "secret_id": "codeguard/openai/production",
       "secret_value": "sk-abc123...",
       "service_name": "openai",
       "language": "python"
     }'

2. JavaScript Code:
   curl -X POST http://localhost:8000/api/v1/secrets/store-and-generate-code \\
     -H "Content-Type: application/json" \\
     -d '{
       "secret_id": "codeguard/gemini/production",
       "secret_value": "AIza...",
       "service_name": "gemini",
       "language": "javascript"
     }'

3. Go Code:
   curl -X POST http://localhost:8000/api/v1/secrets/store-and-generate-code \\
     -H "Content-Type: application/json" \\
     -d '{
       "secret_id": "codeguard/database/production",
       "secret_value": "postgres://user:pass@host/db",
       "service_name": "database",
       "language": "go"
     }'
""")

print("\n" + "=" * 80)
print("✓ Examples complete!")
print("=" * 80)
