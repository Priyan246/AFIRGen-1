# API Authentication Deployment Guide

## Pre-Deployment Checklist

- [ ] API key generated (minimum 32 characters)
- [ ] Backend `.env` file configured with API_KEY
- [ ] Frontend `config.js` configured with API_KEY
- [ ] Keys match between frontend and backend
- [ ] `.env` file added to `.gitignore`
- [ ] No API keys committed to version control
- [ ] Test suite executed successfully
- [ ] Manual testing completed

## Development Deployment

### Step 1: Generate API Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Save the output - you'll need it for both backend and frontend.

### Step 2: Configure Backend

Create or update `AFIRGEN FINAL/.env`:

```bash
# Copy from example
cp .env.example .env

# Edit .env and add your API key
API_KEY=<your-generated-key>

# Other required variables
MYSQL_USER=root
MYSQL_PASSWORD=secure-password
MYSQL_DB=fir_db
FIR_AUTH_KEY=<another-secure-key>
```

### Step 3: Configure Frontend

Update `AFIRGEN FINAL/frontend/config.js`:

```javascript
window.ENV = {
    API_BASE_URL: 'http://localhost:8000',
    API_KEY: '<same-key-as-backend>',
    ENVIRONMENT: 'development',
    ENABLE_DEBUG: true,
};
```

### Step 4: Start Services

```bash
cd "AFIRGEN FINAL"
docker-compose up -d
```

### Step 5: Verify Deployment

```bash
# Wait for services to be healthy
docker-compose ps

# Test health endpoint (should work without auth)
curl http://localhost:8000/health

# Test protected endpoint without auth (should fail)
curl http://localhost:8000/metrics

# Test protected endpoint with auth (should succeed)
curl -H "X-API-Key: <your-key>" http://localhost:8000/metrics
```

### Step 6: Run Test Suite

```bash
# Set API key for tests
export API_KEY=<your-key>

# Run tests
python test_api_authentication.py
```

## Staging Deployment

### Step 1: Generate Production-Grade API Key

```bash
# Generate a strong key
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Step 2: Configure AWS Secrets Manager (Recommended)

```bash
# Create secret
aws secretsmanager create-secret \
  --name afirgen/staging/api-key \
  --description "AFIRGen Staging API Key" \
  --secret-string "{\"API_KEY\":\"<your-key>\"}" \
  --region us-east-1

# Verify secret
aws secretsmanager get-secret-value \
  --secret-id afirgen/staging/api-key \
  --region us-east-1
```

### Step 3: Update Backend Configuration

**Option A: Environment Variables**
```bash
export API_KEY=<your-key>
```

**Option B: AWS Secrets Manager Integration**

Update `main backend/agentv5.py` to load from Secrets Manager:

```python
import boto3
import json

def get_secret(secret_name, region_name="us-east-1"):
    client = boto3.client('secretsmanager', region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Load API key from Secrets Manager
if os.getenv("USE_SECRETS_MANAGER", "false").lower() == "true":
    secrets = get_secret("afirgen/staging/api-key")
    CFG["api_key"] = secrets["API_KEY"]
```

### Step 4: Update Frontend Configuration

**Build-time Configuration** (Recommended):

```bash
# In deployment script
export API_KEY=<your-key>

# Replace in config.js during build
sed -i "s|API_KEY: '.*'|API_KEY: '${API_KEY}'|g" frontend/config.js

# Build and deploy
docker build -t afirgen-frontend:staging ./frontend
```

**Runtime Configuration**:

```javascript
// Create config.staging.js
window.ENV = {
    API_BASE_URL: 'https://staging-api.afirgen.com',
    API_KEY: '<your-staging-key>',
    ENVIRONMENT: 'staging',
    ENABLE_DEBUG: false,
};
```

### Step 5: Deploy to Staging

```bash
# Build images
docker-compose -f docker-compose.staging.yaml build

# Deploy
docker-compose -f docker-compose.staging.yaml up -d

# Verify
curl -H "X-API-Key: <your-key>" https://staging-api.afirgen.com/health
```

### Step 6: Smoke Tests

```bash
# Set staging API key
export API_KEY=<your-staging-key>
export API_BASE_URL=https://staging-api.afirgen.com

# Run tests
python test_api_authentication.py
```

## Production Deployment

### Step 1: Generate Production API Key

```bash
# Generate a very strong key (64 characters)
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Step 2: Store in AWS Secrets Manager

```bash
# Create production secret
aws secretsmanager create-secret \
  --name afirgen/production/api-key \
  --description "AFIRGen Production API Key" \
  --secret-string "{\"API_KEY\":\"<your-production-key>\"}" \
  --region us-east-1 \
  --tags Key=Environment,Value=production Key=Application,Value=AFIRGen

# Enable automatic rotation (optional)
aws secretsmanager rotate-secret \
  --secret-id afirgen/production/api-key \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789012:function:afirgen-key-rotation \
  --rotation-rules AutomaticallyAfterDays=90
```

### Step 3: Configure IAM Roles

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
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:afirgen/production/api-key-*"
    }
  ]
}
```

### Step 4: Update ECS Task Definition

```json
{
  "family": "afirgen-backend",
  "taskRoleArn": "arn:aws:iam::123456789012:role/afirgen-task-role",
  "executionRoleArn": "arn:aws:iam::123456789012:role/afirgen-execution-role",
  "containerDefinitions": [
    {
      "name": "afirgen-backend",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/afirgen-backend:latest",
      "secrets": [
        {
          "name": "API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:afirgen/production/api-key-XXXXXX:API_KEY::"
        }
      ],
      "environment": [
        {
          "name": "USE_SECRETS_MANAGER",
          "value": "true"
        }
      ]
    }
  ]
}
```

### Step 5: Configure Frontend

**CloudFront Distribution**:

```bash
# Store API key in Parameter Store for frontend
aws ssm put-parameter \
  --name /afirgen/production/frontend-api-key \
  --value "<your-production-key>" \
  --type SecureString \
  --region us-east-1

