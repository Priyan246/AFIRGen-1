# AWS Secrets Manager Implementation Guide

## Overview

This document describes the AWS Secrets Manager integration for AFIRGen, which provides secure secret management for production deployments while maintaining backward compatibility with environment variables for local development.

## Features

- **Automatic AWS Integration**: Seamlessly fetches secrets from AWS Secrets Manager in production
- **Environment Variable Fallback**: Uses environment variables for local development
- **Caching**: Minimizes AWS API calls with configurable TTL (default: 5 minutes)
- **Secret Bundles**: Support for storing multiple secrets in a single JSON object
- **Error Handling**: Graceful fallback and detailed error logging
- **Zero Code Changes**: Existing code continues to work with minimal modifications

## Architecture

### Components

1. **SecretsManager Class** (`secrets_manager.py`)
   - Core secrets management functionality
   - AWS Secrets Manager client initialization
   - Caching layer
   - Fallback logic

2. **Integration Points**
   - `agentv5.py`: Main backend configuration
   - Environment variables: `.env` file
   - Docker: `docker-compose.yaml`

### Secret Resolution Flow

```
1. Check cache (if not expired)
   ↓
2. Try AWS Secrets Manager (if enabled)
   ↓
3. Fallback to environment variable
   ↓
4. Return default value (if provided)
   ↓
5. Raise error (if required and not found)
```

## Configuration

### Environment Variables

Add to `.env` file:

```bash
# AWS Configuration
AWS_REGION=us-east-1
ENVIRONMENT=production  # Enables AWS Secrets Manager
USE_AWS_SECRETS=true    # Optional: force enable/disable

# For local development, keep existing env vars:
MYSQL_PASSWORD=password
API_KEY=your-api-key
FIR_AUTH_KEY=your-auth-key
```

### AWS Secrets Manager Setup

#### Option 1: Individual Secrets

Create individual secrets in AWS Secrets Manager:

```bash
# Using AWS CLI
aws secretsmanager create-secret \
    --name MYSQL_PASSWORD \
    --secret-string "your-secure-password" \
    --region us-east-1

aws secretsmanager create-secret \
    --name API_KEY \
    --secret-string "your-secure-api-key" \
    --region us-east-1

aws secretsmanager create-secret \
    --name FIR_AUTH_KEY \
    --secret-string "your-secure-auth-key" \
    --region us-east-1
```

#### Option 2: Secret Bundle (Recommended)

Store all secrets in a single JSON object:

```bash
aws secretsmanager create-secret \
    --name afirgen/production/secrets \
    --secret-string '{
        "MYSQL_PASSWORD": "your-secure-password",
        "API_KEY": "your-secure-api-key",
        "FIR_AUTH_KEY": "your-secure-auth-key",
        "MYSQL_USER": "afirgen_user",
        "MYSQL_DB": "fir_db"
    }' \
    --region us-east-1
```

To use secret bundles, update `agentv5.py`:

```python
from secrets_manager import get_secret_bundle

# Load all secrets at once
secrets = get_secret_bundle("afirgen/production/secrets")

CFG = {
    "mysql": {
        "user": secrets.get("MYSQL_USER", "root"),
        "password": secrets["MYSQL_PASSWORD"],
        "database": secrets.get("MYSQL_DB", "fir_db"),
        # ...
    },
    "auth_key": secrets["FIR_AUTH_KEY"],
    "api_key": secrets["API_KEY"],
}
```

### IAM Permissions

The ECS task role or EC2 instance role needs these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": [
                "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:MYSQL_PASSWORD-*",
                "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:API_KEY-*",
                "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:FIR_AUTH_KEY-*"
            ]
        }
    ]
}
```

Or for secret bundles:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:afirgen/production/secrets-*"
        }
    ]
}
```

## Usage

### Basic Usage

```python
from secrets_manager import get_secret

# Get a required secret (raises error if not found)
db_password = get_secret("MYSQL_PASSWORD")

# Get an optional secret with default
api_timeout = get_secret("API_TIMEOUT", default="30")

# Get a non-required secret
optional_key = get_secret("OPTIONAL_KEY", required=False)
```

### Advanced Usage

