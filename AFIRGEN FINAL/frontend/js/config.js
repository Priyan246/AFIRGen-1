// Frontend Configuration
// This file can be generated dynamically during deployment with environment-specific values
//
// DEPLOYMENT INSTRUCTIONS:
// 1. For Docker: Mount this file as a volume and set API_BASE_URL before container starts
// 2. For AWS: Use a build script to replace API_BASE_URL with CloudFront/ALB URL
// 3. For local dev: Keep default localhost:8000
//
// Example deployment script:
//   sed -i "s|http://localhost:8000|https://api.yourdomain.com|g" config.js

window.ENV = {
  // API Base URL - MUST be configured for production deployment
  // Examples:
  // - Development: 'http://localhost:8000'
  // - Production: 'https://api.yourdomain.com'
  // - AWS ALB: 'https://afirgen-alb-123456.us-east-1.elb.amazonaws.com'
  API_BASE_URL: 'http://localhost:8000',

  // API Key for authentication - MUST be configured
  // Generate a secure key using: python -c "import secrets; print(secrets.token_urlsafe(32))"
  // This should match the API_KEY environment variable in the backend
  API_KEY: 'your-api-key-here',

  // Environment name (development, staging, production)
  ENVIRONMENT: 'development',

  // Feature flags
  ENABLE_DEBUG: true
};

// Override with environment-specific config if available
// This allows runtime configuration without modifying this file
if (typeof window.ENV_OVERRIDE !== 'undefined') {
  window.ENV = { ...window.ENV, ...window.ENV_OVERRIDE };
}