# Lambda@Edge function to inject API key
# (See Lambda@Edge example below)
```

**Lambda@Edge Example**:

```javascript
// viewer-request.js
exports.handler = async (event) => {
    const request = event.Records[0].cf.request;
    
    // Add API key to requests going to backend
    if (request.uri.startsWith('/api/')) {
        request.headers['x-api-key'] = [{
            key: 'X-API-Key',
            value: process.env.API_KEY
        }];
    }
    
    return request;
};
```

**Alternative: Build-time Injection**:

```bash
# In CI/CD pipeline
export API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id afirgen/production/api-key \
  --query SecretString --output text | jq -r .API_KEY)

# Inject into config.js
sed -i "s|API_KEY: '.*'|API_KEY: '${API_KEY}'|g" frontend/config.js

# Build
docker build -t afirgen-frontend:production ./frontend
```

### Step 6: Deploy to Production

```bash
# Update ECS service
aws ecs update-service \
  --cluster afirgen-production \
  --service afirgen-backend \
  --task-definition afirgen-backend:latest \
  --force-new-deployment

# Wait for deployment
aws ecs wait services-stable \
  --cluster afirgen-production \
  --services afirgen-backend

# Verify
curl -H "X-API-Key: <your-key>" https://api.afirgen.com/health
```

### Step 7: Production Smoke Tests

```bash
# Set production API key (from Secrets Manager)
export API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id afirgen/production/api-key \
  --query SecretString --output text | jq -r .API_KEY)

export API_BASE_URL=https://api.afirgen.com

# Run critical tests only
python test_api_authentication.py
```

### Step 8: Enable Monitoring

```bash
# Create CloudWatch alarm for authentication failures
aws cloudwatch put-metric-alarm \
  --alarm-name afirgen-auth-failures \
  --alarm-description "Alert on high authentication failure rate" \
  --metric-name AuthenticationFailures \
  --namespace AFIRGen/Security \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:afirgen-alerts
```

## Rollback Procedure

### If Authentication Issues Occur

**Step 1: Identify the Issue**
```bash
# Check logs
aws logs tail /aws/ecs/afirgen-backend --follow

# Check metrics
aws cloudwatch get-metric-statistics \
  --namespace AFIRGen/Security \
  --metric-name AuthenticationFailures \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

**Step 2: Quick Fix - Disable Authentication Temporarily**

⚠️ **WARNING**: Only use in emergency situations!

```python
# In agentv5.py, comment out middleware temporarily
# app.add_middleware(APIAuthMiddleware)
```

**Step 3: Rollback to Previous Version**

```bash
# Rollback ECS service
aws ecs update-service \
  --cluster afirgen-production \
  --service afirgen-backend \
  --task-definition afirgen-backend:<previous-version>

# Wait for rollback
aws ecs wait services-stable \
  --cluster afirgen-production \
  --services afirgen-backend
```

**Step 4: Verify Rollback**

