# Nginx Reverse Proxy with HTTPS/TLS

This directory contains the nginx reverse proxy configuration for AFIRGen with HTTPS/TLS support.

## Files

- `nginx.conf` - Main nginx configuration with TLS settings
- `Dockerfile` - Container build file for nginx with SSL support
- `ssl/` - Directory for TLS certificates (created automatically)
  - `cert.pem` - TLS certificate
  - `key.pem` - Private key

## Quick Start

### 1. Generate Certificates

**Development (Self-Signed)**:
```bash
cd ..
./scripts/generate-certs.sh  # Select option 1
```

**Production (Let's Encrypt)**:
```bash
cd ..
./scripts/generate-certs.sh  # Select option 2
```

### 2. Start Services

```bash
cd ..
docker-compose up -d
```

### 3. Access Application

- HTTPS: https://localhost
- HTTP: http://localhost (redirects to HTTPS)

## Configuration

### TLS Settings

The nginx configuration uses:
- **Protocols**: TLS 1.2 and TLS 1.3 only
- **Ciphers**: Modern, forward-secret cipher suites
- **Session Cache**: 50MB shared cache
- **OCSP Stapling**: Enabled for better performance

### Security Headers

All responses include:
- `Strict-Transport-Security` - Force HTTPS
- `X-Frame-Options` - Prevent clickjacking
- `X-Content-Type-Options` - Prevent MIME sniffing
- `X-XSS-Protection` - Enable XSS filter
- `Content-Security-Policy` - Restrict resource loading
- `Referrer-Policy` - Control referrer information
- `Permissions-Policy` - Disable unnecessary features

### URL Routing

- `/` → Frontend (port 80, internal)
- `/api/*` → Main Backend (port 8000, internal)
- `/health` → Health check endpoint
- `/metrics` → Performance metrics
- `/reliability` → Reliability status

### Access Control

- Model servers (ports 8001, 8002) are NOT accessible externally
- Only nginx ports (80, 443) are exposed to the internet
- Internal services communicate over Docker network

## Certificate Management

### Self-Signed Certificates

Generated automatically during Docker build for development. To regenerate:

```bash
cd ..
./scripts/generate-certs.sh  # Select option 1
docker-compose restart nginx
```

### Let's Encrypt Certificates

For production deployments:

1. **Initial Setup**:
   ```bash
   cd ..
   ./scripts/generate-certs.sh  # Select option 2
   # Enter domain and email
   ```

2. **Automatic Renewal**:
   ```bash
   # Add to crontab
   sudo crontab -e
   # Add:
   0 0 * * * certbot renew --quiet --post-hook "docker-compose -f /path/to/docker-compose.yaml restart nginx"
   ```

3. **Manual Renewal**:
   ```bash
   sudo certbot renew
   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
   docker-compose restart nginx
   ```

### Custom Certificates

To use your own certificates:

```bash
# Copy certificates
cp /path/to/your/certificate.crt ssl/cert.pem
cp /path/to/your/private-key.key ssl/key.pem

# Set permissions
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem

# Restart nginx
docker-compose restart nginx
```

## Testing

### Manual Testing

```bash
# Test HTTPS
curl -k https://localhost/health

# Test HTTP redirect
curl -I http://localhost

# Test security headers
curl -I -k https://localhost

# Check certificate
openssl s_client -connect localhost:443 -servername localhost
```

### Automated Testing

```bash
cd ..
python test_https_tls.py
```

### Validation Script

```bash
cd ..
./scripts/validate-https.sh
```

## Troubleshooting

### Certificate Errors

**Problem**: "Certificate file not found"

**Solution**:
```bash
ls -la ssl/
# If missing, run:
cd ..
./scripts/generate-certs.sh
```

### Connection Errors

**Problem**: "Connection refused"

**Solution**:
```bash
# Check if nginx is running
docker-compose ps nginx

# Check logs
docker-compose logs nginx

# Restart nginx
docker-compose restart nginx
```

### 502 Bad Gateway

**Problem**: Nginx returns 502 error

**Solution**:
```bash
# Check backend services
docker-compose ps

# Check backend logs
docker-compose logs fir_pipeline

# Restart all services
docker-compose restart
```

### Port Conflicts

**Problem**: "Port 443 already in use"

**Solution**:
```bash
# Check what's using the port
netstat -tuln | grep :443
# or
lsof -i :443

# Stop conflicting service or change nginx port
```

## Monitoring

### Logs

```bash
# View all logs
docker-compose logs nginx

# Follow logs in real-time
docker-compose logs -f nginx

# View last 100 lines
docker-compose logs --tail=100 nginx

# View error logs only
docker-compose logs nginx | grep error
```

### Health Check

```bash
# Check nginx health
curl -k https://localhost/health

# Check all services
docker-compose ps
```

### Metrics

```bash
# View performance metrics
curl -k https://localhost/metrics

# View reliability status
curl -k https://localhost/reliability
```

## Performance

### HTTP/2

Nginx is configured with HTTP/2 support for better performance:
- Multiple requests over single connection
- Header compression
- Server push capability

### Connection Pooling

- Nginx maintains connection pools to backend services
- Reduces connection overhead
- Improves response times

### Caching

- Static assets cached for 1 year
- HTML files not cached (always fresh)
- API responses cached at application level

## Security Best Practices

1. **Use Let's Encrypt in production** - Free, automated, trusted
2. **Keep certificates updated** - Monitor expiration dates
3. **Use strong cipher suites** - Disable weak/deprecated ciphers
4. **Enable HSTS** - Force HTTPS for all future visits
5. **Monitor logs** - Watch for suspicious activity
6. **Regular updates** - Keep nginx and dependencies updated
7. **Restrict access** - Only expose necessary endpoints
8. **Test regularly** - Use SSL Labs to verify configuration

## References

- [Nginx SSL/TLS Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)

## Support

For detailed documentation, see:
- `../HTTPS-TLS-IMPLEMENTATION.md` - Complete implementation guide
- `../HTTPS-TLS-QUICK-REFERENCE.md` - Quick reference
- `../HTTPS-TLS-VALIDATION-CHECKLIST.md` - Validation checklist
- `../HTTPS-TLS-SUMMARY.md` - Implementation summary
