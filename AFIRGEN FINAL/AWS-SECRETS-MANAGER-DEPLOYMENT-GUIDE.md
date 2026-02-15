# AWS Secrets Manager Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying AFIRGen with AWS Secrets Manager integration.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI installed and configured
- Docker and Docker Compose installed (for local testing)
- Python 3.8+ with pip
- AFIRGen application code

## Deployment Steps

### Step 1: Install Dependencies

```bash
cd "AFIRGEN FINAL/main backend"
pip install -r requirements.txt
```

Verify boto3 is installed:
```bash
python -c "import boto3; print(boto3.__version__)"
```

### Step 2: Create Secrets in AWS Secrets Manager

#### Option A: Individual Secrets (Simple)

```bash
# Set your AWS region
export AWS_REGION=us-east-1

# Create MySQL password secret
aws secretsmanager create-secret \
    --name MYSQL_PASSWORD \
    --description "AFIRGen MySQL database password" \
    --secret-string "YOUR_SECURE_PASSWORD_HERE" \
    --region $AWS_REGION

# Create API key secret
aws secretsmanager create-secret \
    --name API_KEY \
    --description "AFIRGen API authentication key" \
    --secret-string "YOUR_SECURE_API_KEY_HERE" \
    --region $AWS_REGION

# Create FIR auth key secret
aws secretsmanager create-secret \
    --name FIR_AUTH_KEY \
    --description "AFIRGen FIR authentication key" \
    --secret-string "YOUR_SECURE_AUTH_KEY_HERE" \
    --region $AWS_REGION
```

#### Option B: Secret Bundle (Recommended)

```bash
# Create a single secret containing all credentials
aws secretsmanager create-secret \
    --name afirgen/production/secrets \
    --description "AFIRGen production secrets bundle" \
    --secret-string '{
        "MYSQL_PASSWORD": "YOUR_SECURE_PASSWORD_HERE",
        "MYSQL_USER": "afirgen_user",
        "MYSQL_DB": "fir_db",
        "API_KEY": "YOUR_SECURE_API_KEY_HERE",
        "FIR_AUTH_KEY": "YOUR_SECURE_AUTH_KEY_HERE"
    }' \
    --region $AWS_REGION
```

**Note**: Replace `YOUR_SECURE_*_HERE` with actual secure values. Use a password generator for production secrets.

### Step 3: Create IAM Policy

Create a file `afirgen-secrets-policy.json`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AFIRGenSecretsAccess",
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": [
                "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT_ID:secret:MYSQL_PASSWORD-*",
                "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT_ID:secret:API_KEY-*",
                "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT_ID:secret:FIR_AUTH_KEY-*"
            ]
        }
    ]
}
```

Or for secret bundle:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AFIRGenSecretsBundleAccess",
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT_ID:secret:afirgen/production/secrets-*"
        }
    ]
}
```

Get your AWS account ID:
```bash
aws sts get-caller-identity --query Account --output text
```

Create the policy:
```bash
aws iam create-policy \
    --policy-name AFIRGenSecretsPolicy \
    --policy-document file://afirgen-secrets-policy.json \
    --description "Policy for AFIRGen to access secrets"
```

### Step 4: Create IAM Role (for ECS)

Create a file `afirgen-task-role-trust-policy.json`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

Create the role:
```bash
aws iam create-role \
    --role-name AFIRGenTaskRole \
    --assume-role-policy-document file://afirgen-task-role-trust-policy.json \
    --description "Task role for AFIRGen ECS tasks"
```

Attach the secrets policy:
```bash
aws iam attach-role-policy \
    --role-name AFIRGenTaskRole \
    --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/AFIRGenSecretsPolicy
```

### Step 5: Test Locally

Before deploying to AWS, test the secrets manager locally:

```bash
# Set AWS credentials
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=us-east-1

# Enable production mode
export ENVIRONMENT=production

# Test secret retrieval
cd "AFIRGEN FINAL/main backend"
python -c "
from secrets_manager import get_secret
print('Testing secret retrieval...')
password = get_secret('MYSQL_PASSWORD')
print(f'Successfully retrieved MYSQL_PASSWORD: {password[:4]}...')
"
```

Run the test suite:
```bash
cd "AFIRGEN FINAL"
python test_secrets_manager.py
```

