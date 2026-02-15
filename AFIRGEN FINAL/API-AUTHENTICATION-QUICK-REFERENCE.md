# API Authentication Quick Reference

## Quick Setup

### 1. Generate API Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Backend Configuration
Add to `.env`:
```bash
API_KEY=<your-generated-key>
```

### 3. Frontend Configuration
Update `frontend/config.js`:
```javascript
window.ENV = {
    API_BASE_URL: 'http://localhost:8000',
    API_KEY: '<same-key-as-backend>',
    ENVIRONMENT: 'development',
    ENABLE_DEBUG: true,
};
```

## API Usage

### Using X-API-Key Header (Recommended)
```bash
curl -X POST http://localhost:8000/process \
  -H "X-API-Key: your-api-key" \
  -F "text=Test complaint"
```

### Using Authorization Bearer Token
```bash
curl -X POST http://localhost:8000/process \
  -H "Authorization: Bearer your-api-key" \
  -F "text=Test complaint"
```

### JavaScript/Frontend
```javascript
fetch(`${API_BASE}/process`, {
    method: 'POST',
    headers: {
        'X-API-Key': API_KEY
    },
    body: formData
});
```

## Public Endpoints (No Auth Required)
- `/health` - Health check
- `/docs` - API documentation
- `/redoc` - Alternative API docs
- `/openapi.json` - OpenAPI schema

## Protected Endpoints (Auth Required)
All other endpoints require authentication:
- `/process` - Start FIR processing
- `/validate` - Validate steps
- `/regenerate/{session_id}` - Regenerate content
- `/session/{session_id}/status` - Session status
- `/fir/{fir_number}` - FIR status
- `/fir/{fir_number}/content` - FIR content
- `/metrics` - Metrics
- `/list-firs` - List FIRs
- And more...

## Error Responses

### 401 - Missing API Key
```json
{
    "detail": "API key required. Include X-API-Key header or Authorization: Bearer <key>"
}
```

### 401 - Invalid API Key
```json
{
    "detail": "Invalid API key"
}
```

### 500 - Not Configured
```json
{
    "detail": "API authentication not properly configured"
}
```

## Testing

### Quick Test Script
```bash
# Test without key (should fail)
curl http://localhost:8000/process -F "text=test"

# Test with key (should succeed)
curl http://localhost:8000/process \
  -H "X-API-Key: your-key" \
  -F "text=This is a test complaint"

# Test health endpoint (should work without key)
curl http://localhost:8000/health
```

## Security Checklist

- [ ] Generate strong API key (32+ characters)
- [ ] Set API_KEY in backend .env
- [ ] Set API_KEY in frontend config.js
- [ ] Never commit API keys to git
- [ ] Use HTTPS in production
- [ ] Rotate keys every 90 days
- [ ] Monitor authentication failures
- [ ] Use AWS Secrets Manager in production

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "API key required" | Add X-API-Key header to request |
| "Invalid API key" | Verify key matches backend config |
| "Not properly configured" | Set API_KEY environment variable |
| Frontend 401 errors | Update config.js with API_KEY |
| CORS errors | Already configured, check API_KEY |

## Production Deployment

### AWS Secrets Manager
```bash
# Store secret
aws secretsmanager create-secret \
  --name afirgen/api-key \
  --secret-string '{"API_KEY":"your-key"}'

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
  frontend:
    environment:
      - API_KEY=${API_KEY}
```

### Environment Variables
```bash
# Set in shell
export API_KEY="your-key"

# Or in .env file
echo "API_KEY=your-key" >> .env
```

## Key Rotation

1. Generate new key
2. Update backend .env
3. Restart backend
4. Update frontend config.js
5. Deploy frontend
6. Verify all requests work
7. Remove old key

## Monitoring

### View Authentication Failures
```bash
grep "Invalid API key attempt" fir_pipeline.log
```

### Count Failures by IP
```bash
grep "Invalid API key attempt" fir_pipeline.log | \
  awk '{print $NF}' | sort | uniq -c | sort -rn
```

## Support

For detailed documentation, see:
- `API-AUTHENTICATION-IMPLEMENTATION.md` - Full implementation guide
- `SECURITY.md` - Security best practices
- `API-AUTHENTICATION-VALIDATION-CHECKLIST.md` - Testing checklist

