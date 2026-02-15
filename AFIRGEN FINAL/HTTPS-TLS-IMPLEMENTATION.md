# HTTPS/TLS Implementation Guide

## Overview

AFIRGen now supports HTTPS/TLS encryption for all traffic using an nginx reverse proxy. This implementation provides:

- **TLS 1.2 and TLS 1.3** support with modern cipher suites
- **HTTP to HTTPS redirection** for all traffic
- **Security headers** (HSTS, CSP, X-Frame-Options, etc.)
- **Let's Encrypt support** for production deployments
- **Self-signed certificates** for development/testing
- **Certificate management scripts** for easy setup

## Architecture

```
Internet
    ↓
[Nginx Reverse Proxy] (Port 443 HTTPS, Port 80 HTTP→HTTPS redirect)
    ↓
    ├─→ [Frontend] (Port 80, internal)
    ├─→ [Main Backend API] (Port 8000, internal)
    ├─→ [GGUF Model Server] (Port 8001, internal - blocked from external access)
    └─→ [ASR/OCR Server] (Port 8002, internal - blocked from external access)
```

### Key Features

1. **TLS Termination**: Nginx handles all TLS encryption/decryption
2. **Internal Communication**: Services communicate over HTTP internally (within Docker network)
3. **Security**: Model servers are not directly accessible from the internet
4. **Performance**: Connection pooling and HTTP/2 support

## Quick Start

### Development (Self-Signed Certificate)

1. **Generate self-signed certificate**:

   **Linux/macOS**:
   ```bash
   cd "AFIRGEN FINAL"
   chmod +x scripts/generate-certs.sh
   ./scripts/generate-certs.sh
   # Select option 1 for self-signed certificate
   ```

   **Windows (PowerShell)**:
   ```powershell
   cd "AFIRGEN FINAL"
   .\scripts\generate-certs.ps1
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - HTTPS: https://localhost (will show browser warning for self-signed cert)
   - HTTP: http://localhost (automatically redirects to HTTPS)

4. **Accept browser warning**:
   - Chrome: Click "Advanced" → "Proceed to localhost (unsafe)"
   - Firefox: Click "Advanced" → "Accept the Risk and Continue"
   - Edge: Click "Advanced" → "Continue to localhost (unsafe)"

### Production (Let's Encrypt)

1. **Prerequisites**:
   - Domain name pointing to your server
   - Port 80 and 443 accessible from the internet
   - certbot installed on the server

2. **Generate Let's Encrypt certificate**:
   ```bash
   cd "AFIRGEN FINAL"
   chmod +x scripts/generate-certs.sh
   ./scripts/generate-certs.sh
   # Select option 2 for Let's Encrypt
   # Enter your domain name and email
   ```

3. **Update environment variables**:
   ```bash
   # Edit .env file
   CORS_ORIGINS=https://yourdomain.com
   API_BASE_URL=https://yourdomain.com
   ENFORCE_HTTPS=true
   ```

4. **Start services**:
   ```bash
   docker-compose up -d
   ```

5. **Setup automatic renewal**:
   ```bash
   # Test renewal
   sudo certbot renew --dry-run
   
   # Add cron job for automatic renewal
   sudo crontab -e
   # Add this line:
   0 0 * * * certbot renew --quiet --post-hook "docker-compose -f /path/to/docker-compose.yaml restart nginx"
   ```

## Certificate Management

### Using Existing Certificates

If you already have TLS certificates:

1. **Copy certificates to the SSL directory**:
   ```bash
   mkdir -p "AFIRGEN FINAL/nginx/ssl"
   cp /path/to/your/certificate.crt "AFIRGEN FINAL/nginx/ssl/cert.pem"
   cp /path/to/your/private-key.key "AFIRGEN FINAL/nginx/ssl/key.pem"
   chmod 600 "AFIRGEN FINAL/nginx/ssl/key.pem"
   chmod 644 "AFIRGEN FINAL/nginx/ssl/cert.pem"
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

### Certificate Renewal

**Let's Encrypt certificates expire in 90 days**. To renew:

1. **Manual renewal**:
   ```bash
   sudo certbot renew
   # Copy renewed certificates
   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem "AFIRGEN FINAL/nginx/ssl/cert.pem"
   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem "AFIRGEN FINAL/nginx/ssl/key.pem"
   # Restart nginx
   docker-compose restart nginx
   ```

2. **Automatic renewal** (recommended):
   ```bash
   # Add to crontab
   0 0 * * * certbot renew --quiet && \
     cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /path/to/AFIRGEN\ FINAL/nginx/ssl/cert.pem && \
     cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /path/to/AFIRGEN\ FINAL/nginx/ssl/key.pem && \
     docker-compose -f /path/to/AFIRGEN\ FINAL/docker-compose.yaml restart nginx
   ```

## Configuration

### Nginx Configuration

The nginx configuration is located at `nginx/nginx.conf`. Key settings:

- **TLS Protocols**: TLS 1.2 and 1.3 only
- **Cipher Suites**: Modern, secure ciphers (ECDHE, AES-GCM, ChaCha20-Poly1305)
- **HSTS**: Enabled with 1-year max-age
- **OCSP Stapling**: Enabled for better performance
- **Security Headers**: CSP, X-Frame-Options, X-Content-Type-Options, etc.

### Environment Variables

Update `.env` file for HTTPS:

```bash
# CORS - Use HTTPS URLs in production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# API Base URL - Use HTTPS in production
API_BASE_URL=https://yourdomain.com

# Enforce HTTPS
ENFORCE_HTTPS=true
```

### Frontend Configuration

Update `frontend/config.js` for production:

