# Frontend API URL Configuration - Implementation Summary

## Overview
The AFIRGen frontend has been updated to support configurable API endpoints for different deployment environments (development, staging, production).

## Changes Made

### 1. Configuration System
**File: `frontend/config.js`**
- Enhanced with deployment instructions and examples
- Supports environment variable substitution
- Allows runtime override via `window.ENV_OVERRIDE`
- Default: `http://localhost:8000` for development

### 2. Security Updates
**File: `frontend/base.html`**
- Updated Content Security Policy (CSP) to allow HTTPS connections
- Changed `connect-src` from `http://localhost:8000` to `http://localhost:8000 https://*`
- Enables production deployments with HTTPS APIs

### 3. Deployment Scripts

#### Linux/Mac: `frontend/deploy-config.sh`
```bash
./deploy-config.sh production
```
- Automatically configures API URL based on environment
- Supports development, staging, production
- Creates backup before modification

#### Windows: `frontend/deploy-config.ps1`
```powershell
.\deploy-config.ps1 -Environment production -ApiBaseUrl "https://api.afirgen.com"
```
- PowerShell script for Windows environments
- Same functionality as bash script
- Supports command-line parameters

### 4. Example Configurations

**Production: `frontend/config.production.example.js`**
- Template for production deployment
- Debug disabled
- HTTPS API URL

**Staging: `frontend/config.staging.example.js`**
- Template for staging environment
- Debug enabled for troubleshooting
- Staging API URL

### 5. Docker Support

**File: `frontend/Dockerfile`**
- Multi-stage build with configurable API URL
- Build arguments: `API_BASE_URL`, `ENVIRONMENT`, `ENABLE_DEBUG`
- Nginx configuration with security headers
- Health check endpoint
- Gzip compression and caching

**File: `frontend/docker-compose.yaml`**
- Standalone frontend deployment
- Environment variable support
- Network configuration
- Health checks

### 6. Main Docker Compose Integration

**File: `docker-compose.yaml`**
- Added frontend service
- Configurable via environment variables
- Depends on backend service
- Health checks enabled

### 7. Environment Variables

**File: `.env.example`**
Added frontend configuration:
```env
API_BASE_URL=http://localhost:8000
ENVIRONMENT=development
ENABLE_DEBUG=true
FRONTEND_PORT=80
```

### 8. Documentation

**File: `frontend/README.md`**
- Comprehensive configuration guide
- Deployment methods (Docker, AWS, manual)
- Security considerations
- Troubleshooting guide

**File: `FRONTEND-DEPLOYMENT-GUIDE.md`**
- Complete deployment guide for all environments
- AWS-specific instructions (S3, ECS, Elastic Beanstalk)
- Verification steps
- Monitoring and rollback procedures

**File: `frontend/test-config.html`**
- Interactive configuration test page
- API connectivity test
- CORS verification
- Configuration display

**Updated: `SETUP.md`**
- Added frontend configuration section
- Updated service list
- Added frontend access instructions

## Configuration Methods

### Method 1: Environment Variables (Recommended)
```bash
export API_BASE_URL="https://api.afirgen.com"
export ENVIRONMENT="production"
docker-compose up -d frontend
```

### Method 2: Deployment Scripts
```bash
# Linux/Mac
./frontend/deploy-config.sh production

# Windows
.\frontend\deploy-config.ps1 -Environment production
```

### Method 3: Docker Build Arguments
```bash
docker build \
  --build-arg API_BASE_URL=https://api.afirgen.com \
  --build-arg ENVIRONMENT=production \
  -t afirgen-frontend:latest \
  frontend/
```

### Method 4: Manual Edit
Edit `frontend/config.js` directly and change `API_BASE_URL` value.

## Verification

### Check Configuration
```bash
# View current config
cat frontend/config.js | grep API_BASE_URL

# Or in browser console
console.log(window.ENV);
```

### Test Connectivity
Open `http://localhost/test-config.html` and click "Test /health Endpoint"

Or use browser console:
```javascript
fetch(window.ENV.API_BASE_URL + '/health')
  .then(r => r.json())
  .then(console.log);
```

## Deployment Examples