```bash
# Test without authentication (should work if rolled back)
curl https://api.afirgen.com/metrics
```

## Key Rotation Procedure

### Scheduled Rotation (Every 90 Days)

**Step 1: Generate New Key**
```bash
NEW_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
echo "New key: $NEW_KEY"
```

**Step 2: Update Secrets Manager**
```bash
# Update secret with new key
aws secretsmanager update-secret \
  --secret-id afirgen/production/api-key \
  --secret-string "{\"API_KEY\":\"$NEW_KEY\",\"OLD_API_KEY\":\"$OLD_KEY\"}"
```

**Step 3: Update Backend to Accept Both Keys**

Temporarily modify backend to accept both old and new keys:

```python
# In APIAuthMiddleware
valid_keys = [CFG["api_key"], CFG.get("old_api_key")]
if not any(hmac.compare_digest(api_key, k) for k in valid_keys if k):
    raise HTTPException(status_code=401, detail="Invalid API key")
```

**Step 4: Deploy Backend**
```bash
# Deploy with dual-key support
aws ecs update-service --cluster afirgen-production --service afirgen-backend --force-new-deployment
```

**Step 5: Update Frontend**
```bash
# Update frontend with new key
# Deploy frontend
```

**Step 6: Verify New Key Works**
```bash
curl -H "X-API-Key: $NEW_KEY" https://api.afirgen.com/health
```

**Step 7: Remove Old Key**
```bash
# Update secret to only have new key
aws secretsmanager update-secret \
  --secret-id afirgen/production/api-key \
  --secret-string "{\"API_KEY\":\"$NEW_KEY\"}"

# Deploy backend again to remove old key support
```

## Monitoring and Alerts

### CloudWatch Metrics

```bash
# Create custom metric filter
aws logs put-metric-filter \
  --log-group-name /aws/ecs/afirgen-backend \
  --filter-name AuthenticationFailures \
  --filter-pattern "[time, level=WARNING, msg=\"Invalid API key attempt*\"]" \
  --metric-transformations \
    metricName=AuthenticationFailures,\
    metricNamespace=AFIRGen/Security,\
    metricValue=1
```

### SNS Alerts

```bash
# Create SNS topic
aws sns create-topic --name afirgen-security-alerts

# Subscribe email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:afirgen-security-alerts \
  --protocol email \
  --notification-endpoint security@afirgen.com
```

### Dashboard

```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name AFIRGen-Security \
  --dashboard-body file://dashboard.json
```

## Troubleshooting

### Issue: High Authentication Failure Rate

**Diagnosis**:
```bash
# Check logs for patterns
aws logs filter-pattern /aws/ecs/afirgen-backend \
  --filter-pattern "Invalid API key attempt" \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

**Solutions**:
1. Check if API key was rotated but frontend not updated
2. Verify Secrets Manager has correct key
3. Check if rate limiting is triggering false positives
4. Look for potential DDoS attack

### Issue: Frontend Can't Authenticate

**Diagnosis**:
```bash
# Check frontend logs
aws logs tail /aws/ecs/afirgen-frontend --follow

# Test API key manually
curl -H "X-API-Key: $API_KEY" https://api.afirgen.com/health
```

**Solutions**:
1. Verify API_KEY in frontend config.js
2. Check CORS configuration allows X-API-Key header
3. Verify API key matches backend
4. Check if CloudFront is stripping headers

### Issue: Secrets Manager Access Denied

**Diagnosis**:
```bash
# Check IAM role permissions
aws iam get-role-policy \
  --role-name afirgen-task-role \
  --policy-name SecretsManagerAccess
```

**Solutions**:
1. Verify IAM role has secretsmanager:GetSecretValue permission
2. Check resource ARN in policy matches secret ARN
3. Verify task role is attached to ECS task definition

## Best Practices

1. **Never commit API keys to version control**
2. **Use AWS Secrets Manager in production**
3. **Rotate keys every 90 days**
4. **Monitor authentication failures**
5. **Use HTTPS only in production**
6. **Test key rotation in staging first**
7. **Have rollback plan ready**
8. **Document all key changes**
9. **Use strong, random keys (64+ characters)**
10. **Limit key access to necessary services only**

## Support

For deployment issues:
- Check logs: `aws logs tail /aws/ecs/afirgen-backend --follow`
- Review metrics: CloudWatch dashboard
- Run tests: `python test_api_authentication.py`
- Consult documentation: `API-AUTHENTICATION-IMPLEMENTATION.md`

