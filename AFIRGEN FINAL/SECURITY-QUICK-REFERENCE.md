# Security Quick Reference Guide

## For Developers

### Environment Setup

1. **Copy environment template**:
```bash
cp .env.example .env
```

2. **Generate secure auth key**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

3. **Update .env file**:
```bash
FIR_AUTH_KEY=<generated-key-from-step-2>
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Running Security Tests

```bash
# Start the services
docker-compose up -d

# Wait for services to be healthy
docker-compose ps

# Run security tests
python test_security.py
```

### Common Security Patterns

#### 1. Input Validation
```python
# Always sanitize user input
from main_backend.agentv5 import sanitise

user_input = sanitise(raw_input)
user_input = user_input.replace("<", "&lt;").replace(">", "&gt;")
```

#### 2. Session Validation
```python
# Validate session ID format
import uuid

try:
    uuid.UUID(session_id)
except ValueError:
    raise HTTPException(status_code=400, detail="Invalid session ID format")
```

#### 3. Authentication
```python
# Use constant-time comparison
import hmac

if not hmac.compare_digest(provided_key, expected_key):
    raise HTTPException(status_code=401, detail="Invalid authentication")
```

#### 4. File Upload Validation
```python
# Validate file size and type
if len(content) > CFG["max_file_size"]:
    raise HTTPException(status_code=413, detail="File too large")

if file.content_type not in CFG["allowed_types"]:
    raise HTTPException(status_code=415, detail="Unsupported file type")
```

### Security Checklist for New Endpoints

- [ ] Input validation implemented
- [ ] Output sanitization (if HTML)
- [ ] Authentication required (if sensitive)
- [ ] Rate limiting considered
- [ ] Error messages don't leak sensitive info
- [ ] Logging added for security events
- [ ] Tests written

### Production Deployment Checklist

- [ ] Strong `FIR_AUTH_KEY` set (min 32 chars)
- [ ] `CORS_ORIGINS` set to specific domains (no wildcards)
- [ ] HTTPS enabled
- [ ] Security headers verified
- [ ] Rate limits configured appropriately
- [ ] Database credentials secured
- [ ] Secrets in AWS Secrets Manager
- [ ] Security tests passing
- [ ] Logs monitored

### Security Monitoring

#### Key Metrics to Monitor
1. Failed authentication attempts
2. Rate limit violations
3. Invalid input attempts (400 errors)
4. Unusual traffic patterns
5. Error rates

#### Log Locations
- Main backend: `fir_pipeline.log`
- Model server: `model_server.log`
- ASR/OCR server: `asr_ocr_server.log`

### Incident Response

If you suspect a security incident:

1. **Immediate Actions**:
   - Check logs for suspicious activity
   - Review recent authentication attempts
   - Check rate limit violations

2. **Containment**:
   - Rotate `FIR_AUTH_KEY` if compromised
   - Update CORS origins if needed
   - Restart services with new configuration

3. **Investigation**:
   - Review all logs
   - Check database for unauthorized access
   - Verify file uploads

4. **Recovery**:
   - Apply security patches
   - Update configurations
   - Document incident

### Common Security Issues

#### Issue: CORS errors in browser
**Solution**: Add your frontend domain to `CORS_ORIGINS` in `.env`

#### Issue: Rate limit hit during development
**Solution**: Increase `RATE_LIMIT_REQUESTS` or restart services to reset

#### Issue: Authentication failing
**Solution**: Verify `FIR_AUTH_KEY` matches in both client and server

#### Issue: File upload rejected
**Solution**: Check file size (<25MB) and type (allowed extensions)

### Security Resources

- Full documentation: `SECURITY.md`
- Implementation summary: `SECURITY-IMPLEMENTATION-SUMMARY.md`
- Test script: `test_security.py`
- Environment template: `.env.example`

### Contact

For security issues: [security@yourdomain.com]

**Do not disclose security vulnerabilities publicly.**
