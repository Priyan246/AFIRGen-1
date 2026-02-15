# AFIRGen Security Implementation

## Overview
This document outlines the security measures implemented in AFIRGen to address vulnerabilities identified in the requirements document.

## Security Vulnerabilities Addressed

### 1. CORS Configuration ✅
**Issue**: CORS allowed all origins (`allow_origins=["*"]`)

**Fix**:
- CORS origins now configurable via `CORS_ORIGINS` environment variable
- Default restricted to `http://localhost:3000,http://localhost:8000`
- Wildcard (`*`) triggers warning in logs
- Production should use specific domain(s): `CORS_ORIGINS=https://yourdomain.com`

**Configuration**:
```bash
# .env file
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

**Implementation**: All three servers (main backend, GGUF model server, ASR/OCR server)

### 2. Rate Limiting ✅
**Issue**: No rate limiting

**Fix**:
- Implemented in-memory rate limiter
- Default: 100 requests per 60 seconds per IP address
- Configurable via environment variables
- Returns HTTP 429 (Too Many Requests) when limit exceeded

**Configuration**:
```bash
# .env file
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

**Implementation**: Main backend only (entry point for all user requests)

### 3. Input Validation & Sanitization ✅
**Issue**: Missing input sanitization in some endpoints

**Fix**:
- All text inputs sanitized using `sanitise()` function
- XSS prevention: HTML entities escaped (`<` → `&lt;`, `>` → `&gt;`)
- File size validation (max 25MB)
- File type validation using MIME types and extensions
- Session ID format validation (UUID format)
- FIR number format validation (regex pattern)

**Endpoints with input validation**:
- `/process` - text, audio, image uploads
- `/validate` - user_input sanitization
- `/regenerate/{session_id}` - user_input sanitization
- `/fir/{fir_number}` - FIR number format validation
- `/view_fir/{fir_number}` - FIR number validation + HTML escaping

### 4. Authentication Security ✅
**Issue**: Auth key stored in environment variable without encryption, simple comparison

**Fix**:
- Constant-time comparison using `hmac.compare_digest()` to prevent timing attacks
- Validation that auth key is not default value
- Failed authentication attempts logged with FIR number
- Returns HTTP 401 for invalid auth

**Configuration**:
```bash
# .env file
FIR_AUTH_KEY=your-secure-random-key-here-min-32-chars
```

**Best Practice**: Generate secure key using:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4.1 API Authentication ✅
**Issue**: No authentication required for API endpoints

**Fix**:
- Implemented `APIAuthMiddleware` for all endpoints except public ones
- Supports both `X-API-Key` and `Authorization: Bearer` headers
- Constant-time comparison to prevent timing attacks
- Public endpoints: `/health`, `/docs`, `/redoc`, `/openapi.json`
- All other endpoints require valid API key
- Failed authentication attempts logged with IP and endpoint

**Configuration**:
```bash
# .env file
API_KEY=your-secure-api-key-here-min-32-chars
```

**Usage**:
```bash
# Using X-API-Key header
curl -H "X-API-Key: your-key" http://localhost:8000/process

# Using Authorization Bearer token
curl -H "Authorization: Bearer your-key" http://localhost:8000/process
```

**Frontend Integration**:
```javascript
// config.js
window.ENV = {
    API_BASE_URL: 'http://localhost:8000',
    API_KEY: 'your-api-key',
};

// All requests include API key
fetch(url, {
    headers: { 'X-API-Key': API_KEY }
});
```

**Documentation**: See `API-AUTHENTICATION-IMPLEMENTATION.md` for full details

### 5. Security Headers ✅
**Issue**: Missing security headers

**Fix**: Implemented `SecurityHeadersMiddleware` with:
- `X-Content-Type-Options: nosniff` - Prevents MIME sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-XSS-Protection: 1; mode=block` - XSS protection
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` - HTTPS enforcement
- `Content-Security-Policy` - Restricts resource loading
- `Referrer-Policy: strict-origin-when-cross-origin` - Controls referrer information
- `Permissions-Policy` - Disables unnecessary browser features

**Implementation**: Main backend

### 6. Frontend API URL Configuration ✅
**Issue**: Frontend hardcodes `localhost:8000` - not configurable

**Fix**:
- Created `config.js` with environment-based configuration
- API URL configurable via `window.ENV.API_BASE_URL`
- Defaults to `http://localhost:8000` for development
- Can be overridden during deployment

**Usage**:
```javascript
// In production deployment, create config.js with:
window.ENV = {
    API_BASE_URL: 'https://api.yourdomain.com',
    ENVIRONMENT: 'production',
    ENABLE_DEBUG: false,
};
```

### 7. SQL Injection Prevention ✅
**Issue**: Potential SQL injection vulnerabilities

**Fix**:
- All database queries use parameterized statements
- FIR number format validation before database queries
- Session ID format validation (UUID)
- MySQL connection pool with proper escaping

**Example**:
```python
# Before: Vulnerable
cur.execute(f"SELECT * FROM fir_records WHERE fir_number = '{fir_number}'")

# After: Safe
cur.execute("SELECT * FROM fir_records WHERE fir_number = %s", (fir_number,))
```

### 8. XSS Prevention ✅
**Issue**: Potential XSS in HTML rendering

**Fix**:
- HTML escaping in `/view_fir/{fir_number}` endpoint using `html.escape()`
- Input sanitization removes/escapes HTML characters
- Content-Security-Policy header restricts inline scripts

