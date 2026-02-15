#!/bin/bash
# Frontend Configuration Deployment Script
# Usage: ./deploy-config.sh [environment]
# Example: ./deploy-config.sh production

set -e

ENVIRONMENT="${1:-development}"
CONFIG_FILE="config.js"

echo "Configuring frontend for environment: ${ENVIRONMENT}"

case "${ENVIRONMENT}" in
    production)
        API_URL="${API_BASE_URL:-https://api.afirgen.com}"
        DEBUG="false"
        ;;
    staging)
        API_URL="${API_BASE_URL:-https://staging-api.afirgen.com}"
        DEBUG="false"
        ;;
    development)
        API_URL="${API_BASE_URL:-http://localhost:8000}"
        DEBUG="true"
        ;;
    *)
        echo "Unknown environment: ${ENVIRONMENT}"
        echo "Valid options: production, staging, development"
        exit 1
        ;;
esac

echo "API Base URL: ${API_URL}"
echo "Debug Mode: ${DEBUG}"

# Backup original config
if [ ! -f "${CONFIG_FILE}.backup" ]; then
    cp "${CONFIG_FILE}" "${CONFIG_FILE}.backup"
    echo "Created backup: ${CONFIG_FILE}.backup"
fi

# Update config.js
sed -i.tmp "s|API_BASE_URL: '[^']*'|API_BASE_URL: '${API_URL}'|g" "${CONFIG_FILE}"
sed -i.tmp "s|ENVIRONMENT: '[^']*'|ENVIRONMENT: '${ENVIRONMENT}'|g" "${CONFIG_FILE}"
sed -i.tmp "s|ENABLE_DEBUG: [^,]*,|ENABLE_DEBUG: ${DEBUG},|g" "${CONFIG_FILE}"

# Remove temporary file
rm -f "${CONFIG_FILE}.tmp"

echo "✓ Frontend configuration updated successfully"
echo ""
echo "Verify configuration:"
echo "  grep API_BASE_URL ${CONFIG_FILE}"
