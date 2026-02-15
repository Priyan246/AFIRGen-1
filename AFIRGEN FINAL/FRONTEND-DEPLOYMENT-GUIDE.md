# AFIRGen Frontend Deployment Guide

## Overview
This guide explains how to configure and deploy the AFIRGen frontend with a configurable API endpoint for different environments.

## Quick Start

### Local Development
```bash
# No configuration needed - uses default localhost:8000
cd "AFIRGEN FINAL"
docker-compose up -d frontend
```

Access at: http://localhost

### Production Deployment
```bash
# Set API URL and deploy
export API_BASE_URL="https://api.afirgen.com"
export ENVIRONMENT="production"
export ENABLE_DEBUG="false"
docker-compose up -d frontend
```

## Configuration Methods

### Method 1: Environment Variables (Recommended)

Create a `.env` file in the project root:

```bash
# Copy example file
cp .env.example .env

# Edit .env file
nano .env
```

Update these values:
```env
API_BASE_URL=https://api.afirgen.com
ENVIRONMENT=production
ENABLE_DEBUG=false
FRONTEND_PORT=80
```

Deploy:
```bash
docker-compose up -d frontend
```

### Method 2: Deployment Scripts

#### Linux/Mac:
```bash
cd "AFIRGEN FINAL/frontend"
chmod +x deploy-config.sh
./deploy-config.sh production
```

#### Windows PowerShell:
```powershell
cd "AFIRGEN FINAL\frontend"
.\deploy-config.ps1 -Environment production -ApiBaseUrl "https://api.afirgen.com"
```

### Method 3: Manual Configuration

Edit `frontend/config.js` directly:

```javascript
window.ENV = {
    API_BASE_URL: 'https://api.afirgen.com',
    ENVIRONMENT: 'production',
    ENABLE_DEBUG: false,
};
```

## Docker Deployment

### Build with Custom API URL

```bash
cd "AFIRGEN FINAL/frontend"
docker build \
  --build-arg API_BASE_URL=https://api.afirgen.com \
  --build-arg ENVIRONMENT=production \
  --build-arg ENABLE_DEBUG=false \
  -t afirgen-frontend:latest .
```

### Run Container

```bash
docker run -d \
  --name afirgen-frontend \
  -p 80:80 \
  --restart unless-stopped \
  afirgen-frontend:latest
```

### Docker Compose (Standalone)

```bash
cd "AFIRGEN FINAL/frontend"
API_BASE_URL=https://api.afirgen.com docker-compose up -d
```

## AWS Deployment

### Option 1: S3 + CloudFront (Static Hosting)

1. **Configure frontend:**
```bash
cd "AFIRGEN FINAL/frontend"
export API_BASE_URL="https://afirgen-alb-123456.us-east-1.elb.amazonaws.com"
./deploy-config.sh production
```

2. **Upload to S3:**
```bash
aws s3 sync . s3://afirgen-frontend-bucket/ \
  --exclude "*.md" \
  --exclude ".git/*" \
  --exclude "Dockerfile" \
  --exclude "docker-compose.yaml" \
  --exclude "*.sh" \
  --exclude "*.ps1"
```

3. **Configure S3 bucket for static hosting:**
```bash
aws s3 website s3://afirgen-frontend-bucket/ \
  --index-document index.html \
  --error-document index.html
```

4. **Create CloudFront distribution:**
```bash
aws cloudfront create-distribution \
  --origin-domain-name afirgen-frontend-bucket.s3.amazonaws.com \
  --default-root-object index.html
```

5. **Invalidate cache after updates:**
```bash
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/*"
```

### Option 2: ECS Fargate

1. **Build and push to ECR:**
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build with production config
docker build \
  --build-arg API_BASE_URL=https://api.afirgen.com \
  --build-arg ENVIRONMENT=production \
  --build-arg ENABLE_DEBUG=false \
  -t afirgen-frontend:latest \
  "AFIRGEN FINAL/frontend"

