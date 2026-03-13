#!/usr/bin/env python3
"""
Examples: Secret Code Generator

Shows how to generate Python code snippets for retrieving secrets.
"""

import json
from app.services.secret_code_generator import SecretCodeGenerator, generate_code_for_secret


def example_1_convenience_function():
    """Generate code using convenience functions (simplest)"""
    print("=" * 80)
    print("EXAMPLE 1: Convenience Function (Recommended for Simple Use)")
    print("=" * 80)
    
    gen = SecretCodeGenerator()
    code = gen.generate_convenience_function_code(
        secret_id="codeguard/openai/production",
        secret_type="simple"
    )
    
    print("\nGenerated Code:")
    print(code)
    print()


def example_2_service_wrapper():
    """Generate code using service wrapper (more features)"""
    print("=" * 80)
    print("EXAMPLE 2: Service Wrapper (More Control)")
    print("=" * 80)
    
    gen = SecretCodeGenerator()
    code = gen.generate_service_wrapper_code(
        secret_id="codeguard/gemini/production",
        auto_parse=True,
        include_imports=True
    )
    
    print("\nGenerated Code:")
    print(code)
    print()


def example_3_raw_boto3_with_errors():
    """Generate raw boto3 code with full error handling"""
    print("=" * 80)
    print("EXAMPLE 3: Raw Boto3 with Error Handling")
    print("=" * 80)
    
    gen = SecretCodeGenerator()
    code = gen.generate_raw_boto3_code(
        secret_id="codeguard/stripe/prod",
        region="us-east-1",
        include_error_handling=True
    )
    
    print("\nGenerated Code:")
    print(code)
    print()


def example_4_raw_boto3_simple():
    """Generate minimal raw boto3 code"""
    print("=" * 80)
    print("EXAMPLE 4: Raw Boto3 (Minimal)")
    print("=" * 80)
    
    gen = SecretCodeGenerator()
    code = gen.generate_raw_boto3_code(
        secret_id="codeguard/sendgrid/dev",
        region="us-east-1",
        include_error_handling=False
    )
    
    print("\nGenerated Code:")
    print(code)
    print()


def example_5_all_patterns():
    """Generate all patterns for a single secret"""
    print("=" * 80)
    print("EXAMPLE 5: All Patterns for One Secret")
    print("=" * 80)
    
    secret_id = "codeguard/database/production"
    
    patterns = SecretCodeGenerator.generate_all_patterns(secret_id)
    
    for pattern_name, code_snippet in patterns.items():
        print(f"\n--- {pattern_name} ---")
        print(code_snippet[:200] + "..." if len(code_snippet) > 200 else code_snippet)


def example_6_quick_function():
    """Use the quick function"""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Quick Function Helper")
    print("=" * 80)
    
    code = generate_code_for_secret(
        secret_id="codeguard/aws/rotation-service",
        pattern="convenience"
    )
    
    print("\nGenerated Code:")
    print(code)
    print()


def example_7_rest_api():
    """Show how to use via REST API"""
    print("=" * 80)
    print("EXAMPLE 7: Use via REST API")
    print("=" * 80)
    
    print("""
1. Request (convenience pattern):
   curl -X POST http://localhost:8000/api/v1/secrets/generate-code \\
     -H "Content-Type: application/json" \\
     -d '{
       "secret_id": "codeguard/openai/production",
       "pattern": "convenience"
     }'

2. Request (raw boto3 with error handling):
   curl -X POST http://localhost:8000/api/v1/secrets/generate-code \\
     -H "Content-Type: application/json" \\
     -d '{
       "secret_id": "codeguard/gemini/production",
       "pattern": "raw_boto3",
       "region": "us-east-1",
       "include_error_handling": true
     }'

3. Request (service wrapper):
   curl -X POST http://localhost:8000/api/v1/secrets/generate-code \\
     -H "Content-Type: application/json" \\
     -d '{
       "secret_id": "codeguard/stripe/production",
       "pattern": "service_wrapper"
     }'

Response:
{
  "status": "success",
  "secret_id": "codeguard/openai/production",
  "pattern": "convenience",
  "code": "from app.services import retrieve_api_key\\n\\napi_key = retrieve_api_key(\\n    service_name=\\"openai\\",\\n    environment=\\"production\\"\\n)\\n\\nprint(f\\"API Key: {{api_key}}\\")",
  "language": "python",
  "message": "Code generated using convenience pattern"
}
""")


def pattern_comparison():
    """Compare all three patterns for the same secret"""
    print("\n" + "=" * 80)
    print("PATTERN COMPARISON")
    print("=" * 80)
    
    secret_id = "codeguard/example/prod"
    
    print("""
┌─────────────────────────────────────────────────────────────────────────────────┐
│ PATTERN           │ USE CASE                   │ LINES │ COMPLEXITY              │
├─────────────────────────────────────────────────────────────────────────────────┤
│ convenience       │ Simple get/set operations  │ 3-5   │ Very low ✓              │
│ service_wrapper   │ Full control + metadata    │ 8-12  │ Low-Medium              │
│ raw_boto3         │ No dependencies needed     │ 15-20 │ Medium (more boilerplate)│
└─────────────────────────────────────────────────────────────────────────────────┘

RECOMMENDATIONS:

✅ Use convenience for:
   - Simple API keys (OpenAI, Stripe, Gemini, etc.)
   - Quick integrations
   - Most common use cases

✅ Use service_wrapper for:
   - Accessing metadata (service, timestamp, etc.)
   - Conditional logic based on secret type
   - Error handling with proper context

✅ Use raw_boto3 for:
   - Standalone scripts without app dependencies
   - Minimal dependencies required
   - Custom error handling logic
""")


if __name__ == "__main__":
    example_1_convenience_function()
    example_2_service_wrapper()
    example_3_raw_boto3_with_errors()
    example_4_raw_boto3_simple()
    example_5_all_patterns()
    example_6_quick_function()
    example_7_rest_api()
    pattern_comparison()
    
    print("\n" + "=" * 80)
    print("✓ All examples completed!")
    print("=" * 80)