```javascript
window.ENV = {
    API_BASE_URL: 'https://yourdomain.com',
    ENVIRONMENT: 'production',
    ENABLE_DEBUG: false,
};
```

Or use Docker build args:

```bash
docker-compose build --build-arg API_BASE_URL=https://yourdomain.com frontend
```

## Security Features

### TLS Configuration

- **Protocols**: TLS 1.2, TLS 1.3 (TLS 1.0 and 1.1 disabled)
- **Cipher Suites**: Modern, forward-secret ciphers only
- **Session Tickets**: Disabled for better security
- **OCSP Stapling**: Enabled for certificate validation

### Security Headers

All responses include:

- `Strict-Transport-Security`: Force HTTPS for 1 year
- `X-Frame-Options`: Prevent clickjacking
- `X-Content-Type-Options`: Prevent MIME sniffing
- `X-XSS-Protection`: Enable XSS filter
- `Content-Security-Policy`: Restrict resource loading
- `Referrer-Policy`: Control referrer information
- `Permissions-Policy`: Disable unnecessary browser features

### Access Control

- **Model servers** (ports 8001, 8002) are not accessible from the internet
- Only the main backend API is exposed through `/api/` path
- Health checks and metrics endpoints are accessible
- Rate limiting is enforced at the application level

## Testing

### Verify HTTPS Setup

1. **Check certificate**:
   ```bash
   openssl s_client -connect localhost:443 -servername localhost
   ```

2. **Test HTTP to HTTPS redirect**:
   ```bash
   curl -I http://localhost
   # Should return 301 redirect to https://localhost
   ```

3. **Test API endpoint**:
   ```bash
   curl -k https://localhost/health
   # Should return health status
   ```

4. **Check security headers**:
   ```bash
   curl -I -k https://localhost
   # Should show security headers
   ```

### SSL Labs Test

For production deployments, test your TLS configuration:

1. Visit: https://www.ssllabs.com/ssltest/
2. Enter your domain name
3. Wait for the scan to complete
4. Aim for an **A or A+** rating

## Troubleshooting

### Certificate Errors

**Problem**: Browser shows "Your connection is not private"

**Solution**:
- For development: This is expected with self-signed certificates. Click "Advanced" and proceed.
- For production: Ensure Let's Encrypt certificate is properly installed and not expired.

**Problem**: Certificate file not found

**Solution**:
```bash
# Check if certificates exist
ls -la "AFIRGEN FINAL/nginx/ssl/"
# Should show cert.pem and key.pem

# If missing, regenerate
cd "AFIRGEN FINAL"
./scripts/generate-certs.sh
```

### Connection Errors

**Problem**: Cannot connect to HTTPS

**Solution**:
```bash
# Check if nginx is running
docker-compose ps nginx

# Check nginx logs
docker-compose logs nginx

# Verify ports are open
netstat -tuln | grep -E ':(80|443)'
```

**Problem**: "502 Bad Gateway" error

**Solution**:
```bash
# Check if backend services are healthy
docker-compose ps

# Check backend logs
docker-compose logs fir_pipeline

# Restart services
docker-compose restart
```

### Let's Encrypt Issues

**Problem**: Certificate request fails

**Solution**:
- Ensure port 80 is accessible from the internet
- Verify DNS points to your server: `nslookup yourdomain.com`
- Check firewall rules: `sudo ufw status`
- Review certbot logs: `sudo cat /var/log/letsencrypt/letsencrypt.log`

## AWS Deployment

For AWS deployment with Application Load Balancer (ALB):

1. **Use ALB for TLS termination** (recommended):
   - Configure ALB with ACM certificate
   - ALB handles HTTPS, forwards HTTP to containers
   - No need for nginx reverse proxy in this case

2. **Or use nginx with Let's Encrypt**:
   - Deploy nginx container with Let's Encrypt
   - Use EFS to persist certificates across container restarts
   - Setup automatic renewal with ECS scheduled tasks

See `AWS-DEPLOYMENT-GUIDE.md` for detailed instructions.

## Performance Considerations

### HTTP/2

Nginx is configured with HTTP/2 support for better performance:
- Multiplexing: Multiple requests over single connection
- Header compression: Reduced bandwidth usage
- Server push: Proactive resource delivery (if needed)

### Connection Pooling

- Nginx maintains connection pools to backend services
- Reduces connection overhead
- Improves response times

### Caching

- Static assets cached for 1 year
- HTML files not cached (always fresh)
- API responses cached at application level

## Monitoring

### Health Checks

- Nginx health check: `https://localhost/health`
- Returns status of all backend services
- Includes circuit breaker and reliability status

### Logs

View nginx logs:
```bash
# Access logs
docker-compose logs nginx | grep "GET\|POST"

# Error logs
docker-compose logs nginx | grep "error"

# Follow logs in real-time
docker-compose logs -f nginx
```

### Metrics

- Access metrics endpoint: `https://localhost/metrics`
- Monitor TLS handshake times
- Track error rates

## Best Practices

1. **Use Let's Encrypt in production** - Free, automated, trusted certificates
2. **Enable HSTS** - Force HTTPS for all future visits
3. **Monitor certificate expiration** - Setup alerts 30 days before expiry
4. **Use strong cipher suites** - Disable weak/deprecated ciphers
5. **Keep nginx updated** - Apply security patches regularly
6. **Test regularly** - Use SSL Labs to verify configuration
7. **Backup certificates** - Store securely in case of server failure
8. **Use HTTP/2** - Better performance than HTTP/1.1
9. **Enable OCSP stapling** - Faster certificate validation
10. **Restrict access** - Only expose necessary endpoints

## References

- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)
- [Nginx SSL/TLS Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
