# API Authentication - README

## What is API Authentication?

API authentication ensures that only authorized clients can access the AFIRGen API endpoints. This prevents unauthorized access, protects sensitive FIR data, and provides an audit trail of API usage.

## Quick Start

### 1. Generate an API Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

This generates a cryptographically secure random key like:
```
xK9mP2vL8nQ4rT6wY1zA3bC5dE7fG0hJ9kM2nP4qR6sT8uV1wX3yZ5aB7cD9eF0g
```

### 2. Configure Backend

Create or update `.env` file:
```bash
API_KEY=xK9mP2vL8nQ4rT6wY1zA3bC5dE7fG0hJ9kM2nP4qR6sT8uV1wX3yZ5aB7cD9eF0g
```

### 3. Configure Frontend

Update `frontend/config.js`:
```javascript
window.ENV = {
    API_BASE_URL: 'http://localhost:8000',
    API_KEY: 'xK9mP2vL8nQ4rT6wY1zA3bC5dE7fG0hJ9kM2nP4qR6sT8uV1wX3yZ5aB7cD9eF0g',
    ENVIRONMENT: 'development',
    ENABLE_DEBUG: true,
};
```

### 4. Start Services

```bash
docker-compose up -d
```

### 5. Test

```bash
# Should fail (no API key)
curl http://localhost:8000/process -F "text=test"

# Should succeed (with API key)
curl http://localhost:8000/process \
  -H "X-API-Key: xK9mP2vL8nQ4rT6wY1zA3bC5dE7fG0hJ9kM2nP4qR6sT8uV1wX3yZ5aB7cD9eF0g" \
  -F "text=This is a test complaint"
```

## How It Works

### Public Endpoints (No Authentication)
These endpoints are accessible without an API key:
- `/health` - Health check
- `/docs` - API documentation
- `/redoc` - Alternative API docs
- `/openapi.json` - OpenAPI schema

### Protected Endpoints (Authentication Required)
All other endpoints require a valid API key:
- `/process` - Start FIR processing
- `/validate` - Validate steps
- `/fir/{number}` - Get FIR data
- And all other endpoints...

### Authentication Methods

**Method 1: X-API-Key Header (Recommended)**
```bash
curl -H "X-API-Key: your-key" http://localhost:8000/process
```

**Method 2: Authorization Bearer Token**
```bash
curl -H "Authorization: Bearer your-key" http://localhost:8000/process
```

## Using the API

### cURL Examples

```bash
# Start FIR processing
curl -X POST http://localhost:8000/process \
  -H "X-API-Key: your-key" \
  -F "text=Complaint text here"

# Get FIR status
curl -H "X-API-Key: your-key" \
  http://localhost:8000/fir/FIR-12345678-20250101000000

# Get metrics
curl -H "X-API-Key: your-key" \
  http://localhost:8000/metrics
```

### JavaScript/Frontend

The frontend automatically includes the API key in all requests:

```javascript
// Configured in config.js
const API_KEY = window.ENV.API_KEY;

// Helper function adds API key to headers
function getAuthHeaders(additionalHeaders = {}) {
    return {
        'X-API-Key': API_KEY,
        ...additionalHeaders
    };
}

// All fetch calls use the helper
fetch(`${API_BASE}/process`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData
});
```

### Python

```python
import requests

API_KEY = "your-api-key"
API_BASE = "http://localhost:8000"

# Using X-API-Key header
headers = {"X-API-Key": API_KEY}
response = requests.post(
    f"{API_BASE}/process",
    headers=headers,
    data={"text": "Test complaint"}
)

# Using Authorization Bearer
headers = {"Authorization": f"Bearer {API_KEY}"}
response = requests.post(
    f"{API_BASE}/process",
    headers=headers,
    data={"text": "Test complaint"}
)
```

## Error Responses

### 401 - Missing API Key
```json
{
    "detail": "API key required. Include X-API-Key header or Authorization: Bearer <key>"
}
```

**Solution**: Add the API key header to your request.

### 401 - Invalid API Key
```json
{
    "detail": "Invalid API key"
}
```

**Solution**: Verify the API key matches the backend configuration.

### 500 - Not Configured
```json
{
    "detail": "API authentication not properly configured"
}
```

**Solution**: Set the `API_KEY` environment variable in the backend.

## Security Features

### 1. Timing Attack Prevention
Uses constant-time comparison to prevent attackers from determining valid keys through timing analysis.

### 2. Comprehensive Logging
All authentication failures are logged with:
- Client IP address
- Requested endpoint
- Timestamp

### 3. No Information Leakage
Error messages are informative but don't reveal:
- Valid API keys
- Key format or length
- Internal system details

### 4. Rate Limiting Integration
Works with existing rate limiting to prevent brute-force attacks.

## Production Deployment

### AWS Secrets Manager

