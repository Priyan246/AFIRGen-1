# API Authentication Implementation

## Overview
This document describes the API authentication implementation for AFIRGen, which requires API keys for all endpoints except public health checks.

## Implementation Details

### Backend Changes

#### 1. API Authentication Middleware
**File**: `main backend/agentv5.py`

Added `APIAuthMiddleware` class that:
- Validates API keys on all endpoints except public ones (`/health`, `/docs`, `/redoc`, `/openapi.json`)
- Accepts API keys via two methods:
  - `X-API-Key` header
  - `Authorization: Bearer <key>` header
- Uses constant-time comparison (`hmac.compare_digest`) to prevent timing attacks
- Logs authentication failures with client IP and endpoint
- Returns HTTP 401 for missing or invalid API keys

**Public Endpoints** (no authentication required):
- `/health` - Health check endpoint
- `/docs` - API documentation (Swagger UI)
- `/redoc` - API documentation (ReDoc)
- `/openapi.json` - OpenAPI schema

**Protected Endpoints** (authentication required):
- `/process` - Start FIR processing
- `/validate` - Validate processing steps
- `/regenerate/{session_id}` - Regenerate content
- `/session/{session_id}/status` - Get session status
- `/authenticate` - Finalize FIR
- `/fir/{fir_number}` - Get FIR status
- `/fir/{fir_number}/content` - Get FIR content
- `/metrics` - Performance metrics
- `/reliability/status` - Reliability status
- `/reliability/circuit-breaker/{name}/reset` - Reset circuit breaker
- `/reliability/recovery/{name}/trigger` - Trigger manual recovery
- `/view_fir_records` - View all FIR records
- `/view_fir/{fir_number}` - View specific FIR
- `/list-firs` - List all FIRs

#### 2. Configuration
**File**: `main backend/agentv5.py`

Added `api_key` to CFG dictionary:
```python
"api_key": os.getenv("API_KEY"),  # API key for endpoint authentication
```

#### 3. Environment Variables
**File**: `.env.example`

Added `API_KEY` configuration:
```bash
API_KEY=your-secure-api-key-here-min-32-chars
```

### Frontend Changes

#### 1. Configuration
**File**: `frontend/config.js`

Added `API_KEY` to window.ENV:
```javascript
window.ENV = {
    API_BASE_URL: 'http://localhost:8000',
    API_KEY: 'your-api-key-here',
    ENVIRONMENT: 'development',
    ENABLE_DEBUG: true,
};
```

#### 2. API Client Updates
**File**: `frontend/script.js`

Added helper function to include API key in all requests:
```javascript
function getAuthHeaders(additionalHeaders = {}) {
    const headers = {
        'X-API-Key': API_KEY,
        ...additionalHeaders
    };
    return headers;
}
```

Updated all fetch calls to include authentication headers:
- `/process` endpoint
- `/validate` endpoint
- `/regenerate/{session_id}` endpoint
- `/session/{session_id}/status` endpoint
- `/fir/{fir_number}` endpoint

#### 3. Environment Configuration
**File**: `frontend/.env.example`

Added `API_KEY` configuration:
```bash
API_KEY=your-api-key-here
```

## Security Features

### 1. Constant-Time Comparison
Uses `hmac.compare_digest()` to prevent timing attacks when validating API keys.

### 2. Multiple Authentication Methods
Supports both:
- `X-API-Key: <key>` header (recommended)
- `Authorization: Bearer <key>` header (standard OAuth2 format)

### 3. Comprehensive Logging
Logs all authentication failures with:
- Client IP address
- Requested endpoint
- Timestamp

### 4. Configuration Validation
Validates that API_KEY is configured before accepting requests, preventing misconfiguration.

## Configuration Guide

### Development Setup

1. **Generate a secure API key**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. **Backend configuration** (`.env` file):
```bash
API_KEY=<generated-key>
```

3. **Frontend configuration** (`frontend/config.js`):
```javascript
window.ENV = {
    API_BASE_URL: 'http://localhost:8000',
    API_KEY: '<same-generated-key>',
    ENVIRONMENT: 'development',
    ENABLE_DEBUG: true,
};
```

### Production Deployment

#### Option 1: Environment Variables (Recommended)

**Backend**:
```bash
# In .env or AWS Secrets Manager
API_KEY=<production-key>
```

