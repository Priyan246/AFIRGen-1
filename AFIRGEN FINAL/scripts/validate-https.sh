#!/bin/bash
# HTTPS/TLS Validation Script for AFIRGen
# Validates all aspects of HTTPS/TLS configuration

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASS=0
FAIL=0
WARN=0

echo -e "${BLUE}=========================================="
echo "HTTPS/TLS Validation Script"
echo -e "==========================================${NC}"
echo ""

# Function to check and print result
check() {
    local name="$1"
    local command="$2"
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗${NC} $name"
        ((FAIL++))
        return 1
    fi
}

# Function to print warning
warn() {
    local name="$1"
    local message="$2"
    
    echo -e "${YELLOW}⚠${NC} $name"
    if [ -n "$message" ]; then
        echo "  $message"
    fi
    ((WARN++))
}

# Certificate Checks
echo -e "${BLUE}Certificate Checks:${NC}"
check "Certificate file exists" "test -f nginx/ssl/cert.pem"
check "Private key file exists" "test -f nginx/ssl/key.pem"

if [ -f nginx/ssl/key.pem ]; then
    PERMS=$(stat -c "%a" nginx/ssl/key.pem 2>/dev/null || stat -f "%A" nginx/ssl/key.pem 2>/dev/null)
    if [ "$PERMS" = "600" ]; then
        echo -e "${GREEN}✓${NC} Private key has secure permissions (600)"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠${NC} Private key permissions are $PERMS (should be 600)"
        ((WARN++))
    fi
fi

if command -v openssl &> /dev/null && [ -f nginx/ssl/cert.pem ]; then
    if openssl x509 -in nginx/ssl/cert.pem -noout -checkend 0 > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Certificate is valid (not expired)"
        ((PASS++))
        
        # Show expiration date
        EXPIRY=$(openssl x509 -in nginx/ssl/cert.pem -noout -enddate | cut -d= -f2)
        echo "  Expires: $EXPIRY"
    else
        echo -e "${RED}✗${NC} Certificate is expired"
        ((FAIL++))
    fi
else
    warn "OpenSSL not found" "Cannot validate certificate expiration"
fi

echo ""

# Docker Service Checks
echo -e "${BLUE}Docker Service Checks:${NC}"
if command -v docker-compose &> /dev/null; then
    SERVICES=("nginx" "fir_pipeline" "gguf_model_server" "asr_ocr_model_server")
    
    for service in "${SERVICES[@]}"; do
        if docker-compose ps "$service" 2>/dev/null | grep -q "Up"; then
            echo -e "${GREEN}✓${NC} $service container is running"
            ((PASS++))
        else
            echo -e "${RED}✗${NC} $service container is not running"
            ((FAIL++))
        fi
    done
else
    warn "Docker Compose not found" "Cannot check service status"
fi

echo ""

# HTTPS Connectivity Checks
echo -e "${BLUE}HTTPS Connectivity Checks:${NC}"
if command -v curl &> /dev/null; then
    check "HTTPS endpoint accessible" "curl -k -f -s https://localhost/health > /dev/null"
    
    # Check HTTP redirect
    if curl -I -s http://localhost 2>/dev/null | grep -q "301\|302\|307\|308"; then
        echo -e "${GREEN}✓${NC} HTTP redirects to HTTPS"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} HTTP does not redirect to HTTPS"
        ((FAIL++))
    fi
else
    warn "curl not found" "Cannot test HTTPS connectivity"
fi

echo ""

