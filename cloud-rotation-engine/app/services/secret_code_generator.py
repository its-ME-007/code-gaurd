"""
Code generator for AWS Secrets Manager secret retrieval.

Generates language-specific code snippets for accessing stored secrets.
Supports Python, JavaScript, Go, Java, PHP, and C#.
"""

from typing import Literal, Dict


class SecretCodeGenerator:
    """Generates language-specific code snippets for retrieving secrets."""
    
    # Supported languages
    SUPPORTED_LANGUAGES = {
        'py': 'python',
        'python': 'python',
        'js': 'javascript',
        'javascript': 'javascript',
        'node': 'javascript',
        'go': 'go',
        'java': 'java',
        'php': 'php',
        'cs': 'csharp',
        'csharp': 'csharp',
    }
    
    @staticmethod
    def generate_python(secret_id: str, region: str = "us-east-1") -> str:
        """Generate Python code snippet"""
        return f'''import boto3
import json
from botocore.exceptions import ClientError


def get_secret():
    """Retrieve secret from AWS Secrets Manager"""
    secret_name = "{secret_id}"
    region_name = "{region}"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    secret = get_secret_value_response['SecretString']
    secret_data = json.loads(secret)
    secret_value = secret_data['value']
    metadata = secret_data['metadata']
    
    if metadata['type'] == 'json':
        secret_value = json.loads(secret_value)
    
    return secret_value


secret = get_secret()
print(f"Retrieved secret: {{secret}}")
'''
    
    @staticmethod
    def generate_javascript(secret_id: str, region: str = "us-east-1") -> str:
        """Generate Node.js code snippet"""
        return f'''const AWS = require("aws-sdk")

const client = new AWS.SecretsManager({{
    region: "{region}"
}})

async function getSecret() {{
    try {{
        const response = await client.getSecretValue({{
            SecretId: "{secret_id}"
        }}).promise()

        const secret = JSON.parse(response.SecretString)
        let secretValue = secret.value
        const metadata = secret.metadata

        if (metadata.type === 'json') {{
            secretValue = JSON.parse(secretValue)
        }}

        return secretValue
    }} catch (error) {{
        console.error("Error retrieving secret:", error)
        throw error
    }}
}}

(async () => {{
    const secret = await getSecret()
    console.log("Retrieved secret:", secret)
}})()
'''
    
    @staticmethod
    def generate_go(secret_id: str, region: str = "us-east-1") -> str:
        """Generate Go code snippet"""
        return f'''package main

import (
    "encoding/json"
    "fmt"
    "log"
    "github.com/aws/aws-sdk-go/aws"
    "github.com/aws/aws-sdk-go/aws/session"
    "github.com/aws/aws-sdk-go/service/secretsmanager"
)

type SecretData struct {{
    Value    string            `json:"value"`
    Metadata map[string]string `json:"metadata"`
}}

func getSecret() (interface{{}}, error) {{
    secretName := "{secret_id}"
    region := "{region}"

    sess := session.Must(session.NewSession(&aws.Config{{
        Region: aws.String(region),
    }}))

    client := secretsmanager.New(sess)
    result, err := client.GetSecretValue(&secretsmanager.GetSecretValueInput{{
        SecretId: aws.String(secretName),
    }})

    if err != nil {{
        return nil, err
    }}

    var secretData SecretData
    err = json.Unmarshal([]byte(*result.SecretString), &secretData)
    if err != nil {{
        return nil, err
    }}

    if secretData.Metadata["type"] == "json" {{
        var jsonValue interface{{}}
        err = json.Unmarshal([]byte(secretData.Value), &jsonValue)
        return jsonValue, err
    }}

    return secretData.Value, nil
}}

func main() {{
    secret, err := getSecret()
    if err != nil {{
        log.Fatalf("Error: %v", err)
    }}
    fmt.Printf("Retrieved secret: %v\\n", secret)
}}
'''
    
    @staticmethod
    def generate_java(secret_id: str, region: str = "us-east-1") -> str:
        """Generate Java code snippet"""
        return f'''import com.amazonaws.services.secretsmanager.AWSSecretsManager;
import com.amazonaws.services.secretsmanager.AWSSecretsManagerClientBuilder;
import com.amazonaws.services.secretsmanager.model.GetSecretValueRequest;
import com.amazonaws.services.secretsmanager.model.GetSecretValueResult;
import org.json.JSONObject;

public class GetSecret {{
    public static Object getSecret() throws Exception {{
        String secretName = "{secret_id}";
        String region = "{region}";

        AWSSecretsManager client = AWSSecretsManagerClientBuilder.standard()
                .withRegion(region)
                .build();

        GetSecretValueRequest request = new GetSecretValueRequest()
                .withSecretId(secretName);

        GetSecretValueResult result = client.getSecretValue(request);
        String secret = result.getSecretString();
        JSONObject secretData = new JSONObject(secret);
        String secretValue = secretData.getString("value");
        JSONObject metadata = secretData.getJSONObject("metadata");

        if ("json".equals(metadata.getString("type"))) {{
            return new JSONObject(secretValue);
        }}

        return secretValue;
    }}

    public static void main(String[] arg) throws Exception {{
        Object secret = getSecret();
        System.out.println("Retrieved secret: " + secret);
    }}
}}
'''
    
    @staticmethod
    def generate_php(secret_id: str, region: str = "us-east-1") -> str:
        """Generate PHP code snippet"""
        return f'''<?php

require 'vendor/autoload.php';

use Aws\\SecretsManager\\SecretsManagerClient;
use Aws\\Exception\\AwsException;

function getSecret() {{
    $secretName = "{secret_id}";
    $region = "{region}";

    $client = new SecretsManagerClient([
        'region' => $region,
        'version' => 'latest'
    ]);

    try {{
        $result = $client->getSecretValue([
            'SecretId' => $secretName,
        ]);
    }} catch (AwsException $e) {{
        throw $e;
    }}

    $secret = $result['SecretString'];
    $secretData = json_decode($secret, true);
    $secretValue = $secretData['value'];
    $metadata = $secretData['metadata'];

    if ($metadata['type'] === 'json') {{
        $secretValue = json_decode($secretValue, true);
    }}

    return $secretValue;
}}

$secret = getSecret();
var_dump($secret);
?>
'''
    
    @staticmethod
    def generate_csharp(secret_id: str, region: str = "us-east-1") -> str:
        """Generate C# code snippet"""
        return f'''using Amazon;
using Amazon.SecretsManager;
using Amazon.SecretsManager.Model;
using Newtonsoft.Json.Linq;
using System;
using System.Threading.Tasks;

class Program {{
    static async Task Main(string[] args) {{
        var secret = await GetSecret();
        Console.WriteLine($"Retrieved secret: {{secret}}");
    }}

    static async Task<string> GetSecret() {{
        string secretName = "{secret_id}";
        string region = "{region}";

        using (var client = new AmazonSecretsManagerClient(RegionEndpoint.GetBySystemName(region))) {{
            var request = new GetSecretValueRequest {{
                SecretId = secretName,
            }};

            var response = await client.GetSecretValueAsync(request);
            var secretData = JObject.Parse(response.SecretString);
            var secretValue = secretData["value"].ToString();
            var metadata = (JObject)secretData["metadata"];

            if (metadata["type"].ToString() == "json") {{
                return secretData["value"].ToString();
            }}

            return secretValue;
        }}
    }}
}}
'''
    
    @staticmethod
    def generate_code(
        secret_id: str,
        language: str = "python",
        region: str = "us-east-1"
    ) -> str:
        """
        Generate code snippet in the specified language.
        
        Args:
            secret_id: Secret identifier (e.g., "codeguard/gemini/prod")
            language: Programming language (python, javascript, go, java, php, csharp)
            region: AWS region
            
        Returns:
            Code snippet as string
        """
        lang_lower = language.lower()
        if lang_lower not in SecretCodeGenerator.SUPPORTED_LANGUAGES:
            supported = ', '.join(SecretCodeGenerator.SUPPORTED_LANGUAGES.keys())
            raise ValueError(f"Unsupported language: {language}. Supported: {supported}")
        
        normalized_lang = SecretCodeGenerator.SUPPORTED_LANGUAGES[lang_lower]
        
        if normalized_lang == 'python':
            return SecretCodeGenerator.generate_python(secret_id, region)
        elif normalized_lang == 'javascript':
            return SecretCodeGenerator.generate_javascript(secret_id, region)
        elif normalized_lang == 'go':
            return SecretCodeGenerator.generate_go(secret_id, region)
        elif normalized_lang == 'java':
            return SecretCodeGenerator.generate_java(secret_id, region)
        elif normalized_lang == 'php':
            return SecretCodeGenerator.generate_php(secret_id, region)
        elif normalized_lang == 'csharp':
            return SecretCodeGenerator.generate_csharp(secret_id, region)
        else:
            raise ValueError(f"Language handler not implemented: {normalized_lang}")


