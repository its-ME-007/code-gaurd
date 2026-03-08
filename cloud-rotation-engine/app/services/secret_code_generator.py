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


__all__ = [
    'SecretCodeGenerator',
    'generate_code_for_secret',
]
