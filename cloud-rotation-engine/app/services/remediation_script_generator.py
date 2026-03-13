"""
Service for generating remediation scripts and code snippets.
Creates storage scripts and retrieval code for different secret types and languages.
In the client-driven model, these scripts are executed locally by the developer.
"""
from app.utils.rule_mapping import get_service_from_rule, get_display_name
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RemediationScriptGenerator:
    """Generates scripts and code for local secret remediation"""
    
    # Template for AWS Secrets Manager storage (Python)
    STORAGE_SCRIPT_PYTHON = '''import boto3
import json

def store_secret():
    """
    Store the secret in AWS Secrets Manager.
    This script runs LOCALLY - the secret never touches external services.
    """
    client = boto3.client("secretsmanager", region_name="{region}")
    
    secret_name = "{secret_name}"
    secret_value = {secret_value_expr}
    
    try:
        # Try to create new secret
        response = client.create_secret(
            Name=secret_name,
            SecretString=json.dumps({{"value": secret_value}}),
            Description="Remediated secret from CodeGuard detection"
        )
        print(f"✓ Secret created: {{response['ARN']}}")
        return response
    except client.exceptions.ResourceExistsException:
        # If secret exists, update it
        response = client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps({{"value": secret_value}})
        )
        print(f"✓ Secret updated: {{response['ARN']}}")
        return response

if __name__ == "__main__":
    try:
        store_secret()
    except Exception as e:
        print(f"✗ Error: {{e}}")
        exit(1)
'''
    
    # Template for AWS Secrets Manager storage (JavaScript/Node.js)
    STORAGE_SCRIPT_JAVASCRIPT = '''const AWS = require('aws-sdk');

async function storeSecret() {{
  const client = new AWS.SecretsManager({{ region: "{region}" }});
  
  const secretName = "{secret_name}";
  const secretValue = {secret_value_expr};
  
  try {{
    // Try to create new secret
    const params = {{
      Name: secretName,
      SecretString: JSON.stringify({{ value: secretValue }}),
      Description: "Remediated secret from CodeGuard detection"
    }};
    
    try {{
      const response = await client.createSecret(params).promise();
      console.log(`✓ Secret created: ${{response.ARN}}`);
      return response;
    }} catch (error) {{
      if (error.code === "ResourceExistsException") {{
        // If secret exists, update it
        const updateParams = {{
          SecretId: secretName,
          SecretString: JSON.stringify({{ value: secretValue }})
        }};
        const response = await client.updateSecret(updateParams).promise();
        console.log(`✓ Secret updated: ${{response.ARN}}`);
        return response;
      }} else {{
        throw error;
      }}
    }}
  }} catch (error) {{
    console.error(`✗ Error: ${{error.message}}`);
    process.exit(1);
  }}
}}

if (require.main === module) {{
  storeSecret();
}}

module.exports = {{ storeSecret }};
'''
    
    # Template for AWS Secrets Manager storage (Go)
    STORAGE_SCRIPT_GO = '''package main

import (
	"encoding/json"
	"fmt"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/secretsmanager"
	"os"
)

func storeSecret() error {{
	sess, err := session.NewSession(&aws.Config{{
		Region: aws.String("{region}"),
	}})
	if err != nil {{
		return err
	}}
	
	client := secretsmanager.New(sess)
	
	secretName := "{secret_name}"
	secretValue := {secret_value_expr}
	
	secretData := map[string]interface{{{{
		"value": secretValue,
	}}
	
	jsonData, err := json.Marshal(secretData)
	if err != nil {{
		return err
	}}
	
	// Try to create new secret
	createinput := &secretsmanager.CreateSecretInput{{
		Name:         aws.String(secretName),
		SecretString: aws.String(string(jsonData)),
		Description:  aws.String("Remediated secret from CodeGuard detection"),
	}}
	
	response, err := client.CreateSecret(createInput)
	if err != nil {{
		if err.Error() == secretsmanager.ErrCodeResourceExistsException {{
			// If secret exists, update it
			updateInput := &secretsmanager.UpdateSecretInput{{
				SecretId:     aws.String(secretName),
				SecretString: aws.String(string(jsonData)),
			}}
			updateResponse, err := client.UpdateSecret(updateInput)
			if err != nil {{
				return err
			}}
			fmt.Printf("✓ Secret updated: %s\\n", *updateResponse.ARN)
			return nil
		}}
		return err
	}}
	
	fmt.Printf("✓ Secret created: %s\\n", *response.ARN)
	return nil
}}

func main() {{
	if err := storeSecret(); err != nil {{
		fmt.Fprintf(os.Stderr, "✗ Error: %v\\n", err)
		os.Exit(1)
	}}
}}
'''
    
    # Template for AWS Secrets Manager storage (Java)
    STORAGE_SCRIPT_JAVA = '''import software.amazon.awssdk.services.secretsmanager.SecretsManagerClient;
import software.amazon.awssdk.services.secretsmanager.model.CreateSecretRequest;
import software.amazon.awssdk.services.secretsmanager.model.CreateSecretResponse;
import software.amazon.awssdk.services.secretsmanager.model.UpdateSecretRequest;
import software.amazon.awssdk.services.secretsmanager.model.UpdateSecretResponse;
import software.amazon.awssdk.services.secretsmanager.model.ResourceExistsException;
import com.fasterxml.jackson.databind.ObjectMapper;

public class StoreSecret {{
    private static final ObjectMapper objectMapper = new ObjectMapper();
    
    public static void storeSecret() throws Exception {{
        try (SecretsManagerClient client = SecretsManagerClient.builder()
                .region(software.amazon.awssdk.regions.Region.of("{region}"))
                .build()) {{
            
            String secretName = "{secret_name}";
            String secretValue = {secret_value_expr};
            
            // Create JSON payload
            String jsonPayload = objectMapper.writeValueAsString(
                java.util.Map.of("value", secretValue)
            );
            
            try {{
                // Try to create new secret
                CreateSecretRequest createRequest = CreateSecretRequest.builder()
                        .name(secretName)
                        .secretString(jsonPayload)
                        .description("Remediated secret from CodeGuard detection")
                        .build();
                
                CreateSecretResponse createResponse = client.createSecret(createRequest);
                System.out.println("✓ Secret created: " + createResponse.arn());
                
            }} catch (ResourceExistsException e) {{
                // If secret exists, update it
                UpdateSecretRequest updateRequest = UpdateSecretRequest.builder()
                        .secretId(secretName)
                        .secretString(jsonPayload)
                        .build();
                
                UpdateSecretResponse updateResponse = client.updateSecret(updateRequest);
                System.out.println("✓ Secret updated: " + updateResponse.arn());
            }}
        }}
    }}
    
    public static void main(String[] args) {{
        try {{
            storeSecret();
        }} catch (Exception e) {{
            System.err.println("✗ Error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }}
    }}
}}
'''
    
    # Template for retrieval code (Python)
    RETRIEVAL_CODE_PYTHON = '''import boto3
import json

def get_secret(secret_name="{secret_name}", region="{region}"):
    """Retrieve secret from AWS Secrets Manager"""
    client = boto3.client("secretsmanager", region_name=region)
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response["SecretString"])
        return secret.get("value")
    except Exception as e:
        raise Exception(f"Failed to retrieve secret: {{e}}")

# Usage
{service_var} = get_secret()
'''
    
    # Template for retrieval code (JavaScript/Node.js)
    RETRIEVAL_CODE_JAVASCRIPT = '''const AWS = require('aws-sdk');

async function getSecret(secretName = "{secret_name}", region = "{region}") {{
  const client = new AWS.SecretsManager({{ region }});
  
  try {{
    const response = await client.getSecretValue({{ SecretId: secretName }}).promise();
    const secret = JSON.parse(response.SecretString);
    return secret.value;
  }} catch (error) {{
    throw new Error(`Failed to retrieve secret: ${{error.message}}`);
  }}
}}

// Usage
const {service_var} = await getSecret();
'''
    
    # Template for retrieval code (Go)
    RETRIEVAL_CODE_GO = '''package main

import (
	"encoding/json"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/secretsmanager"
)

func getSecret(secretName string, region string) (string, error) {{
	sess, err := session.NewSession(&aws.Config{{
		Region: aws.String(region),
	}})
	if err != nil {{
		return "", err
	}}
	
	client := secretsmanager.New(sess)
	input := &secretsmanager.GetSecretValueInput{{
		SecretId: aws.String(secretName),
	}}
	
	result, err := client.GetSecretValue(input)
	if err != nil {{
		return "", err
	}}
	
	var secret map[string]interface{{}}
	err = json.Unmarshal([]byte(*result.SecretString), &secret)
	if err != nil {{
		return "", err
	}}
	
	return secret["value"].(string), nil
}}

// Usage
func main() {{
	mySecret, err := getSecret("{secret_name}", "{region}")
	if err != nil {{
		panic(err)
	}}
	// Use mySecret...
}}
'''
    
    REMEDIATION_INSTRUCTIONS = '''
# Secret Remediation Workflow

## Step 1: Store Secret in AWS Secrets Manager

The following Python script stores your secret securely in AWS Secrets Manager.
**This script runs LOCALLY on your machine - the secret is never transmitted to the backend.**

```python
{storage_script}
```

**To execute:**
```bash
python store_secret.py
```

## Step 2: Update Your Code

Replace the hardcoded secret with the retrieval code:

**Before (INSECURE):**
```python
{service_var} = "hardcoded_secret_value"
```

**After (SECURE):**
```python
{retrieval_code}
```

## Step 3: Verify Storage

Confirm the secret was stored:
```bash
aws secretsmanager describe-secret --secret-id {secret_name} --region {region}
```

## Step 4: Log Completion

The system has already logged this incident. Once you complete the remediation steps above,
mark this incident as resolved in your audit dashboard.

---

**Security Benefits:**
- ✓ Secret stored in AWS Secrets Manager (encrypted at rest)
- ✓ Secret retrieved only when needed by your application
- ✓ Audit trail maintained of all access
- ✓ Secret can be rotated independently
- ✓ No hardcoded credentials in source code or version control
'''
    
    def __init__(self):
        self.region = "us-east-1"  # Default, can be overridden
    
    def generate_remediation_scripts(
        self,
        incident_id: str,
        secret_value: str,
        secret_type: str,
        service_name: str,
        language: str = "python",
        environment: str = "production",
        region: str = "us-east-1",
    ) -> dict:
        """
        Generate local remediation scripts for a detected secret.
        
        Args:
            incident_id: The incident UUID
            secret_value: The actual secret value (only available locally)
            secret_type: Type of secret (from rule mapping)
            service_name: Service name
            language: Language for retrieval code
            environment: Target environment
            region: AWS region
            
        Returns:
            Dict containing storage script, retrieval code, and instructions
        """
        try:
            # Generate secret name for AWS Secrets Manager
            secret_name = f"codeguard/{service_name}/{environment}"
            service_var = service_name.lower().replace("-", "_")
            
            # Generate storage script in specified language
            storage_script = self._generate_storage_script(
                secret_name=secret_name,
                secret_value=secret_value,
                language=language,
                region=region
            )
            
            # Generate retrieval code
            retrieval_code = self._generate_retrieval_code(
                secret_name=secret_name,
                service_var=service_var,
                language=language,
                region=region
            )
            
            # Generate instructions
            instructions = self._generate_instructions(
                storage_script=storage_script,
                retrieval_code=retrieval_code,
                secret_name=secret_name,
                service_var=service_var,
                region=region,
                language=language
            )
            
            return {
                "status": "success",
                "incident_id": incident_id,
                "storage_script": storage_script,
                "retrieval_code": retrieval_code,
                "instructions": instructions,
                "message": f"Remediation scripts generated for {service_name}",
            }
            
        except Exception as e:
            logger.error(f"Failed to generate remediation scripts: {e}")
            return {
                "status": "error",
                "incident_id": incident_id,
                "message": f"Script generation failed: {str(e)}",
            }
    
    def _generate_storage_script(
        self,
        secret_name: str,
        secret_value: str,
        language: str = "python",
        region: str = "us-east-1"
    ) -> str:
        """Generate storage script in specified language"""
        if secret_value.startswith('{') and secret_value.endswith('}'):
            # Already JSON
            secret_value_expr = secret_value
        else:
            # String value
            if language.lower() in ["javascript", "js", "node"]:
                secret_value_expr = f'"{secret_value}"'
            elif language.lower() == "go":
                secret_value_expr = f'"{secret_value}"'
            elif language.lower() == "java":
                secret_value_expr = f'"{secret_value}"'
            else:  # Python default
                secret_value_expr = f'"{secret_value}"'
        
        if language.lower() in ["javascript", "js", "node"]:
            script = self.STORAGE_SCRIPT_JAVASCRIPT.format(
                region=region,
                secret_name=secret_name,
                secret_value_expr=secret_value_expr
            )
        elif language.lower() == "go":
            script = self.STORAGE_SCRIPT_GO.format(
                region=region,
                secret_name=secret_name,
                secret_value_expr=secret_value_expr
            )
        elif language.lower() == "java":
            script = self.STORAGE_SCRIPT_JAVA.format(
                region=region,
                secret_name=secret_name,
                secret_value_expr=secret_value_expr
            )
        else:  # Python default
            script = self.STORAGE_SCRIPT_PYTHON.format(
                region=region,
                secret_name=secret_name,
                secret_value_expr=secret_value_expr
            )
        return script
    
    def _generate_retrieval_code(
        self,
        secret_name: str,
        service_var: str,
        language: str = "python",
        region: str = "us-east-1"
    ) -> str:
        """Generate language-specific retrieval code"""
        if language.lower() == "javascript" or language.lower() == "js" or language.lower() == "node":
            return self.RETRIEVAL_CODE_JAVASCRIPT.format(
                secret_name=secret_name,
                service_var=service_var,
                region=region
            )
        elif language.lower() == "go":
            return self.RETRIEVAL_CODE_GO.format(
                secret_name=secret_name,
                service_var=service_var,
                region=region
            )
        else:
            # Default to Python
            return self.RETRIEVAL_CODE_PYTHON.format(
                secret_name=secret_name,
                service_var=service_var,
                region=region
            )
    
    def _generate_instructions(
        self,
        storage_script: str,
        retrieval_code: str,
        secret_name: str,
        service_var: str,
        region: str = "us-east-1",
        language: str = "python"
    ) -> str:
        """Generate human-readable instructions"""
        return self.REMEDIATION_INSTRUCTIONS.format(
            storage_script=storage_script,
            retrieval_code=retrieval_code,
            secret_name=secret_name,
            service_var=service_var,
            region=region
        )