### Step 6: Update Application Configuration

If using secret bundles, update `agentv5.py`:

```python
from secrets_manager import get_secret_bundle

# Load all secrets at startup
try:
    secrets = get_secret_bundle("afirgen/production/secrets")
    log.info("Loaded secrets from AWS Secrets Manager")
except Exception as e:
    log.warning(f"Failed to load secret bundle, using individual secrets: {e}")
    secrets = None

CFG = {
    "mysql": {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": secrets.get("MYSQL_USER") if secrets else get_secret("MYSQL_USER", default="root"),
        "password": secrets.get("MYSQL_PASSWORD") if secrets else get_secret("MYSQL_PASSWORD"),
        "database": secrets.get("MYSQL_DB") if secrets else get_secret("MYSQL_DB", default="fir_db"),
        # ...
    },
    "auth_key": secrets.get("FIR_AUTH_KEY") if secrets else get_secret("FIR_AUTH_KEY"),
    "api_key": secrets.get("API_KEY") if secrets else get_secret("API_KEY"),
}
```

### Step 7: Deploy to AWS ECS

#### Create ECS Task Definition

Create `ecs-task-definition.json`:

```json
{
    "family": "afirgen-fir-pipeline",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "2048",
    "memory": "4096",
    "taskRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/AFIRGenTaskRole",
    "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/ecsTaskExecutionRole",
    "containerDefinitions": [
        {
            "name": "fir_pipeline",
            "image": "YOUR_ECR_REPO/afirgen-fir-pipeline:latest",
            "essential": true,
            "portMappings": [
                {
                    "containerPort": 8000,
                    "protocol": "tcp"
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
                },
                {
                    "name": "MYSQL_HOST",
                    "value": "your-rds-endpoint.rds.amazonaws.com"
                },
                {
                    "name": "MYSQL_PORT",
                    "value": "3306"
                }
            ],
            "secrets": [
                {
                    "name": "MYSQL_PASSWORD",
                    "valueFrom": "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT_ID:secret:MYSQL_PASSWORD-XXXXX"
                },
                {
                    "name": "API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT_ID:secret:API_KEY-XXXXX"
                },
                {
                    "name": "FIR_AUTH_KEY",
                    "valueFrom": "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT_ID:secret:FIR_AUTH_KEY-XXXXX"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/afirgen/fir-pipeline",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "ecs"
                }
            }
        }
    ]
}
```

Register the task definition:
```bash
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
```

#### Create ECS Service

```bash
aws ecs create-service \
    --cluster afirgen-cluster \
    --service-name afirgen-fir-pipeline \
    --task-definition afirgen-fir-pipeline \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=DISABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID:targetgroup/afirgen-tg/xxx,containerName=fir_pipeline,containerPort=8000"
```

### Step 8: Verify Deployment

#### Check ECS Task Status

```bash
aws ecs list-tasks --cluster afirgen-cluster --service-name afirgen-fir-pipeline
```

#### View CloudWatch Logs

```bash
aws logs tail /ecs/afirgen/fir-pipeline --follow
```

Look for log messages:
- "AWS Secrets Manager initialized for region: us-east-1"
- "Retrieved secret 'MYSQL_PASSWORD' from AWS Secrets Manager"
- "Loaded secrets from AWS Secrets Manager"

#### Test API Endpoint

```bash
# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --names afirgen-alb \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

# Test health endpoint
curl -H "X-API-Key: YOUR_API_KEY" https://$ALB_DNS/health
```

### Step 9: Enable Secret Rotation (Optional)

#### Create Rotation Lambda

```bash
aws secretsmanager rotate-secret \
    --secret-id MYSQL_PASSWORD \
    --rotation-lambda-arn arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:SecretsManagerRotation \
    --rotation-rules AutomaticallyAfterDays=30
```

#### Update Application for Rotation

Add rotation handler in `agentv5.py`:

```python
@app.post("/admin/rotate-secrets")
async def rotate_secrets():
    """Handle secret rotation notification"""
    from secrets_manager import get_secrets_manager
    
    secrets = get_secrets_manager()
    secrets.clear_cache()
    
    # Reconnect to database with new credentials
    await reconnect_database()
    
    return {"status": "secrets rotated"}
```

