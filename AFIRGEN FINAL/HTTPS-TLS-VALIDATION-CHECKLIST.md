# HTTPS/TLS Validation Checklist

## Pre-Deployment Validation

### Certificate Setup
- [ ] Certificates generated and placed in `nginx/ssl/` directory
- [ ] Certificate file exists: `nginx/ssl/cert.pem`
- [ ] Private key file exists: `nginx/ssl/key.pem`
- [ ] Private key has correct permissions (600)
- [ ] Certificate is valid (not expired)
- [ ] Certificate matches private key

**Verification Commands**:
```bash
# Check files exist
ls -la nginx/ssl/

# Check permissions
stat nginx/ssl/key.pem  # Should be 600 or -rw-------

# Check certificate validity
openssl x509 -in nginx/ssl/cert.pem -noout -dates

# Verify certificate and key match
openssl x509 -noout -modulus -in nginx/ssl/cert.pem | openssl md5
openssl rsa -noout -modulus -in nginx/ssl/key.pem | openssl md5
# Both MD5 hashes should match
```

### Configuration Files
- [ ] `nginx/nginx.conf` exists and is valid
- [ ] `nginx/Dockerfile` exists
- [ ] `docker-compose.yaml` includes nginx service
- [ ] Environment variables configured in `.env`
- [ ] CORS_ORIGINS uses HTTPS URLs
- [ ] API_BASE_URL uses HTTPS URL

**Verification Commands**:
```bash
# Test nginx configuration syntax
docker run --rm -v $(pwd)/nginx/nginx.conf:/etc/nginx/nginx.conf:ro nginx nginx -t

# Check environment variables
cat .env | grep -E 'CORS_ORIGINS|API_BASE_URL|ENFORCE_HTTPS'
```

### Docker Setup
- [ ] All services have network configuration
- [ ] Nginx service defined in docker-compose.yaml
- [ ] Ports 80 and 443 exposed on nginx service
- [ ] Internal service ports removed from docker-compose
- [ ] Volume mounts configured for certificates
- [ ] Health checks configured

**Verification Commands**:
```bash
# Validate docker-compose syntax
docker-compose config

# Check for port conflicts
netstat -tuln | grep -E ':(80|443)'
```

## Deployment Validation

### Service Startup
- [ ] All services start successfully
- [ ] Nginx container is running
- [ ] No errors in nginx logs
- [ ] Health checks passing
- [ ] Services can communicate internally

**Verification Commands**:
```bash
# Check all services are running
docker-compose ps

# Check nginx logs
docker-compose logs nginx | tail -50

# Check health status
docker-compose ps | grep healthy
```

### TLS Configuration
- [ ] HTTPS endpoint accessible
- [ ] HTTP redirects to HTTPS
- [ ] TLS 1.2 and 1.3 enabled
- [ ] Weak ciphers disabled
- [ ] Certificate chain complete
- [ ] OCSP stapling working

**Verification Commands**:
```bash
# Test HTTPS connection
curl -k https://localhost/health

# Test HTTP redirect
curl -I http://localhost
# Should return 301 redirect

# Check TLS version
openssl s_client -connect localhost:443 -tls1_2 </dev/null 2>/dev/null | grep "Protocol"

# Check cipher suites
nmap --script ssl-enum-ciphers -p 443 localhost
```

### Security Headers
- [ ] Strict-Transport-Security header present
- [ ] X-Frame-Options header present
- [ ] X-Content-Type-Options header present
- [ ] X-XSS-Protection header present
- [ ] Content-Security-Policy header present
- [ ] Referrer-Policy header present

**Verification Commands**:
```bash
# Check all security headers
curl -I -k https://localhost

# Specific header checks
curl -I -k https://localhost | grep -i "strict-transport-security"
curl -I -k https://localhost | grep -i "x-frame-options"
curl -I -k https://localhost | grep -i "content-security-policy"
```

### API Functionality
- [ ] Health endpoint accessible via HTTPS
- [ ] API endpoints accessible via /api/ path
- [ ] Authentication working
- [ ] File uploads working
- [ ] Response times acceptable
- [ ] Error handling working