# Tag and push
docker tag afirgen-frontend:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/afirgen-frontend:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/afirgen-frontend:latest
```

2. **Create ECS task definition:**
```json
{
  "family": "afirgen-frontend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "frontend",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/afirgen-frontend:latest",
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "wget --quiet --tries=1 --spider http://localhost/ || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 10
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/afirgen-frontend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

3. **Create ECS service:**
```bash
aws ecs create-service \
  --cluster afirgen-cluster \
  --service-name afirgen-frontend \
  --task-definition afirgen-frontend \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/afirgen-frontend/1234567890,containerName=frontend,containerPort=80"
```

### Option 3: Elastic Beanstalk

1. **Create Dockerrun.aws.json:**
```json
{
  "AWSEBDockerrunVersion": "1",
  "Image": {
    "Name": "123456789012.dkr.ecr.us-east-1.amazonaws.com/afirgen-frontend:latest",
    "Update": "true"
  },
  "Ports": [
    {
      "ContainerPort": 80,
      "HostPort": 80
    }
  ]
}
```

2. **Deploy:**
```bash
eb init -p docker afirgen-frontend
eb create afirgen-frontend-env
eb deploy
```

## Verification

### Check Configuration
```bash
# View current config
cat "AFIRGEN FINAL/frontend/config.js" | grep API_BASE_URL

# Or in browser console
console.log(window.ENV);
```

### Test API Connectivity
```bash
# From command line
curl http://localhost/

# In browser console
fetch(window.ENV.API_BASE_URL + '/health')
  .then(r => r.json())
  .then(console.log);
```

### Health Check
```bash
# Docker container
docker exec afirgen-frontend wget --quiet --tries=1 --spider http://localhost/

# Direct
curl -f http://localhost/ || echo "Health check failed"
```

## Environment-Specific Configurations

### Development
```env
API_BASE_URL=http://localhost:8000
ENVIRONMENT=development
ENABLE_DEBUG=true
FRONTEND_PORT=80
```

### Staging
```env
API_BASE_URL=https://staging-api.afirgen.com
ENVIRONMENT=staging
ENABLE_DEBUG=true
FRONTEND_PORT=80
```

### Production
```env
API_BASE_URL=https://api.afirgen.com
ENVIRONMENT=production
ENABLE_DEBUG=false
FRONTEND_PORT=80
```

## Security Considerations

### CORS Configuration
Ensure backend CORS settings match your frontend domain:

```python
# In main backend/agentv5.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "https://afirgen.com",
        "https://www.afirgen.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Content Security Policy
For production, update CSP in `base.html` to restrict to your domain:

```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline'; 
               style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; 
               font-src 'self' https://fonts.gstatic.com; 
               connect-src 'self' https://api.afirgen.com">
```

### HTTPS Enforcement
Always use HTTPS in production:
- Use AWS Certificate Manager (ACM) for SSL certificates
- Configure ALB/CloudFront to redirect HTTP to HTTPS
- Set `ENFORCE_HTTPS=true` in backend environment

## Troubleshooting

### Issue: API requests fail with CORS error
**Solution:** 
1. Check backend CORS configuration includes frontend domain
2. Verify API_BASE_URL is correct in config.js
3. Check browser console for exact error

### Issue: Frontend shows localhost API in production
**Solution:**
1. Verify config.js was updated: `cat frontend/config.js | grep API_BASE_URL`
2. Rebuild Docker image with correct build args
3. Clear browser cache

### Issue: CSP blocks API requests
**Solution:**
Update CSP meta tag in base.html to include your API domain

### Issue: Changes not reflected after deployment
**Solution:**
1. Clear browser cache (Ctrl+Shift+R)
2. Invalidate CloudFront cache if using CloudFront
3. Check Docker image was rebuilt with new config

### Issue: Health check fails
**Solution:**
1. Check nginx is running: `docker exec afirgen-frontend ps aux | grep nginx`
2. Check logs: `docker logs afirgen-frontend`
3. Verify port 80 is accessible

## Monitoring

### CloudWatch Logs
```bash
# View logs
aws logs tail /ecs/afirgen-frontend --follow

# Filter errors
aws logs filter-log-events \
  --log-group-name /ecs/afirgen-frontend \
  --filter-pattern "ERROR"
```

### Container Logs
```bash
# Docker logs
docker logs -f afirgen-frontend

# Last 100 lines
docker logs --tail 100 afirgen-frontend
```

### Metrics
Monitor these metrics in CloudWatch:
- Request count
- Error rate (4xx, 5xx)
- Response time
- CPU/Memory utilization

## Rollback

### Docker
```bash
# Stop current version
docker stop afirgen-frontend
docker rm afirgen-frontend

# Run previous version
docker run -d --name afirgen-frontend -p 80:80 afirgen-frontend:previous
```

### ECS
```bash
# Update service to previous task definition
aws ecs update-service \
  --cluster afirgen-cluster \
  --service afirgen-frontend \
  --task-definition afirgen-frontend:previous-revision
```

## Best Practices

1. **Always use environment variables** for configuration
2. **Never commit .env files** with production credentials
3. **Use HTTPS in production** with valid SSL certificates
4. **Implement proper CORS** - never use `*` in production
5. **Enable CloudWatch logging** for troubleshooting
6. **Set up health checks** for automatic recovery
7. **Use CDN (CloudFront)** for better performance
8. **Implement cache invalidation** strategy
9. **Monitor error rates** and set up alerts
10. **Test configuration** in staging before production

## Additional Resources

- [Frontend README](frontend/README.md) - Detailed configuration guide
- [Docker Documentation](https://docs.docker.com/)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