### Step 10: Set Up Monitoring

#### Create CloudWatch Alarms

```bash
# Alarm for secret access failures
aws cloudwatch put-metric-alarm \
    --alarm-name afirgen-secrets-access-failures \
    --alarm-description "Alert when secrets cannot be accessed" \
    --metric-name Errors \
    --namespace AWS/SecretsManager \
    --statistic Sum \
    --period 300 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1
```

#### Enable CloudTrail Logging

```bash
aws cloudtrail create-trail \
    --name afirgen-secrets-audit \
    --s3-bucket-name your-cloudtrail-bucket

aws cloudtrail start-logging --name afirgen-secrets-audit
```

## Rollback Procedure

If deployment fails:

1. **Revert to environment variables**:
   ```bash
   aws ecs update-service \
       --cluster afirgen-cluster \
       --service afirgen-fir-pipeline \
       --task-definition afirgen-fir-pipeline:PREVIOUS_VERSION
   ```

2. **Check logs for errors**:
   ```bash
   aws logs tail /ecs/afirgen/fir-pipeline --since 1h
   ```

3. **Verify IAM permissions**:
   ```bash
   aws iam simulate-principal-policy \
       --policy-source-arn arn:aws:iam::YOUR_ACCOUNT_ID:role/AFIRGenTaskRole \
       --action-names secretsmanager:GetSecretValue \
       --resource-arns arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT_ID:secret:MYSQL_PASSWORD-*
   ```

## Troubleshooting

### Issue: "Access Denied" errors

**Solution**:
1. Verify IAM role has correct permissions
2. Check secret ARN matches policy
3. Ensure task role is attached to ECS task

```bash
# Check role policies
aws iam list-attached-role-policies --role-name AFIRGenTaskRole

# Test secret access
aws secretsmanager get-secret-value --secret-id MYSQL_PASSWORD
```

### Issue: "Secret not found"

**Solution**:
1. Verify secret exists in correct region
2. Check secret name matches exactly
3. Ensure secret is not deleted

```bash
# List all secrets
aws secretsmanager list-secrets --region us-east-1

# Describe specific secret
aws secretsmanager describe-secret --secret-id MYSQL_PASSWORD
```

### Issue: Application using environment variables instead of AWS

**Solution**:
1. Verify `ENVIRONMENT=production` is set
2. Check CloudWatch logs for "Using environment variables" message
3. Ensure boto3 is installed in container

```bash
# Check container environment
aws ecs describe-tasks \
    --cluster afirgen-cluster \
    --tasks TASK_ARN \
    --query 'tasks[0].containers[0].environment'
```

### Issue: High AWS costs

**Solution**:
1. Increase cache TTL to reduce API calls
2. Use secret bundles instead of individual secrets
3. Monitor API call metrics

```bash
# Check API call metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/SecretsManager \
    --metric-name GetSecretValue \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-31T23:59:59Z \
    --period 86400 \
    --statistics Sum
```

## Security Best Practices

1. **Use least privilege IAM policies**: Only grant access to specific secrets
2. **Enable CloudTrail**: Audit all secret access
3. **Rotate secrets regularly**: Use automatic rotation
4. **Use VPC endpoints**: Reduce data transfer costs and improve security
5. **Encrypt secrets**: Use KMS for additional encryption (enabled by default)
6. **Monitor access**: Set up CloudWatch alarms for unusual access patterns
7. **Separate environments**: Use different secrets for dev/staging/prod
8. **Never log secrets**: Ensure secrets are not logged in application logs

## Cost Optimization

- **Use secret bundles**: $0.40/month instead of $1.20/month for 3 secrets
- **Enable caching**: Reduce API calls by 99%
- **Use VPC endpoints**: Eliminate data transfer charges
- **Monitor usage**: Set up billing alerts

**Estimated monthly cost**: $2-5 for typical usage

## Next Steps

1. Set up automated secret rotation
2. Configure CloudWatch dashboards for monitoring
3. Implement secret versioning strategy
4. Document secret management procedures
5. Train team on secret rotation process

## References

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [ECS Task IAM Roles](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html)
- [Secrets Manager Pricing](https://aws.amazon.com/secrets-manager/pricing/)
- [boto3 Secrets Manager API](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html)