```bash
# Store API key
aws secretsmanager create-secret \
  --name afirgen/api-key \
  --secret-string '{"API_KEY":"your-production-key"}'

# Retrieve in application
aws secretsmanager get-secret-value \
  --secret-id afirgen/api-key
```

### Docker

```yaml
# docker-compose.yaml
services:
  backend:
    environment:
      - API_KEY=${API_KEY}
```

```bash
# Set environment variable
export API_KEY="your-production-key"
docker-compose up -d
```

### Kubernetes

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: afirgen-api-key
type: Opaque
stringData:
  api-key: your-production-key

# deployment.yaml
env:
  - name: API_KEY
    valueFrom:
      secretKeyRef:
        name: afirgen-api-key
        key: api-key
```

## Testing

### Automated Tests

Run the test suite:
```bash
python test_api_authentication.py
```

### Manual Testing

```bash
# Test without key (should fail with 401)
curl http://localhost:8000/process -F "text=test"

# Test with invalid key (should fail with 401)
curl -H "X-API-Key: wrong-key" \
  http://localhost:8000/process -F "text=test"

# Test with valid key (should succeed)
curl -H "X-API-Key: your-key" \
  http://localhost:8000/process \
  -F "text=This is a test complaint about theft"

# Test public endpoint (should work without key)
curl http://localhost:8000/health
```

## Monitoring

### View Authentication Failures

```bash
# View all authentication failures
grep "Invalid API key attempt" fir_pipeline.log

# Count failures by IP address
grep "Invalid API key attempt" fir_pipeline.log | \
  awk '{print $NF}' | sort | uniq -c | sort -rn

# View recent failures (last 100 lines)
tail -100 fir_pipeline.log | grep "Invalid API key"
```

### Set Up Alerts

Monitor for:
- High authentication failure rate (>10 failures/minute)
- Repeated failures from same IP (potential attack)
- Missing API_KEY configuration errors

## Troubleshooting

### Problem: "API key required" error

**Cause**: Request is missing the API key header.

**Solution**: Add the header to your request:
```bash
curl -H "X-API-Key: your-key" http://localhost:8000/process
```

### Problem: "Invalid API key" error

**Cause**: The API key doesn't match the backend configuration.

**Solution**: 
1. Check the API key in your request
2. Verify the API_KEY in backend `.env` file
3. Ensure they match exactly (case-sensitive)

### Problem: Frontend shows 401 errors

**Cause**: API key not configured in frontend.

**Solution**: Update `frontend/config.js`:
```javascript
window.ENV = {
    API_KEY: 'your-key',  // Add this line
    // ... other config
};
```

### Problem: "API authentication not properly configured"

**Cause**: API_KEY environment variable not set in backend.

**Solution**: Add to `.env` file:
```bash
API_KEY=your-key
```

### Problem: CORS errors with authentication

**Cause**: Usually not related to authentication - CORS is already configured.

**Solution**: 
1. Verify API_KEY is correct
2. Check CORS_ORIGINS environment variable
3. Ensure frontend origin is in allowed origins

## Best Practices

### 1. Key Generation
- Use cryptographically secure random keys
- Minimum 32 characters
- Never use predictable keys like "password" or "admin"

### 2. Key Storage
- Never commit keys to version control
- Use `.env` files (add to `.gitignore`)
- Use secrets manager in production (AWS Secrets Manager, etc.)

### 3. Key Transmission
- Always use HTTPS in production
- Never include keys in URLs
- Use headers only

### 4. Key Rotation
- Rotate keys every 90 days
- Have a rotation procedure documented
- Test rotation in staging first

### 5. Monitoring
- Monitor authentication failures
- Set up alerts for suspicious activity
- Review logs regularly

## Documentation

For more detailed information, see:

- **[API-AUTHENTICATION-IMPLEMENTATION.md](./API-AUTHENTICATION-IMPLEMENTATION.md)** - Full implementation details
- **[API-AUTHENTICATION-QUICK-REFERENCE.md](./API-AUTHENTICATION-QUICK-REFERENCE.md)** - Quick reference guide
- **[API-AUTHENTICATION-VALIDATION-CHECKLIST.md](./API-AUTHENTICATION-VALIDATION-CHECKLIST.md)** - Testing checklist
- **[API-AUTHENTICATION-SUMMARY.md](./API-AUTHENTICATION-SUMMARY.md)** - Implementation summary
- **[SECURITY.md](./SECURITY.md)** - Overall security documentation

## Support

If you encounter issues:

1. Check this README for common problems
2. Review the error message carefully
3. Check the logs: `grep "API key" fir_pipeline.log`
4. Run the test suite: `python test_api_authentication.py`
5. Consult the detailed documentation above

## Changelog

- **2025-02-12**: Initial API authentication implementation
  - Added APIAuthMiddleware for all endpoints
  - Frontend integration with automatic headers
  - Comprehensive documentation and testing
  - Production-ready deployment support