### 9. File Upload Security ✅
**Issue**: Insufficient file validation

**Fix**:
- File extension whitelist
- MIME type validation
- File size limits (25MB)
- Secure filename generation using UUID
- Optional python-magic for deep MIME detection
- Temporary files cleaned up after processing

**Allowed file types**:
- Images: `.jpg`, `.jpeg`, `.png` (MIME: `image/jpeg`, `image/png`)
- Audio: `.wav`, `.mp3`, `.mpeg` (MIME: `audio/wav`, `audio/mpeg`, `audio/mp3`)

### 10. Session Security ✅
**Issue**: Session management vulnerabilities

**Fix**:
- Session IDs are UUIDs (cryptographically random)
- Session timeout configurable (default: 3600 seconds)
- Automatic session cleanup
- Session status validation before operations
- SQLite persistence with proper locking

**Configuration**:
```bash
# .env file
SESSION_TIMEOUT=3600
```

## Security Best Practices

### Production Deployment Checklist

1. **Environment Variables**
   - [ ] Set strong `FIR_AUTH_KEY` (min 32 characters)
   - [ ] Set strong `API_KEY` (min 32 characters)
   - [ ] Configure specific `CORS_ORIGINS` (no wildcards)
   - [ ] Set appropriate `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW`
   - [ ] Use strong `MYSQL_PASSWORD`

2. **HTTPS/TLS**
   - [ ] Deploy behind HTTPS load balancer
   - [ ] Obtain SSL/TLS certificate (Let's Encrypt or ACM)
   - [ ] Set `ENFORCE_HTTPS=true` in environment
   - [ ] Update frontend `config.js` with HTTPS API URL

3. **Database Security**
   - [ ] Use strong MySQL passwords
   - [ ] Restrict MySQL access to application subnet only
   - [ ] Enable MySQL SSL/TLS connections
   - [ ] Regular database backups

4. **Network Security**
   - [ ] Use VPC with private subnets for services
   - [ ] Security groups: Allow only necessary ports
   - [ ] NAT Gateway for outbound internet access
   - [ ] No direct internet access to databases

5. **Secrets Management**
   - [ ] Use AWS Secrets Manager or similar
   - [ ] Rotate credentials regularly
   - [ ] Never commit secrets to version control
   - [ ] Use `.env` file (not committed)

6. **Monitoring & Logging**
   - [ ] Enable CloudWatch logging
   - [ ] Set up alerts for failed authentication attempts
   - [ ] Monitor rate limit violations
   - [ ] Track error rates

7. **Docker Security**
   - [ ] Run containers as non-root user
   - [ ] Use read-only volumes where possible
   - [ ] Scan images for vulnerabilities
   - [ ] Keep base images updated

## Remaining Security Considerations

### Not Yet Implemented (Future Enhancements)

1. **Audit Logging**
   - Log all FIR creation/modification events
   - Track user actions with timestamps
   - Implement log retention policies

3. **Data Encryption**
   - Encrypt sensitive data at rest (database encryption)
   - Encrypt temporary files
   - Use encrypted volumes in production

4. **DDoS Protection**
   - Current rate limiting is basic
   - Consider AWS WAF or CloudFlare
   - Implement request throttling at load balancer

5. **Vulnerability Scanning**
   - Regular dependency updates
   - Automated security scanning (Snyk, Dependabot)
   - Penetration testing

6. **Compliance**
   - GDPR compliance for personal data
   - Data retention policies
   - Right to deletion implementation

## Security Testing

### Manual Testing

1. **CORS Testing**
```bash
curl -H "Origin: https://malicious.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS http://localhost:8000/process
# Should return 403 or no CORS headers
```

2. **Rate Limiting Testing**
```bash
for i in {1..101}; do
  curl http://localhost:8000/health
done
# 101st request should return 429
```

3. **Input Validation Testing**
```bash
# Test XSS
curl -X POST http://localhost:8000/process \
     -F "text=<script>alert('xss')</script>"
# Should sanitize input

# Test SQL injection
curl http://localhost:8000/fir/FIR-test' OR '1'='1
# Should return 400 (invalid format)
```

4. **Authentication Testing**
```bash
# Test timing attack resistance
time curl -X POST http://localhost:8000/authenticate \
     -H "Content-Type: application/json" \
     -d '{"fir_number":"FIR-12345678-20250101000000","auth_key":"wrong"}'
# Time should be consistent regardless of key
```

### Automated Testing

Consider implementing:
- OWASP ZAP for vulnerability scanning
- Burp Suite for penetration testing
- Security unit tests for input validation

## Incident Response

### Security Incident Procedure

1. **Detection**
   - Monitor logs for suspicious activity
   - Set up alerts for authentication failures
   - Track rate limit violations

2. **Response**
   - Isolate affected systems
   - Rotate compromised credentials
   - Review access logs

3. **Recovery**
   - Restore from backups if needed
   - Apply security patches
   - Update security configurations

4. **Post-Incident**
   - Document incident
   - Update security measures
   - Conduct security review

## Contact

For security issues, please contact the security team at: [security@yourdomain.com]

**Do not disclose security vulnerabilities publicly.**

## Changelog

- **2025-01-XX**: Initial security implementation
  - CORS configuration
  - Rate limiting
  - Input validation
  - Security headers
  - Authentication improvements