def generate_code_for_secret(
    secret_id: str,
    language: str = "python",
    region: str = "us-east-1"
) -> str:
    """
    Quick function to generate code for a specific secret in any language.
    
    Args:
        secret_id: Secret identifier
        language: Programming language
        region: AWS region
        
    Returns:
        Code snippet as string
    """
    return SecretCodeGenerator.generate_code(secret_id, language, region)


# ============================================================================
# Batch Multi-Secret Code Generation Methods
# ============================================================================

class SecretCodeGeneratorBatch:
    """Generates language-specific code snippets for retrieving multiple secrets."""
    
    @staticmethod
    def generate_batch_python(secret_ids: list, region: str = "us-east-1") -> str:
        """Generate Python code snippet for batch secret retrieval"""
        secret_ids_str = ', '.join([f'"{sid}"' for sid in secret_ids])
        return f'''import boto3
import json
from botocore.exceptions import ClientError


def get_secrets(secret_ids):
    """
    Retrieve multiple secrets from AWS Secrets Manager.
    
    Args:
        secret_ids: List of secret identifiers to retrieve
        
    Returns:
        Dictionary with secret IDs as keys and secret values as values.
        Note: The 'language' field in stored metadata is for reference only.
    """
    region_name = "{region}"
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    results = {{}}
    errors = {{}}
    
    for secret_id in secret_ids:
        try:
            response = client.get_secret_value(SecretId=secret_id)
            secret = json.loads(response['SecretString'])
            secret_value = secret['value']
            metadata = secret['metadata']
            
            if metadata['type'] == 'json':
                secret_value = json.loads(secret_value)
            
            results[secret_id] = secret_value
        except ClientError as e:
            errors[secret_id] = str(e)
    
    return {{"results": results, "errors": errors}}


# Retrieve all secrets
secret_ids = [{secret_ids_str}]
all_secrets = get_secrets(secret_ids)

if all_secrets['errors']:
    print(f"Errors encountered: {{all_secrets['errors']}}")

print(f"Retrieved secrets: {{all_secrets['results']}}")
'''
    
    @staticmethod
    def generate_batch_javascript(secret_ids: list, region: str = "us-east-1") -> str:
        """Generate Node.js code snippet for batch secret retrieval"""
        secret_ids_str = ', '.join([f'"{sid}"' for sid in secret_ids])
        return f'''const AWS = require("aws-sdk")

const client = new AWS.SecretsManager({{
    region: "{region}"
}})

async function getSecrets(secretIds) {{
    /**
     * Retrieve multiple secrets from AWS Secrets Manager.
     * 
     * Args:
     *     secretIds: Array of secret identifiers to retrieve
     * 
     * Returns:
     *     Object with 'results' (successful secrets) and 'errors' (failed secrets).
     *     Note: The 'language' field in stored metadata is for reference only.
     */
    const results = {{}}
    const errors = {{}}
    
    for (const secretId of secretIds) {{
        try {{
            const response = await client.getSecretValue({{
                SecretId: secretId
            }}).promise()
            
            const secret = JSON.parse(response.SecretString)
            let secretValue = secret.value
            const metadata = secret.metadata
            
            if (metadata.type === 'json') {{
                secretValue = JSON.parse(secretValue)
            }}
            
            results[secretId] = secretValue
        }} catch (error) {{
            errors[secretId] = error.message
        }}
    }}
    
    return {{ results, errors }}
}}

(async () => {{
    const secretIds = [{secret_ids_str}]
    const allSecrets = await getSecrets(secretIds)
    
    if (Object.keys(allSecrets.errors).length > 0) {{
        console.error("Errors encountered:", allSecrets.errors)
    }}
    
    console.log("Retrieved secrets:", allSecrets.results)
}})()
'''
    
    @staticmethod
    def generate_batch_go(secret_ids: list, region: str = "us-east-1") -> str:
        """Generate Go code snippet for batch secret retrieval"""
        secret_ids_str = ', '.join([f'"{sid}"' for sid in secret_ids])
        return f'''package main

import (
    "encoding/json"
    "fmt"
    "log"
    "github.com/aws/aws-sdk-go/aws"
    "github.com/aws/aws-sdk-go/aws/session"
    "github.com/aws/aws-sdk-go/service/secretsmanager"
)

type SecretData struct {{
    Value    string            `json:"value"`
    Metadata map[string]string `json:"metadata"`
}}

type BatchResult struct {{
    Results map[string]interface{{}} `json:"results"`
    Errors  map[string]string       `json:"errors"`
}}

func getSecrets(secretIds []string) (*BatchResult, error) {{
    /*
     * Retrieve multiple secrets from AWS Secrets Manager.
     * 
     * Args:
     *     secretIds: Array of secret identifiers to retrieve
     * 
     * Returns:
     *     BatchResult with 'Results' (successful secrets) and 'Errors' (failed secrets).
     *     Note: The 'language' field in stored metadata is for reference only.
     */
    region := "{region}"
    sess := session.Must(session.NewSession(&aws.Config{{
        Region: aws.String(region),
    }}))

    client := secretsmanager.New(sess)
    
    results := make(map[string]interface{{}})
    errors := make(map[string]string)
    
    for _, secretId := range secretIds {{
        result, err := client.GetSecretValue(&secretsmanager.GetSecretValueInput{{
            SecretId: aws.String(secretId),
        }})
        
        if err != nil {{
            errors[secretId] = err.Error()
            continue
        }}
        
        var secretData SecretData
        err = json.Unmarshal([]byte(*result.SecretString), &secretData)
        if err != nil {{
            errors[secretId] = err.Error()
            continue
        }}
        
        if secretData.Metadata["type"] == "json" {{
            var jsonValue interface{{}}
            err = json.Unmarshal([]byte(secretData.Value), &jsonValue)
            if err == nil {{
                results[secretId] = jsonValue
            }} else {{
                results[secretId] = secretData.Value
            }}
        }} else {{
            results[secretId] = secretData.Value
        }}
    }}
    
    return &BatchResult{{
        Results: results,
        Errors:  errors,
    }}, nil
}}

func main() {{
    secretIds := []string{{{secret_ids_str}}}
    allSecrets, err := getSecrets(secretIds)
    if err != nil {{
        log.Fatalf("Error: %v", err)
    }}
    
    if len(allSecrets.Errors) > 0 {{
        fmt.Println("Errors encountered:", allSecrets.Errors)
    }}
    
    fmt.Println("Retrieved secrets:", allSecrets.Results)
}}
'''
    
    @staticmethod
    def generate_batch_java(secret_ids: list, region: str = "us-east-1") -> str:
        """Generate Java code snippet for batch secret retrieval"""
        secret_ids_str = ', '.join([f'"{sid}"' for sid in secret_ids])
        return f'''import com.amazonaws.services.secretsmanager.AWSSecretsManager;
import com.amazonaws.services.secretsmanager.AWSSecretsManagerClientBuilder;
import com.amazonaws.services.secretsmanager.model.GetSecretValueRequest;
import com.amazonaws.services.secretsmanager.model.GetSecretValueResult;
import org.json.JSONObject;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class GetSecrets {{
    public static class BatchResult {{
        public Map<String, Object> results;
        public Map<String, String> errors;
        
        public BatchResult() {{
            this.results = new HashMap<>();
            this.errors = new HashMap<>();
        }}
    }}
    
    public static BatchResult getSecrets(List<String> secretIds) throws Exception {{
        /*
         * Retrieve multiple secrets from AWS Secrets Manager.
         * 
         * Note: The 'language' field in stored metadata is for reference only.
         */
        String region = "{region}";
        
        AWSSecretsManager client = AWSSecretsManagerClientBuilder.standard()
                .withRegion(region)
                .build();
        
        BatchResult batchResult = new BatchResult();
        
        for (String secretId : secretIds) {{
            try {{
                GetSecretValueRequest request = new GetSecretValueRequest()
                        .withSecretId(secretId);
                
                GetSecretValueResult result = client.getSecretValue(request);
                String secret = result.getSecretString();
                JSONObject secretData = new JSONObject(secret);
                String secretValue = secretData.getString("value");
                JSONObject metadata = secretData.getJSONObject("metadata");
                
                if ("json".equals(metadata.getString("type"))) {{
                    batchResult.results.put(secretId, new JSONObject(secretValue));
                }} else {{
                    batchResult.results.put(secretId, secretValue);
                }}
            }} catch (Exception e) {{
                batchResult.errors.put(secretId, e.getMessage());
            }}
        }}
        
        return batchResult;
    }}
    
    public static void main(String[] args) throws Exception {{
        List<String> secretIds = Arrays.asList({secret_ids_str});
        BatchResult allSecrets = getSecrets(secretIds);
        
        if (!allSecrets.errors.isEmpty()) {{
            System.out.println("Errors encountered: " + allSecrets.errors);
        }}
        
        System.out.println("Retrieved secrets: " + allSecrets.results);
    }}
}}
'''
    
    @staticmethod
    def generate_batch_php(secret_ids: list, region: str = "us-east-1") -> str:
        """Generate PHP code snippet for batch secret retrieval"""
        secret_ids_str = ', '.join([f'"{sid}"' for sid in secret_ids])
        return f'''<?php

require 'vendor/autoload.php';

use Aws\\SecretsManager\\SecretsManagerClient;
use Aws\\Exception\\AwsException;

function getSecrets($secretIds) {{
    /**
     * Retrieve multiple secrets from AWS Secrets Manager.
     * 
     * Args:
     *     $secretIds: Array of secret identifiers to retrieve
     * 
     * Returns:
     *     Array with 'results' (successful secrets) and 'errors' (failed secrets).
     *     Note: The 'language' field in stored metadata is for reference only.
     */
    $region = "{region}";
    
    $client = new SecretsManagerClient([
        'region' => $region,
        'version' => 'latest'
    ]);
    
    $results = [];
    $errors = [];
    
    foreach ($secretIds as $secretId) {{
        try {{
            $result = $client->getSecretValue([
                'SecretId' => $secretId,
            ]);
            
            $secret = $result['SecretString'];
            $secretData = json_decode($secret, true);
            $secretValue = $secretData['value'];
            $metadata = $secretData['metadata'];
            
            if ($metadata['type'] === 'json') {{
                $secretValue = json_decode($secretValue, true);
            }}
            
            $results[$secretId] = $secretValue;
        }} catch (AwsException $e) {{
            $errors[$secretId] = $e->getMessage();
        }}
    }}
    
    return [
        'results' => $results,
        'errors' => $errors,
    ];
}}

$secretIds = [{secret_ids_str}];
$allSecrets = getSecrets($secretIds);

if (!empty($allSecrets['errors'])) {{
    echo "Errors encountered: " . json_encode($allSecrets['errors']) . "\\n";
}}

echo "Retrieved secrets: " . json_encode($allSecrets['results']) . "\\n";
?>
'''
    
    @staticmethod
    def generate_batch_csharp(secret_ids: list, region: str = "us-east-1") -> str:
        """Generate C# code snippet for batch secret retrieval"""
        secret_ids_str = ', '.join([f'"{sid}"' for sid in secret_ids])
        return f'''using Amazon;
using Amazon.SecretsManager;
using Amazon.SecretsManager.Model;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

class Program {{
    public class BatchResult {{
        public Dictionary<string, object> Results {{ get; set; }}
        public Dictionary<string, string> Errors {{ get; set; }}
        
        public BatchResult() {{
            Results = new Dictionary<string, object>();
            Errors = new Dictionary<string, string>();
        }}
    }}
    
    static async Task Main(string[] args) {{
        var secret = await GetSecrets(new List<string> {{{secret_ids_str}}});
        
        if (secret.Errors.Any()) {{
            Console.WriteLine($"Errors encountered: {{string.Join(", ", secret.Errors)}}");
        }}
        
        Console.WriteLine($"Retrieved secrets: {{string.Join(", ", secret.Results)}}");
    }}
    
    static async Task<BatchResult> GetSecrets(List<string> secretIds) {{
        /*
         * Retrieve multiple secrets from AWS Secrets Manager.
         * 
         * Note: The 'language' field in stored metadata is for reference only.
         */
        string region = "{region}";
        var batchResult = new BatchResult();
        
        using (var client = new AmazonSecretsManagerClient(RegionEndpoint.GetBySystemName(region))) {{
            foreach (var secretId in secretIds) {{
                try {{
                    var request = new GetSecretValueRequest {{
                        SecretId = secretId,
                    }};
                    
                    var response = await client.GetSecretValueAsync(request);
                    var secretData = JObject.Parse(response.SecretString);
                    var secretValue = secretData["value"].ToString();
                    var metadata = (JObject)secretData["metadata"];
                    
                    if (metadata["type"].ToString() == "json") {{
                        batchResult.Results[secretId] = JObject.Parse(secretValue);
                    }} else {{
                        batchResult.Results[secretId] = secretValue;
                    }}
                }} catch (Exception e) {{
                    batchResult.Errors[secretId] = e.Message;
                }}
            }}
        }}
        
        return batchResult;
    }}
}}
'''
    
    @staticmethod
    def generate_batch_code(
        secret_ids: list,
        language: str = "python",
        region: str = "us-east-1"
    ) -> str:
        """
        Generate unified code snippet for retrieving multiple secrets.
        
        Args:
            secret_ids: List of secret identifiers to retrieve
            language: Programming language (python, javascript, go, java, php, csharp)
            region: AWS region
            
        Returns:
            Code snippet as string with helper function for batch retrieval
        """
        lang_lower = language.lower()
        if lang_lower not in SecretCodeGenerator.SUPPORTED_LANGUAGES:
            supported = ', '.join(SecretCodeGenerator.SUPPORTED_LANGUAGES.keys())
            raise ValueError(f"Unsupported language: {language}. Supported: {supported}")
        
        normalized_lang = SecretCodeGenerator.SUPPORTED_LANGUAGES[lang_lower]
        
        if normalized_lang == 'python':
            return SecretCodeGeneratorBatch.generate_batch_python(secret_ids, region)
        elif normalized_lang == 'javascript':
            return SecretCodeGeneratorBatch.generate_batch_javascript(secret_ids, region)
        elif normalized_lang == 'go':
            return SecretCodeGeneratorBatch.generate_batch_go(secret_ids, region)
        elif normalized_lang == 'java':
            return SecretCodeGeneratorBatch.generate_batch_java(secret_ids, region)
        elif normalized_lang == 'php':
            return SecretCodeGeneratorBatch.generate_batch_php(secret_ids, region)
        elif normalized_lang == 'csharp':
            return SecretCodeGeneratorBatch.generate_batch_csharp(secret_ids, region)
        else:
            raise ValueError(f"Language handler not implemented: {normalized_lang}")


__all__ = [
    'SecretCodeGenerator',
    'SecretCodeGeneratorBatch',
    'generate_code_for_secret',
]