**Verification Commands**:
```bash
# Test health endpoint
curl -k https://localhost/health

# Test API endpoint
curl -k https://localhost/api/health

# Test with authentication (if configured)
curl -k -H "Authorization: Bearer YOUR_TOKEN" https://localhost/api/session/test-id/status
```

### Access Control
- [ ] Model servers not accessible externally
- [ ] Only nginx ports (80, 443) exposed
- [ ] Internal services accessible from nginx
- [ ] Rate limiting working
- [ ] CORS configured correctly

**Verification Commands**:
```bash
# Try to access model server directly (should fail)
curl http://localhost:8001/health
# Should fail with connection refused

# Check exposed ports
docker-compose ps | grep -E "0.0.0.0"
# Should only show ports 80 and 443 for nginx

# Test CORS
curl -k -H "Origin: https://yourdomain.com" -I https://localhost/health
```

## Post-Deployment Validation

### Performance Testing
- [ ] Response times under 200ms for API calls
- [ ] TLS handshake time acceptable (<100ms)
- [ ] No connection timeouts
- [ ] HTTP/2 working
- [ ] Connection pooling effective

**Verification Commands**:
```bash
# Test response time
time curl -k https://localhost/health

# Test TLS handshake time
curl -k -w "time_connect: %{time_connect}\ntime_starttransfer: %{time_starttransfer}\n" -o /dev/null -s https://localhost/health

# Check HTTP/2
curl -k -I --http2 https://localhost/health | grep "HTTP/2"

# Load test (requires apache bench)
ab -n 100 -c 10 -k https://localhost/health
```

### Security Testing
- [ ] SSL Labs test passes (A or A+ rating)
- [ ] No weak ciphers enabled
- [ ] No SSL/TLS vulnerabilities
- [ ] Certificate chain valid
- [ ] HSTS preload eligible

**Verification Commands**:
```bash
# Test with testssl.sh (if installed)
testssl.sh https://localhost

# Check for common vulnerabilities
nmap --script ssl-heartbleed,ssl-poodle,ssl-dh-params -p 443 localhost

# Verify HSTS
curl -I -k https://localhost | grep -i "strict-transport-security"
```

### Monitoring Setup
- [ ] Logs accessible and readable
- [ ] Metrics endpoint working
- [ ] Health checks reporting correctly
- [ ] Alerts configured (if applicable)
- [ ] Certificate expiration monitoring

**Verification Commands**:
```bash
# Check logs
docker-compose logs nginx | tail -100

# Check metrics
curl -k https://localhost/metrics

# Check reliability status
curl -k https://localhost/reliability

# Monitor logs in real-time
docker-compose logs -f nginx
```

### Certificate Management
- [ ] Certificate expiration date known
- [ ] Renewal process documented
- [ ] Automatic renewal configured (production)
- [ ] Backup of certificates exists
- [ ] Certificate rotation tested

**Verification Commands**:
```bash
# Check expiration date
openssl x509 -in nginx/ssl/cert.pem -noout -enddate

# Calculate days until expiration
echo $(( ($(date -d "$(openssl x509 -in nginx/ssl/cert.pem -noout -enddate | cut -d= -f2)" +%s) - $(date +%s)) / 86400 )) days

# Test renewal (Let's Encrypt)
sudo certbot renew --dry-run
```

## Production-Specific Validation

### DNS and Domain
- [ ] Domain points to correct server
- [ ] DNS propagation complete
- [ ] SSL certificate matches domain
- [ ] Wildcard certificate (if needed)
- [ ] Multiple domains configured (if needed)

**Verification Commands**:
```bash
# Check DNS
nslookup yourdomain.com

# Check from external location
curl -I https://yourdomain.com

# Verify certificate domain
openssl x509 -in nginx/ssl/cert.pem -noout -text | grep "DNS:"
```

### Firewall and Network
- [ ] Port 80 open in firewall
- [ ] Port 443 open in firewall
- [ ] Internal ports blocked externally
- [ ] Security groups configured (AWS)
- [ ] Network ACLs configured (AWS)

**Verification Commands**:
```bash
# Check firewall rules
sudo ufw status
# or
sudo iptables -L -n

# Test from external location
curl -I https://yourdomain.com

# Check port accessibility
nmap -p 80,443,8000,8001,8002 yourdomain.com
# Only 80 and 443 should be open
```