### Local Development
```bash
docker-compose up -d
# Access at http://localhost
```

### Production with Custom API
```bash
API_BASE_URL=https://api.afirgen.com \
ENVIRONMENT=production \
ENABLE_DEBUG=false \
docker-compose up -d frontend
```

### AWS S3 + CloudFront
```bash
cd frontend
export API_BASE_URL="https://afirgen-alb-123456.us-east-1.elb.amazonaws.com"
./deploy-config.sh production
aws s3 sync . s3://afirgen-frontend-bucket/
```

### AWS ECS
```bash
docker build \
  --build-arg API_BASE_URL=https://api.afirgen.com \
  -t 123456789012.dkr.ecr.us-east-1.amazonaws.com/afirgen-frontend:latest \
  frontend/
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/afirgen-frontend:latest
```

## Security Considerations

### CORS Configuration
Backend must allow frontend domain:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "https://afirgen.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Content Security Policy
For production, restrict CSP to specific domain:
```html
<meta http-equiv="Content-Security-Policy" 
      content="connect-src 'self' https://api.afirgen.com">
```

### HTTPS Enforcement
- Always use HTTPS in production
- Use AWS Certificate Manager for SSL
- Configure ALB to redirect HTTP to HTTPS

## Files Created/Modified

### Created Files:
1. `frontend/README.md` - Configuration guide
2. `frontend/deploy-config.sh` - Linux/Mac deployment script
3. `frontend/deploy-config.ps1` - Windows deployment script
4. `frontend/config.production.example.js` - Production config template
5. `frontend/config.staging.example.js` - Staging config template
6. `frontend/Dockerfile` - Docker build configuration
7. `frontend/docker-compose.yaml` - Standalone deployment
8. `frontend/.env.example` - Environment variables template
9. `frontend/test-config.html` - Configuration test page
10. `FRONTEND-DEPLOYMENT-GUIDE.md` - Complete deployment guide
11. `FRONTEND-CONFIGURATION-SUMMARY.md` - This file

### Modified Files:
1. `frontend/config.js` - Enhanced with deployment instructions
2. `frontend/base.html` - Updated CSP to allow HTTPS
3. `docker-compose.yaml` - Added frontend service
4. `.env.example` - Added frontend variables
5. `SETUP.md` - Added frontend configuration section

## Testing

### Local Testing
1. Start services: `docker-compose up -d`
2. Open: http://localhost/test-config.html
3. Click "Test /health Endpoint"
4. Verify API connectivity

### Production Testing
1. Deploy with production API URL
2. Open test page: https://yourdomain.com/test-config.html
3. Verify configuration shows production URL
4. Test API connectivity
5. Check browser console for errors

## Troubleshooting

### Issue: API requests fail
**Check:**
1. API_BASE_URL is correct in config.js
2. Backend CORS includes frontend domain
3. Backend is running and accessible
4. Network connectivity

### Issue: Configuration not updated
**Solution:**
1. Verify config.js was modified
2. Clear browser cache (Ctrl+Shift+R)
3. Rebuild Docker image
4. Check deployment script ran successfully

### Issue: CSP blocks requests
**Solution:**
Update CSP in base.html to include API domain

## Next Steps

1. ✅ Frontend API URL is now configurable
2. ⏭️ Test deployment in staging environment
3. ⏭️ Configure production API URL
4. ⏭️ Set up AWS infrastructure (ALB, ECS, S3)
5. ⏭️ Configure CORS on backend for production domain
6. ⏭️ Set up CloudWatch monitoring
7. ⏭️ Implement CI/CD pipeline

## Acceptance Criteria Status

✅ Frontend API URL configurable via environment variables
✅ Deployment scripts for Linux/Mac and Windows
✅ Docker support with build arguments
✅ Example configurations for all environments
✅ Comprehensive documentation
✅ Test page for verification
✅ Security considerations documented
✅ Integration with main docker-compose

## References

- [Frontend README](frontend/README.md)
- [Deployment Guide](FRONTEND-DEPLOYMENT-GUIDE.md)
- [Setup Guide](SETUP.md)
- [Requirements](.kiro/specs/afirgen-aws-optimization/requirements.md)
