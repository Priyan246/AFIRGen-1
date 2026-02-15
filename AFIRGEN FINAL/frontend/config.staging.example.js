// Staging Configuration Example
// Copy this file to config.js for staging deployment

window.ENV = {
    // Staging API URL
    API_BASE_URL: 'https://staging-api.afirgen.com',
    
    // Environment name
    ENVIRONMENT: 'staging',
    
    // Enable debug logging in staging for troubleshooting
    ENABLE_DEBUG: true,
};

// Override with environment-specific config if available
if (typeof window.ENV_OVERRIDE !== 'undefined') {
    window.ENV = { ...window.ENV, ...window.ENV_OVERRIDE };
}
