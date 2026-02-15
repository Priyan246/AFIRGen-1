# AFIRGen Frontend Configuration

## Overview
The AFIRGen frontend is a static HTML/CSS/JS application that can be deployed to any web server or CDN. The API endpoint is configurable via the `config.js` file.

## Configuration

### API Base URL
The frontend connects to the backend API using the URL specified in `config.js`:

```javascript
window.ENV = {
    API_BASE_URL: 'http://localhost:8000',  // Change this for production
    ENVIRONMENT: 'development',
    ENABLE_DEBUG: true,
};
```

## Deployment Methods

### Method 1: Environment Variable Substitution (Recommended for Docker/AWS)

Create a deployment script that replaces the API URL at build/deploy time:

```bash
#!/bin/bash
# deploy-frontend.sh

API_URL="${API_BASE_URL:-http://localhost:8000}"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Replace API_BASE_URL in config.js
sed -i "s|API_BASE_URL: '.*'|API_BASE_URL: '${API_URL}'|g" config.js
sed -i "s|ENVIRONMENT: '.*'|ENVIRONMENT: '${ENVIRONMENT}'|g" config.js
sed -i "s|ENABLE_DEBUG: .*,|ENABLE_DEBUG: false,|g" config.js

echo "Frontend configured for ${ENVIRONMENT} with API URL: ${API_URL}"
```

Usage:
```bash
export API_BASE_URL="https://api.afirgen.com"
export ENVIRONMENT="production"
./deploy-frontend.sh
```

### Method 2: Docker Volume Mount

Mount a custom `config.js` file when running the container:

```yaml
# docker-compose.yml
services:
  frontend:
    image: nginx:alpine
    volumes:
      - ./frontend:/usr/share/nginx/html
      - ./config.production.js:/usr/share/nginx/html/config.js:ro
    ports:
      - "80:80"
```

Create `config.production.js`:
```javascript
window.ENV = {
    API_BASE_URL: 'https://api.afirgen.com',
    ENVIRONMENT: 'production',
    ENABLE_DEBUG: false,
};
```

### Method 3: Runtime Override (Advanced)

Inject configuration at runtime using a separate script loaded before `config.js`:

```html
<!-- In base.html, before config.js -->
<script>
    window.ENV_OVERRIDE = {
        API_BASE_URL: window.location.origin.replace('www', 'api'),
    };
</script>
<script src="config.js"></script>
```

## AWS Deployment

### S3 + CloudFront

1. **Build and configure:**
```bash
export API_BASE_URL="https://afirgen-alb-123456.us-east-1.elb.amazonaws.com"
sed -i "s|http://localhost:8000|${API_BASE_URL}|g" config.js
```

2. **Upload to S3:**
```bash
aws s3 sync . s3://afirgen-frontend-bucket/ --exclude "*.md" --exclude ".git/*"
```

3. **Invalidate CloudFront cache:**
```bash
aws cloudfront create-invalidation --distribution-id E1234567890ABC --paths "/*"
```

### ECS with Nginx

Create a Dockerfile that configures the frontend at build time:

```dockerfile
FROM nginx:alpine

# Copy frontend files
COPY . /usr/share/nginx/html

# Configure API URL from build arg
ARG API_BASE_URL=http://localhost:8000
RUN sed -i "s|http://localhost:8000|${API_BASE_URL}|g" /usr/share/nginx/html/config.js

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build with API URL:
```bash
docker build --build-arg API_BASE_URL=https://api.afirgen.com -t afirgen-frontend .
```

## Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `API_BASE_URL` | Backend API endpoint | `http://localhost:8000` | `https://api.afirgen.com` |
| `ENVIRONMENT` | Environment name | `development` | `production`, `staging` |
| `ENABLE_DEBUG` | Enable debug logging | `true` | `false` |

## Verification

After deployment, verify the configuration:

1. Open browser developer console
2. Check `window.ENV`:
```javascript
console.log(window.ENV);
// Should show your production API URL
```

3. Test API connectivity:
```javascript
fetch(window.ENV.API_BASE_URL + '/health')
    .then(r => r.json())
    .then(console.log);
```

## Security Considerations

### Content Security Policy (CSP)

The `base.html` includes a CSP header that allows connections to:
- `'self'` (same origin)
- `http://localhost:8000` (development)
- `https://*` (any HTTPS endpoint for production)

For stricter security in production, update the CSP to only allow your specific API domain:

```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline'; 
               style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; 
               font-src 'self' https://fonts.gstatic.com; 
               connect-src 'self' https://api.afirgen.com">
```

### CORS Configuration

Ensure your backend CORS settings allow requests from your frontend domain:

```python
# In backend (agentv5.py)
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

## Troubleshooting

### Issue: API requests fail with CORS error
**Solution:** Check that backend CORS settings include your frontend domain

### Issue: API requests go to localhost in production
**Solution:** Verify `config.js` was properly updated during deployment

### Issue: CSP blocks API requests
**Solution:** Update CSP meta tag to include your API domain

### Issue: Changes not reflected after deployment
**Solution:** Clear browser cache or add cache-busting query parameter to config.js