```python
from secrets_manager import SecretsManager

# Initialize with custom settings
secrets = SecretsManager(
    region_name="us-west-2",
    use_aws=True,
    cache_ttl=600  # 10 minutes
)

# Get secret
password = secrets.get_secret("MYSQL_PASSWORD")

# Force refresh (bypass cache)
fresh_password = secrets.refresh_secret("MYSQL_PASSWORD")

# Clear cache
secrets.clear_cache()

# Get secret bundle
all_secrets = secrets.get_secret_bundle("afirgen/production/secrets")
```

## Docker Integration

### Development (Local)

No changes needed - uses environment variables from `.env` file:

```bash
docker-compose up
```

### Production (AWS ECS)

#### Option 1: Environment Variables from Secrets Manager

In ECS task definition:

```json
{
    "containerDefinitions": [
        {
            "name": "fir_pipeline",
            "secrets": [
                {
                    "name": "MYSQL_PASSWORD",
                    "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:MYSQL_PASSWORD-XXXXX"
                },
                {
                    "name": "API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:API_KEY-XXXXX"
                },
                {
                    "name": "FIR_AUTH_KEY",
                    "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:FIR_AUTH_KEY-XXXXX"
                }
            ],
            "environment": [
                {
                    "name": "ENVIRONMENT",
                    "value": "production"
                },
                {
                    "name": "AWS_REGION",
                    "value": "us-east-1"
                }
            ]
        }
    ]
}
```

#### Option 2: Direct AWS Secrets Manager Access

Application fetches secrets directly at runtime:

```json
{
    "containerDefinitions": [
        {
            "name": "fir_pipeline",
            "environment": [
                {
                    "name": "ENVIRONMENT",
                    "value": "production"
                },
                {
                    "name": "AWS_REGION",
                    "value": "us-east-1"
                },
                {
                    "name": "USE_AWS_SECRETS",
                    "value": "true"
                }
            ]
        }
    ],
    "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/AFIRGenTaskRole"
}
```

## Testing

### Unit Tests

Create `test_secrets_manager.py`:

```python
import os
import pytest
from secrets_manager import SecretsManager

def test_environment_variable_fallback():
    """Test that env vars work when AWS is disabled"""
    os.environ["TEST_SECRET"] = "test-value"
    
    secrets = SecretsManager(use_aws=False)
    value = secrets.get_secret("TEST_SECRET")
    
    assert value == "test-value"

def test_required_secret_missing():
    """Test that missing required secrets raise error"""
    secrets = SecretsManager(use_aws=False)
    
    with pytest.raises(ValueError):
        secrets.get_secret("NONEXISTENT_SECRET", required=True)

def test_optional_secret_missing():
    """Test that missing optional secrets return None"""
    secrets = SecretsManager(use_aws=False)
    value = secrets.get_secret("NONEXISTENT_SECRET", required=False)
    
    assert value is None

def test_default_value():
    """Test default value when secret not found"""
    secrets = SecretsManager(use_aws=False)
    value = secrets.get_secret("NONEXISTENT_SECRET", default="default-value")
    
    assert value == "default-value"

def test_cache():
    """Test that caching works"""
    os.environ["CACHED_SECRET"] = "cached-value"
    
    secrets = SecretsManager(use_aws=False, cache_ttl=60)
    
    # First call
    value1 = secrets.get_secret("CACHED_SECRET")
    
    # Change env var
    os.environ["CACHED_SECRET"] = "new-value"
    
    # Second call should return cached value
    value2 = secrets.get_secret("CACHED_SECRET")
    
    assert value1 == value2 == "cached-value"
    
    # Clear cache and try again
    secrets.clear_cache()
    value3 = secrets.get_secret("CACHED_SECRET")
    
    assert value3 == "new-value"
```

Run tests:

```bash
cd "AFIRGEN FINAL/main backend"
pytest test_secrets_manager.py -v
```

### Integration Tests

Test with actual AWS Secrets Manager:

```python
def test_aws_secrets_manager():
    """Test AWS Secrets Manager integration (requires AWS credentials)"""
    secrets = SecretsManager(use_aws=True, region_name="us-east-1")
    
    # This requires actual secrets in AWS
    try:
        value = secrets.get_secret("MYSQL_PASSWORD")
        assert value is not None
        print(f"Successfully retrieved secret from AWS")
    except Exception as e:
        pytest.skip(f"AWS Secrets Manager not available: {e}")
```

### Manual Testing

1. **Local Development**:
   ```bash
   # Set environment variables
   export MYSQL_PASSWORD=test-password
   export API_KEY=test-api-key
   export FIR_AUTH_KEY=test-auth-key
   export ENVIRONMENT=development
   
   # Run application
   cd "AFIRGEN FINAL/main backend"
   python agentv5.py
   ```