**Frontend** (Docker):
```dockerfile
# In Dockerfile or docker-compose.yaml
ENV API_KEY=<production-key>
```

**Frontend** (Build-time):
```bash
# In deployment script
sed -i "s|API_KEY: '.*'|API_KEY: '${API_KEY}'|g" config.js
```

#### Option 2: AWS Secrets Manager

**Backend**:
```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

secrets = get_secret('afirgen/api-keys')
CFG["api_key"] = secrets["API_KEY"]
```

**Frontend** (via API Gateway or Lambda):
- Store API key in AWS Secrets Manager
- Inject at runtime via environment variable
- Use CloudFront to add header automatically

#### Option 3: Multiple API Keys (Future Enhancement)

For multi-tenant or team-based access:
```python
# Store multiple keys in database or Secrets Manager
VALID_API_KEYS = {
    "team-a-key": {"name": "Team A", "permissions": ["read", "write"]},
    "team-b-key": {"name": "Team B", "permissions": ["read"]},
}

# Validate and check permissions
if api_key in VALID_API_KEYS:
    request.state.api_key_info = VALID_API_KEYS[api_key]
```

## Testing

### Manual Testing

#### 1. Test without API key (should fail):
```bash
curl -X POST http://localhost:8000/process \
  -F "text=Test complaint"

# Expected: HTTP 401 - API key required
```

#### 2. Test with invalid API key (should fail):
```bash
curl -X POST http://localhost:8000/process \
  -H "X-API-Key: invalid-key" \
  -F "text=Test complaint"

# Expected: HTTP 401 - Invalid API key
```

#### 3. Test with valid API key (should succeed):
```bash
curl -X POST http://localhost:8000/process \
  -H "X-API-Key: your-valid-key" \
  -F "text=Test complaint"

# Expected: HTTP 200 - Success
```

#### 4. Test Bearer token format:
```bash
curl -X POST http://localhost:8000/process \
  -H "Authorization: Bearer your-valid-key" \
  -F "text=Test complaint"

# Expected: HTTP 200 - Success
```

#### 5. Test public endpoint (should work without key):
```bash
curl http://localhost:8000/health

# Expected: HTTP 200 - Health status
```

### Automated Testing

Create `test_api_authentication.py`:
```python
import requests
import os

API_BASE = "http://localhost:8000"
API_KEY = os.getenv("API_KEY", "test-key")

def test_no_api_key():
    """Test that requests without API key are rejected"""
    response = requests.post(f"{API_BASE}/process", data={"text": "test"})
    assert response.status_code == 401
    assert "API key required" in response.json()["detail"]

def test_invalid_api_key():
    """Test that requests with invalid API key are rejected"""
    response = requests.post(
        f"{API_BASE}/process",
        headers={"X-API-Key": "invalid-key"},
        data={"text": "test"}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]

def test_valid_api_key():
    """Test that requests with valid API key are accepted"""
    response = requests.post(
        f"{API_BASE}/process",
        headers={"X-API-Key": API_KEY},
        data={"text": "This is a test complaint about theft"}
    )
    assert response.status_code == 200

def test_bearer_token():
    """Test that Bearer token format works"""
    response = requests.post(
        f"{API_BASE}/process",
        headers={"Authorization": f"Bearer {API_KEY}"},
        data={"text": "This is a test complaint about theft"}
    )
    assert response.status_code == 200

def test_public_endpoint():
    """Test that health endpoint works without API key"""
    response = requests.get(f"{API_BASE}/health")
    assert response.status_code == 200

if __name__ == "__main__":
    print("Testing API authentication...")
    test_no_api_key()
    print("✅ No API key test passed")
    test_invalid_api_key()
    print("✅ Invalid API key test passed")
    test_valid_api_key()
    print("✅ Valid API key test passed")
    test_bearer_token()
    print("✅ Bearer token test passed")
    test_public_endpoint()
    print("✅ Public endpoint test passed")
    print("\n✅ All authentication tests passed!")
```

Run tests:
```bash
python test_api_authentication.py
```

## Monitoring and Logging

### Authentication Failure Monitoring

Monitor logs for authentication failures:
```bash
# View authentication failures
grep "Invalid API key attempt" fir_pipeline.log

# Count failures by IP
grep "Invalid API key attempt" fir_pipeline.log | awk '{print $NF}' | sort | uniq -c | sort -rn
```

### CloudWatch Metrics (AWS)