### Load Balancer (if applicable)
- [ ] ALB/ELB configured with SSL certificate
- [ ] Health checks configured
- [ ] Target groups healthy
- [ ] SSL policy configured
- [ ] Access logs enabled

**Verification (AWS)**:
```bash
# Check ALB status
aws elbv2 describe-load-balancers --names afirgen-alb

# Check target health
aws elbv2 describe-target-health --target-group-arn YOUR_TG_ARN

# Check SSL policy
aws elbv2 describe-ssl-policies --names ELBSecurityPolicy-TLS-1-2-2017-01
```

## Compliance Validation

### OWASP Top 10
- [ ] A01: Broken Access Control - CORS configured
- [ ] A02: Cryptographic Failures - TLS 1.2+ only
- [ ] A03: Injection - Input validation enabled
- [ ] A05: Security Misconfiguration - Security headers present
- [ ] A06: Vulnerable Components - Dependencies updated
- [ ] A07: Authentication Failures - Auth implemented
- [ ] A09: Security Logging - Logs enabled

### PCI DSS (if applicable)
- [ ] TLS 1.2 or higher
- [ ] Strong cryptography
- [ ] Certificate management process
- [ ] Access controls
- [ ] Logging and monitoring

### GDPR (if applicable)
- [ ] Data encryption in transit
- [ ] Secure communication channels
- [ ] Access logging
- [ ] Data protection measures

## Validation Report Template

```
HTTPS/TLS Validation Report
Date: _______________
Validator: _______________

Pre-Deployment:
- Certificate Setup: [ ] Pass [ ] Fail
- Configuration Files: [ ] Pass [ ] Fail
- Docker Setup: [ ] Pass [ ] Fail

Deployment:
- Service Startup: [ ] Pass [ ] Fail
- TLS Configuration: [ ] Pass [ ] Fail
- Security Headers: [ ] Pass [ ] Fail
- API Functionality: [ ] Pass [ ] Fail
- Access Control: [ ] Pass [ ] Fail

Post-Deployment:
- Performance Testing: [ ] Pass [ ] Fail
- Security Testing: [ ] Pass [ ] Fail
- Monitoring Setup: [ ] Pass [ ] Fail
- Certificate Management: [ ] Pass [ ] Fail

Production (if applicable):
- DNS and Domain: [ ] Pass [ ] Fail
- Firewall and Network: [ ] Pass [ ] Fail
- Load Balancer: [ ] Pass [ ] Fail

Overall Status: [ ] Pass [ ] Fail

Notes:
_________________________________
_________________________________
_________________________________

Signature: _______________
```

## Automated Validation Script

Save as `validate-https.sh`:

```bash
#!/bin/bash

echo "HTTPS/TLS Validation Script"
echo "============================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

PASS=0
FAIL=0

check() {
    if eval "$2" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $1"
        ((FAIL++))
    fi
}

echo "Certificate Checks:"
check "Certificate file exists" "test -f nginx/ssl/cert.pem"
check "Private key file exists" "test -f nginx/ssl/key.pem"
check "Certificate is valid" "openssl x509 -in nginx/ssl/cert.pem -noout -checkend 0"

echo ""
echo "Service Checks:"
check "Nginx container running" "docker-compose ps nginx | grep -q Up"
check "HTTPS endpoint accessible" "curl -k -f https://localhost/health"
check "HTTP redirects to HTTPS" "curl -I http://localhost 2>/dev/null | grep -q '301'"

echo ""
echo "Security Checks:"
check "HSTS header present" "curl -I -k https://localhost 2>/dev/null | grep -qi 'strict-transport-security'"
check "X-Frame-Options present" "curl -I -k https://localhost 2>/dev/null | grep -qi 'x-frame-options'"
check "CSP header present" "curl -I -k https://localhost 2>/dev/null | grep -qi 'content-security-policy'"

echo ""
echo "============================"
echo "Results: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC}"
echo "============================"

exit $FAIL
```

Run with:
```bash
chmod +x validate-https.sh
./validate-https.sh
```