2. **AWS Production**:
   ```bash
   # Set AWS credentials
   export AWS_ACCESS_KEY_ID=your-access-key
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   export AWS_REGION=us-east-1
   export ENVIRONMENT=production
   
   # Run application (will fetch from AWS Secrets Manager)
   python agentv5.py
   ```

## Monitoring

### CloudWatch Logs

Monitor secrets access:

```python
import logging

logger = logging.getLogger("secrets_manager")
logger.setLevel(logging.INFO)

# Logs will show:
# - "Retrieved secret 'X' from AWS Secrets Manager"
# - "Retrieved secret 'X' from environment variable"
# - "Failed to get secret 'X' from AWS: <error>"
```

### CloudWatch Metrics

Create custom metrics for secret access:

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def log_secret_access(secret_name, source):
    cloudwatch.put_metric_data(
        Namespace='AFIRGen/Secrets',
        MetricData=[
            {
                'MetricName': 'SecretAccess',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'SecretName', 'Value': secret_name},
                    {'Name': 'Source', 'Value': source}  # 'AWS' or 'EnvVar'
                ]
            }
        ]
    )
```

## Troubleshooting

### Issue: "boto3 not available"

**Solution**: Install boto3:
```bash
pip install boto3
```

### Issue: "Access denied to secret"

**Solution**: Check IAM permissions. The ECS task role needs `secretsmanager:GetSecretValue` permission.

### Issue: "Secret not found in AWS Secrets Manager"

**Solution**: 
1. Verify secret exists: `aws secretsmanager list-secrets`
2. Check secret name matches exactly
3. Verify AWS region is correct
4. Ensure fallback env var is set for development

### Issue: "Application fails to start in production"

**Solution**:
1. Check CloudWatch logs for error messages
2. Verify `ENVIRONMENT=production` is set
3. Ensure AWS credentials are available (IAM role)
4. Test secret access manually:
   ```bash
   aws secretsmanager get-secret-value --secret-id MYSQL_PASSWORD
   ```

### Issue: "Secrets not updating after rotation"

**Solution**: 
1. Clear cache: `secrets.clear_cache()`
2. Reduce cache TTL in production
3. Implement secret rotation handler:
   ```python
   def rotate_secret(secret_name):
       secrets = get_secrets_manager()
       secrets.refresh_secret(secret_name)
       # Restart connections, etc.
   ```

## Best Practices

1. **Use Secret Bundles**: Store related secrets together for easier management
2. **Enable Rotation**: Configure automatic secret rotation in AWS
3. **Monitor Access**: Track secret access patterns in CloudWatch
4. **Least Privilege**: Grant minimal IAM permissions needed
5. **Cache Wisely**: Balance between API costs and secret freshness
6. **Test Locally**: Always test with environment variables before deploying
7. **Document Secrets**: Maintain a list of required secrets in documentation
8. **Version Secrets**: Use secret versioning for rollback capability

## Cost Optimization

- **Caching**: Default 5-minute cache reduces API calls by ~99%
- **Secret Bundles**: One API call instead of multiple
- **Pricing**: $0.40/secret/month + $0.05 per 10,000 API calls
- **Estimated Cost**: ~$2-5/month for typical usage

## Migration Guide

### From Environment Variables to AWS Secrets Manager

1. **Create secrets in AWS**:
   ```bash
   aws secretsmanager create-secret --name MYSQL_PASSWORD --secret-string "current-password"
   ```

2. **Update IAM role** with required permissions

3. **Deploy with both** env vars and AWS secrets (for rollback):
   ```bash
   # Keep env vars as fallback
   MYSQL_PASSWORD=fallback-password
   ENVIRONMENT=production
   ```

4. **Verify AWS secrets work** in staging

5. **Remove env vars** from production after validation

6. **Monitor** CloudWatch logs to confirm AWS secrets are being used

## Security Considerations

- **Never log secret values**: Only log secret names
- **Use IAM roles**: Don't use access keys in production
- **Enable encryption**: Secrets Manager encrypts at rest by default
- **Audit access**: Enable CloudTrail for secret access logs
- **Rotate regularly**: Implement automatic rotation
- **Separate environments**: Use different secrets for dev/staging/prod

## References

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [boto3 Secrets Manager API](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html)
- [ECS Secrets Management](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/specifying-sensitive-data.html)
