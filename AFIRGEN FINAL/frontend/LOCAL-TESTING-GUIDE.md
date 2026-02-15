# Frontend Local Testing Guide

## Quick Start (Easiest)

### Method 1: Python HTTP Server (No Docker Required)

```bash
# Navigate to frontend directory
cd "AFIRGEN FINAL/frontend"

# Start simple HTTP server
python -m http.server 8080
```

**Open in browser**: `http://localhost:8080`

**Test configuration**: `http://localhost:8080/test-config.html`

---

## Method 2: Docker (Recommended)

### Build and Run

```bash
# Navigate to frontend directory
cd "AFIRGEN FINAL/frontend"

# Build the image
docker build -t afirgen-frontend .

# Run the container
docker run -p 8080:80 afirgen-frontend
```

**Open in browser**: `http://localhost:8080`

### With Custom API URL

```bash
# Build with custom API URL
docker build --build-arg API_BASE_URL=http://localhost:8000 -t afirgen-frontend .

# Run
docker run -p 8080:80 afirgen-frontend
```

---

## Method 3: Docker Compose (Full Stack)

### Frontend Only

```bash
cd "AFIRGEN FINAL/frontend"
docker-compose up -d
```

**Open in browser**: `http://localhost`

### With Custom Configuration

```bash
# Set environment variables
export API_BASE_URL="http://localhost:8000"
export ENVIRONMENT="development"
export ENABLE_DEBUG="true"

# Start
docker-compose up -d
```

### Stop

```bash
docker-compose down
```

---

## Method 4: Full Application Stack

To test the frontend with the backend running:

```bash
# Navigate to main directory
cd "AFIRGEN FINAL"

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f frontend
```

**Frontend**: `http://localhost` (via Nginx)  
**Backend API**: `http://localhost:8000`  
**Direct Frontend**: `http://localhost:3000` (if configured)

---

## Testing the Configuration

### 1. Open Test Page

Navigate to: `http://localhost:8080/test-config.html`

This page shows:
- ✅ Current API_BASE_URL
- ✅ Environment settings
- ✅ API connectivity test
- ✅ Configuration verification

### 2. Check Browser Console

Open browser DevTools (F12) and run:

```javascript
// Check configuration
console.log(window.ENV);

// Expected output:
// {
//   API_BASE_URL: "http://localhost:8000",
//   API_KEY: "your-api-key-here",
//   ENVIRONMENT: "development",
//   ENABLE_DEBUG: true
// }
```

### 3. Test API Connectivity

```javascript
// Test health endpoint
fetch(window.ENV.API_BASE_URL + '/health')
    .then(r => r.json())
    .then(data => console.log('API Health:', data))
    .catch(err => console.error('API Error:', err));
```

---

## Troubleshooting

### Issue: "Cannot GET /"

**Solution**: Make sure you're accessing the correct URL:
- Python server: `http://localhost:8080`
- Docker: `http://localhost:8080` (or port you specified)
- Docker Compose: `http://localhost`

### Issue: API requests fail with CORS error

**Solution**: 
1. Make sure backend is running
2. Check CORS configuration in backend allows your frontend origin
3. Verify API_BASE_URL in config.js matches your backend URL

```bash
# Check backend CORS settings
cd "AFIRGEN FINAL/main backend"
grep -A 5 "CORS_ORIGINS" agentv5.py
```

### Issue: "Connection refused" when testing API

**Solution**: Start the backend first:

```bash
cd "AFIRGEN FINAL"
docker-compose up -d fir_pipeline
```

### Issue: Changes not reflected

**Solution**: Clear browser cache or hard refresh:
- Chrome/Edge: `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
- Firefox: `Ctrl + F5` (Windows) or `Cmd + Shift + R` (Mac)

### Issue: Docker build fails

**Solution**: Make sure Docker Desktop is running:

```bash
# Check Docker status
docker --version
docker ps

# If not running, start Docker Desktop
```

---

## Configuration Options

### Change API URL

**Option 1: Edit config.js directly**
```javascript
// In config.js
window.ENV = {
    API_BASE_URL: 'http://localhost:8000',  // Change this
    // ...
};
```

**Option 2: Use environment variable**
```bash
export API_BASE_URL="http://localhost:8000"
./deploy-config.sh
```

**Option 3: Docker build argument**
```bash
docker build --build-arg API_BASE_URL=http://localhost:8000 -t frontend .
```

### Enable Debug Mode

Edit `config.js`:
```javascript
window.ENV = {
    // ...
    ENABLE_DEBUG: true,  // Enable debug logging
};
```

---

## Viewing Logs

### Python HTTP Server
Logs appear in the terminal where you ran the command.

### Docker
```bash
# View logs
docker logs afirgen-frontend

# Follow logs
docker logs -f afirgen-frontend
```

### Docker Compose
```bash
# View all logs
docker-compose logs

# View frontend logs only
docker-compose logs frontend

# Follow logs
docker-compose logs -f frontend
```

---

## Stopping the Frontend

### Python HTTP Server
Press `Ctrl + C` in the terminal

### Docker
```bash
docker stop afirgen-frontend
docker rm afirgen-frontend
```

### Docker Compose
```bash
docker-compose down
```

---

## Next Steps

Once you've verified the frontend works locally:

1. **Test with Backend**: Start the full stack with `docker-compose up -d`
2. **Test API Integration**: Use the test page to verify API connectivity
3. **Test Features**: Try creating a FIR, uploading files, etc.
4. **Check Logs**: Monitor logs for any errors
5. **Prepare for Deployment**: Configure production API URL

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `python -m http.server 8080` | Start simple HTTP server |
| `docker build -t afirgen-frontend .` | Build Docker image |
| `docker run -p 8080:80 afirgen-frontend` | Run Docker container |
| `docker-compose up -d` | Start with Docker Compose |
| `docker-compose down` | Stop Docker Compose |
| `docker logs -f afirgen-frontend` | View Docker logs |

---

**Need Help?** Check the main README.md for more detailed information.
