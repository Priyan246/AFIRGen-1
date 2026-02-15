# AWS Secrets Manager - Quick Reference

## Quick Start

### Local Development
```bash
# Use .env file - no changes needed
MYSQL_PASSWORD=password
API_KEY=your-api-key
FIR_AUTH_KEY=your-auth-key
```

### Production (AWS)
```bash
# Create secrets
aws secretsmanager create-secret --name MYSQL_PASSWORD --secret-string "secure-password"
aws secretsmanager create-secret --name API_KEY --secret-string "secure-api-key"
aws secretsmanager create-secret --name FIR_AUTH_KEY --secret-string "secure-auth-key"

# Set environment
ENVIRONMENT=production
AWS_REGION=us-east-1
```

## Common Commands

### Create Secret
```bash
aws secretsmanager create-secret \
    --name SECRET_NAME \
    --secret-string "secret-value" \
    --region us-east-1
```

### Create Secret Bundle
```bash
aws secretsmanager create-secret \
    --name afirgen/production/secrets \
    --secret-string '{
        "MYSQL_PASSWORD": "password",
        "API_KEY": "api-key",
        "FIR_AUTH_KEY": "auth-key"
    }' \
    --region us-east-1
```

### Get Secret
```bash
aws secretsmanager get-secret-value --secret-id SECRET_NAME
```

### Update Secret
```bash
aws secretsmanager update-secret \
    --secret-id SECRET_NAME \
    --secret-string "new-value"
```

### List Secrets
```bash
aws secretsmanager list-secrets
```

### Delete Secret
```bash
aws secretsmanager delete-secret \
    --secret-id SECRET_NAME \
    --recovery-window-in-days 7
```

## Code Usage

### Basic
```python
from secrets_manager import get_secret

password = get_secret("MYSQL_PASSWORD")
api_key = get_secret("API_KEY", default="fallback-key")
optional = get_secret("OPTIONAL_KEY", required=False)
```

### Secret Bundle
```python
from secrets_manager import get_secret_bundle

secrets = get_secret_bundle("afirgen/production/secrets")
password = secrets["MYSQL_PASSWORD"]
api_key = secrets["API_KEY"]
```

### Advanced
```python
from secrets_manager import SecretsManager

secrets = SecretsManager(region_name="us-west-2", cache_ttl=600)
password = secrets.get_secret("MYSQL_PASSWORD")
secrets.refresh_secret("MYSQL_PASSWORD")  # Force refresh
secrets.clear_cache()  # Clear all cached secrets
```

## IAM Policy

### Minimal Permissions
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:SECRET_NAME-*"
        }
    ]
}
```

### Multiple Secrets
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": [
                "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:MYSQL_PASSWORD-*",
                "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:API_KEY-*",
                "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:FIR_AUTH_KEY-*"
            ]
        }
    ]
}
```

## ECS Task Definition

### Using Secrets Manager
```json
{
    "containerDefinitions": [
        {
            "name": "fir_pipeline",
            "secrets": [
                {
                    "name": "MYSQL_PASSWORD",
                    "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:MYSQL_PASSWORD-XXXXX"
                }
            ],
            "environment": [
                {
                    "name": "ENVIRONMENT",
                    "value": "production"
                }
            ]
        }
    ],
    "taskRoleArn": "arn:aws:iam::ACCOUNT:role/AFIRGenTaskRole"
}
```

## Environment Variables

### Required
```bash
ENVIRONMENT=production          # Enables AWS Secrets Manager
AWS_REGION=us-east-1           # AWS region
```

### Optional
```bash
USE_AWS_SECRETS=true           # Force enable AWS Secrets Manager
AWS_SECRET_BUNDLE_NAME=name    # Secret bundle name
```

## Troubleshooting

### Check Secret Exists
```bash
aws secretsmanager describe-secret --secret-id SECRET_NAME
```

### Test Secret Access
```bash
aws secretsmanager get-secret-value --secret-id SECRET_NAME --query SecretString --output text
```

### Check IAM Permissions
```bash
aws iam get-role-policy --role-name AFIRGenTaskRole --policy-name SecretsAccess
```

### View CloudWatch Logs
```bash
aws logs tail /ecs/afirgen/fir_pipeline --follow
```

## Common Issues

| Issue | Solution |
|-------|----------|
| "boto3 not available" | `pip install boto3` |
| "Access denied" | Check IAM permissions |
| "Secret not found" | Verify secret name and region |
| "Using env vars in prod" | Set `ENVIRONMENT=production` |
| "Secrets not updating" | Call `secrets.refresh_secret()` or reduce cache TTL |

## Cost Estimate

- **Storage**: $0.40/secret/month
- **API Calls**: $0.05 per 10,000 calls
- **Typical Usage**: $2-5/month (with caching)

## Best Practices

✅ Use secret bundles for related secrets  
✅ Enable automatic rotation  
✅ Use IAM roles (not access keys)  
✅ Cache secrets (default: 5 minutes)  
✅ Monitor access in CloudWatch  
✅ Test locally with env vars first  
✅ Use least privilege IAM policies  
✅ Enable CloudTrail for audit logs  

❌ Don't log secret values  
❌ Don't hardcode secrets  
❌ Don't use same secrets across environments  
❌ Don't disable caching in production  
❌ Don't grant broad IAM permissions  

## Testing

### Local Test
```bash
export MYSQL_PASSWORD=test-password
export ENVIRONMENT=development
python agentv5.py
```

### AWS Test
```bash
export AWS_REGION=us-east-1
export ENVIRONMENT=production
python agentv5.py
```

### Unit Test
```bash
pytest test_secrets_manager.py -v
```

## Migration Checklist

- [ ] Create secrets in AWS Secrets Manager
- [ ] Update IAM role with permissions
- [ ] Test in staging environment
- [ ] Deploy to production with fallback env vars
- [ ] Verify AWS secrets are being used (check logs)
- [ ] Remove fallback env vars
- [ ] Enable secret rotation
- [ ] Set up CloudWatch monitoring

## Support

- Documentation: `AWS-SECRETS-MANAGER-IMPLEMENTATION.md`
- AWS Docs: https://docs.aws.amazon.com/secretsmanager/
- boto3 API: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html
