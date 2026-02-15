# HTTPS/TLS Quick Reference

## Quick Setup Commands

### Development (Self-Signed Certificate)

**Linux/macOS**:
```bash
cd "AFIRGEN FINAL"
chmod +x scripts/generate-certs.sh
./scripts/generate-certs.sh  # Select option 1
docker-compose up -d
```

**Windows (PowerShell)**:
```powershell
cd "AFIRGEN FINAL"
.\scripts\generate-certs.ps1
docker-compose up -d
```

**Access**: https://localhost (accept browser warning)

### Production (Let's Encrypt)

```bash
cd "AFIRGEN FINAL"
chmod +x scripts/generate-certs.sh
./scripts/generate-certs.sh  # Select option 2
# Enter domain and email
docker-compose up -d
```

## Common Commands

### Certificate Management

```bash
# Generate self-signed certificate
./scripts/generate-certs.sh

# Check certificate expiration
openssl x509 -in nginx/ssl/cert.pem -noout -enddate

# Verify certificate
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Test TLS connection
openssl s_client -connect localhost:443 -servername localhost
```

### Service Management

```bash
# Start all services
docker-compose up -d

# Restart nginx only
docker-compose restart nginx

# View nginx logs
docker-compose logs -f nginx

# Check service status
docker-compose ps
```

### Testing

```bash
# Test HTTPS endpoint
curl -k https://localhost/health

# Test HTTP redirect
curl -I http://localhost

# Check security headers
curl -I -k https://localhost

# Test API endpoint
curl -k https://localhost/api/health
```

## File Locations

```
AFIRGEN FINAL/
├── nginx/
│   ├── nginx.conf          # Nginx configuration
│   ├── Dockerfile          # Nginx container build
│   └── ssl/                # TLS certificates
│       ├── cert.pem        # Certificate file
│       └── key.pem         # Private key file
├── scripts/
│   ├── generate-certs.sh   # Certificate generation (Linux/macOS)
│   └── generate-certs.ps1  # Certificate generation (Windows)
└── docker-compose.yaml     # Service orchestration
```

## Environment Variables

```bash
# .env file
CORS_ORIGINS=https://yourdomain.com
API_BASE_URL=https://yourdomain.com
ENFORCE_HTTPS=true
```

## Ports

- **80**: HTTP (redirects to HTTPS)
- **443**: HTTPS (main entry point)
- **8000**: Main backend (internal only)
- **8001**: GGUF model server (internal only)
- **8002**: ASR/OCR server (internal only)

## URL Paths

- `/` - Frontend
- `/api/*` - Main backend API
- `/health` - Health check
- `/metrics` - Performance metrics
- `/reliability` - Reliability status

## Troubleshooting

### Certificate not found
```bash
ls -la nginx/ssl/
# If missing, run: ./scripts/generate-certs.sh
```

### Cannot connect to HTTPS
```bash
docker-compose ps nginx
docker-compose logs nginx
netstat -tuln | grep -E ':(80|443)'
```

### 502 Bad Gateway
```bash
docker-compose ps
docker-compose logs fir_pipeline
docker-compose restart
```

### Let's Encrypt fails
```bash
# Check DNS
nslookup yourdomain.com

# Check port 80 accessibility
curl http://yourdomain.com/.well-known/acme-challenge/test

# Check certbot logs
sudo cat /var/log/letsencrypt/letsencrypt.log
```

## Certificate Renewal

### Manual Renewal
```bash
sudo certbot renew
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
docker-compose restart nginx
```

### Automatic Renewal (Cron)
```bash
sudo crontab -e
# Add:
0 0 * * * certbot renew --quiet --post-hook "docker-compose -f /path/to/docker-compose.yaml restart nginx"
```

## Security Checklist

- [ ] TLS 1.2+ only (no TLS 1.0/1.1)
- [ ] Strong cipher suites configured
- [ ] HSTS header enabled
- [ ] HTTP redirects to HTTPS
- [ ] Security headers present
- [ ] Certificate not expired
- [ ] OCSP stapling enabled
- [ ] Model servers not externally accessible
- [ ] Rate limiting enabled
- [ ] CORS properly configured

## Testing Checklist

- [ ] HTTPS works: `curl -k https://localhost/health`
- [ ] HTTP redirects: `curl -I http://localhost`
- [ ] API accessible: `curl -k https://localhost/api/health`
- [ ] Security headers present: `curl -I -k https://localhost`
- [ ] Certificate valid: `openssl x509 -in nginx/ssl/cert.pem -noout -dates`
- [ ] Services healthy: `docker-compose ps`
- [ ] Logs clean: `docker-compose logs nginx`

## Production Deployment

1. Generate Let's Encrypt certificate
2. Update `.env` with HTTPS URLs
3. Configure DNS to point to server
4. Open ports 80 and 443 in firewall
5. Start services: `docker-compose up -d`
6. Test with SSL Labs: https://www.ssllabs.com/ssltest/
7. Setup automatic certificate renewal
8. Monitor certificate expiration

## Support

For detailed documentation, see:
- `HTTPS-TLS-IMPLEMENTATION.md` - Complete implementation guide
- `HTTPS-TLS-VALIDATION-CHECKLIST.md` - Validation checklist
- `SECURITY.md` - Security best practices