Create custom metrics for:
- Authentication failure rate
- Requests by API key (if using multiple keys)
- Failed authentication attempts by IP

Example CloudWatch filter:
```json
{
  "filterPattern": "[time, level=WARNING, msg=\"Invalid API key attempt*\"]",
  "metricTransformations": [{
    "metricName": "AuthenticationFailures",
    "metricNamespace": "AFIRGen/Security",
    "metricValue": "1"
  }]
}
```

### Alerts

Set up alerts for:
- High authentication failure rate (>10 failures/minute)
- Repeated failures from same IP (potential attack)
- Missing API_KEY configuration

## Security Best Practices

### 1. Key Generation
- Use cryptographically secure random keys (minimum 32 characters)
- Generate using: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Never use predictable keys like "password" or "admin"

### 2. Key Storage
- **Never commit keys to version control**
- Use `.env` files (add to `.gitignore`)
- Use AWS Secrets Manager or similar for production
- Rotate keys regularly (every 90 days recommended)

### 3. Key Transmission
- Always use HTTPS in production
- Never log API keys
- Never include keys in URLs (use headers only)

### 4. Key Rotation
When rotating keys:
1. Generate new key
2. Update backend configuration
3. Update frontend configuration
4. Deploy backend first (supports both old and new keys temporarily)
5. Deploy frontend
6. Remove old key from backend after verification

### 5. Rate Limiting
API authentication works with existing rate limiting:
- Rate limits apply per IP address
- Failed authentication attempts count toward rate limit
- Prevents brute-force attacks

## Troubleshooting

### Issue: "API authentication not properly configured"
**Cause**: API_KEY environment variable not set
**Solution**: Set API_KEY in `.env` file or environment variables

### Issue: "API key required"
**Cause**: Request missing X-API-Key or Authorization header
**Solution**: Add header to request:
```javascript
headers: { 'X-API-Key': 'your-key' }
```

### Issue: "Invalid API key"
**Cause**: API key doesn't match backend configuration
**Solution**: Verify API_KEY matches in both frontend and backend

### Issue: Frontend shows 401 errors
**Cause**: API_KEY not configured in frontend config.js
**Solution**: Update `window.ENV.API_KEY` in config.js

### Issue: CORS errors with authentication
**Cause**: Authorization header not allowed in CORS
**Solution**: Already configured - `allow_headers` includes "Authorization"

## Migration Guide

### Migrating Existing Deployments

1. **Update backend code** (this implementation)
2. **Set API_KEY environment variable**:
   ```bash
   export API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
   ```
3. **Update frontend config.js** with same API_KEY
4. **Test locally** before deploying
5. **Deploy backend first** (will reject unauthenticated requests)
6. **Deploy frontend** (will include API key in requests)

### Backward Compatibility

This implementation is **not backward compatible** - all clients must include API keys.

To maintain backward compatibility temporarily:
1. Make authentication optional initially
2. Log warnings for unauthenticated requests
3. Set deadline for mandatory authentication
4. Enable enforcement after deadline

## Future Enhancements

### 1. JWT Tokens
Replace simple API keys with JWT tokens for:
- Expiration support
- User identity
- Fine-grained permissions

### 2. OAuth2
Implement OAuth2 for:
- Third-party integrations
- User authentication
- Refresh tokens

### 3. API Key Management
Add endpoints for:
- Creating new API keys
- Revoking keys
- Listing active keys
- Setting key permissions

### 4. Per-Key Rate Limiting
Different rate limits for different API keys:
```python
RATE_LIMITS = {
    "premium-key": 1000,  # 1000 requests/minute
    "standard-key": 100,  # 100 requests/minute
}
```

### 5. Audit Logging
Log all API requests with:
- API key used
- Endpoint accessed
- Request parameters
- Response status
- Timestamp

## Compliance

### GDPR
- API keys are not personal data
- Log retention policies apply to authentication logs
- Users can request deletion of their API keys

### SOC 2
- API keys provide access control
- Authentication failures are logged
- Keys can be rotated and revoked

### PCI DSS
- API keys protect sensitive FIR data
- Keys must be stored securely
- Regular key rotation required

## References

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [NIST Digital Identity Guidelines](https://pages.nist.gov/800-63-3/)

## Changelog

- **2025-02-12**: Initial API authentication implementation
  - Added APIAuthMiddleware
  - Updated frontend to include API keys
  - Added configuration and documentation
  - Created test suite