# Security Header Checks
echo -e "${BLUE}Security Header Checks:${NC}"
if command -v curl &> /dev/null; then
    HEADERS=$(curl -I -k -s https://localhost 2>/dev/null)
    
    check "HSTS header present" "echo '$HEADERS' | grep -qi 'strict-transport-security'"
    check "X-Frame-Options present" "echo '$HEADERS' | grep -qi 'x-frame-options'"
    check "X-Content-Type-Options present" "echo '$HEADERS' | grep -qi 'x-content-type-options'"
    check "X-XSS-Protection present" "echo '$HEADERS' | grep -qi 'x-xss-protection'"
    check "Content-Security-Policy present" "echo '$HEADERS' | grep -qi 'content-security-policy'"
    check "Referrer-Policy present" "echo '$HEADERS' | grep -qi 'referrer-policy'"
fi

echo ""

# TLS Configuration Checks
echo -e "${BLUE}TLS Configuration Checks:${NC}"
if command -v openssl &> /dev/null; then
    # Test TLS 1.2
    if echo | openssl s_client -connect localhost:443 -tls1_2 2>/dev/null | grep -q "Protocol.*TLSv1.2"; then
        echo -e "${GREEN}✓${NC} TLS 1.2 supported"
        ((PASS++))
    else
        warn "TLS 1.2 test" "Could not verify TLS 1.2 support"
    fi
    
    # Test TLS 1.3
    if echo | openssl s_client -connect localhost:443 -tls1_3 2>/dev/null | grep -q "Protocol.*TLSv1.3"; then
        echo -e "${GREEN}✓${NC} TLS 1.3 supported"
        ((PASS++))
    else
        warn "TLS 1.3 test" "TLS 1.3 may not be supported (this is optional)"
    fi
    
    # Check cipher strength
    if echo | openssl s_client -connect localhost:443 -cipher HIGH 2>/dev/null | grep -q "Cipher"; then
        echo -e "${GREEN}✓${NC} Strong cipher suites available"
        ((PASS++))
    else
        warn "Cipher strength test" "Could not verify cipher strength"
    fi
else
    warn "OpenSSL not found" "Cannot test TLS configuration"
fi

echo ""

# API Endpoint Checks
echo -e "${BLUE}API Endpoint Checks:${NC}"
if command -v curl &> /dev/null; then
    check "Health endpoint accessible" "curl -k -f -s https://localhost/health > /dev/null"
    check "Metrics endpoint accessible" "curl -k -f -s https://localhost/metrics > /dev/null"
    check "Reliability endpoint accessible" "curl -k -f -s https://localhost/reliability > /dev/null"
fi

echo ""

# Access Control Checks
echo -e "${BLUE}Access Control Checks:${NC}"
if command -v curl &> /dev/null; then
    # Check that internal ports are not accessible
    INTERNAL_PORTS=(8000 8001 8002)
    
    for port in "${INTERNAL_PORTS[@]}"; do
        if ! curl -f -s --connect-timeout 2 http://localhost:$port/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Port $port blocked from external access"
            ((PASS++))
        else
            echo -e "${RED}✗${NC} Port $port is accessible (should be blocked)"
            ((FAIL++))
        fi
    done
fi

echo ""

# Performance Checks
echo -e "${BLUE}Performance Checks:${NC}"
if command -v curl &> /dev/null; then
    # Test response time
    START=$(date +%s%N)
    curl -k -f -s https://localhost/health > /dev/null 2>&1
    END=$(date +%s%N)
    RESPONSE_TIME=$(( (END - START) / 1000000 ))
    
    if [ $RESPONSE_TIME -lt 200 ]; then
        echo -e "${GREEN}✓${NC} Response time < 200ms (${RESPONSE_TIME}ms)"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠${NC} Response time is ${RESPONSE_TIME}ms (target: <200ms)"
        ((WARN++))
    fi
fi

echo ""

# Summary
echo -e "${BLUE}=========================================="
echo "Test Summary"
echo -e "==========================================${NC}"
TOTAL=$((PASS + FAIL))
if [ $TOTAL -gt 0 ]; then
    PASS_RATE=$((PASS * 100 / TOTAL))
else
    PASS_RATE=0
fi

echo "Total tests: $TOTAL"
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo -e "${YELLOW}Warnings: $WARN${NC}"
echo "Pass rate: ${PASS_RATE}%"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review the output above.${NC}"
    echo ""
    exit 1
fi
