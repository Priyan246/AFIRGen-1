// Production Configuration Example
// Copy this file to config.js for production deployment
// Or use deploy-config.sh to automatically configure

window.ENV = {
    // Production API URL - Update this to your actual production API endpoint
    // Examples:
    // - AWS ALB: 'https://afirgen-alb-123456.us-east-1.elb.amazonaws.com'
    // - CloudFront: 'https://api.afirgen.com'
    // - Custom domain: 'https://api.yourdomain.com'
    API_BASE_URL: 'https://api.afirgen.com',
    
    // Environment name
    ENVIRONMENT: 'production',
    
    // Disable debug logging in production
    ENABLE_DEBUG: false,
};

// Override with environment-specific config if available
if (typeof window.ENV_OVERRIDE !== 'undefined') {
    window.ENV = { ...window.ENV, ...window.ENV_OVERRIDE };
}
