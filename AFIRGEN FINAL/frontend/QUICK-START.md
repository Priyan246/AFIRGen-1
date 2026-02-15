# Frontend Configuration - Quick Start

## 🚀 Quick Deploy

### Development (Default)
```bash
docker-compose up -d frontend
```
Access: http://localhost

### Production
```bash
# Set your API URL
export API_BASE_URL="https://api.afirgen.com"
export ENVIRONMENT="production"
export ENABLE_DEBUG="false"

# Deploy
docker-compose up -d --build frontend
```

## 🔧 Configuration Methods

### 1. Environment Variables (Easiest)
```bash
# Edit .env file
API_BASE_URL=https://api.afirgen.com
ENVIRONMENT=production
ENABLE_DEBUG=false

# Deploy
docker-compose up -d frontend
```

### 2. Deployment Script
```bash
# Linux/Mac
./deploy-config.sh production

# Windows
.\deploy-config.ps1 -Environment production
```

### 3. Manual Edit
Edit `config.js`:
```javascript
API_BASE_URL: 'https://api.afirgen.com',
```

## ✅ Verify Configuration

### Browser Console
```javascript
console.log(window.ENV);
```

### Test Page
Open: http://localhost/test-config.html

### API Test
```javascript
fetch(window.ENV.API_BASE_URL + '/health')
  .then(r => r.json())
  .then(console.log);
```

## 🐛 Troubleshooting

### API requests fail?
1. Check API_BASE_URL in config.js
2. Verify backend is running
3. Check CORS configuration

### Changes not showing?
1. Clear browser cache (Ctrl+Shift+R)
2. Rebuild Docker: `docker-compose up -d --build frontend`

### CSP blocking requests?
Update CSP in base.html to include your API domain

## 📚 Full Documentation
- [Complete Guide](README.md)
- [Deployment Guide](../FRONTEND-DEPLOYMENT-GUIDE.md)
- [Setup Guide](../SETUP.md)
