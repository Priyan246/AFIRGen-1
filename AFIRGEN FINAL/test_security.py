#!/usr/bin/env python3
"""
Security Testing Script for AFIRGen
Tests various security measures implemented in the system
"""

import requests
import time
import sys
from typing import Dict, List, Tuple

# Configuration
BASE_URL = "http://localhost:8000"
COLORS = {
    "GREEN": "\033[92m",
    "RED": "\033[91m",
    "YELLOW": "\033[93m",
    "BLUE": "\033[94m",
    "RESET": "\033[0m"
}

def print_test(name: str, passed: bool, message: str = ""):
    """Print test result with color"""
    status = f"{COLORS['GREEN']}✓ PASS{COLORS['RESET']}" if passed else f"{COLORS['RED']}✗ FAIL{COLORS['RESET']}"
    print(f"{status} - {name}")
    if message:
        print(f"  {message}")

def test_cors_protection() -> bool:
    """Test CORS configuration"""
    print(f"\n{COLORS['BLUE']}Testing CORS Protection...{COLORS['RESET']}")
    
    # Test with malicious origin
    try:
        response = requests.options(
            f"{BASE_URL}/process",
            headers={
                "Origin": "https://malicious.com",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        # Should not have CORS headers for unauthorized origin
        has_cors = "Access-Control-Allow-Origin" in response.headers
        passed = not has_cors or response.headers.get("Access-Control-Allow-Origin") != "https://malicious.com"
        
        print_test("CORS blocks unauthorized origins", passed)
        return passed
    except Exception as e:
        print_test("CORS blocks unauthorized origins", False, f"Error: {e}")
        return False

def test_rate_limiting() -> bool:
    """Test rate limiting"""
    print(f"\n{COLORS['BLUE']}Testing Rate Limiting...{COLORS['RESET']}")
    
    try:
        # Make requests until rate limit is hit
        success_count = 0
        rate_limited = False
        
        for i in range(105):  # Try more than the limit
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 429:
                rate_limited = True
                break
            elif response.status_code == 200:
                success_count += 1
        
        print_test("Rate limiting active", rate_limited, f"Succeeded {success_count} times before rate limit")
        return rate_limited
    except Exception as e:
        print_test("Rate limiting active", False, f"Error: {e}")
        return False

def test_input_validation() -> bool:
    """Test input validation and sanitization"""
    print(f"\n{COLORS['BLUE']}Testing Input Validation...{COLORS['RESET']}")
    
    all_passed = True
    
    # Test XSS in text input
    try:
        response = requests.post(
            f"{BASE_URL}/process",
            data={"text": "<script>alert('xss')</script>"}
        )
        # Should either reject or sanitize
        passed = response.status_code in [400, 413] or "<script>" not in response.text
        print_test("XSS prevention in text input", passed)
        all_passed = all_passed and passed
    except Exception as e:
        print_test("XSS prevention in text input", False, f"Error: {e}")
        all_passed = False
    
    # Test invalid FIR number format
    try:
        response = requests.get(f"{BASE_URL}/fir/invalid-fir-number")
        passed = response.status_code == 400
        print_test("FIR number format validation", passed)
        all_passed = all_passed and passed
    except Exception as e:
        print_test("FIR number format validation", False, f"Error: {e}")
        all_passed = False
    
    # Test SQL injection attempt
    try:
        response = requests.get(f"{BASE_URL}/fir/FIR-test' OR '1'='1")
        passed = response.status_code == 400
        print_test("SQL injection prevention", passed)
        all_passed = all_passed and passed
    except Exception as e:
        print_test("SQL injection prevention", False, f"Error: {e}")
        all_passed = False
    
    return all_passed

def test_authentication() -> bool:
    """Test authentication security"""
    print(f"\n{COLORS['BLUE']}Testing Authentication...{COLORS['RESET']}")
    
    all_passed = True
    
    # Test with wrong auth key
    try:
        response = requests.post(
            f"{BASE_URL}/authenticate",
            json={
                "fir_number": "FIR-12345678-20250101000000",
                "auth_key": "wrong-key"
            }
        )
        passed = response.status_code == 401
        print_test("Rejects invalid auth key", passed)
        all_passed = all_passed and passed
    except Exception as e:
        print_test("Rejects invalid auth key", False, f"Error: {e}")
        all_passed = False
    
    # Test timing attack resistance (basic check)
    try:
        times = []
        for _ in range(5):
            start = time.time()
            requests.post(
                f"{BASE_URL}/authenticate",
                json={
                    "fir_number": "FIR-12345678-20250101000000",
                    "auth_key": "wrong-key-" + "x" * 50
                }
            )
            times.append(time.time() - start)
        
        # Check if times are relatively consistent (within 50ms variance)
        avg_time = sum(times) / len(times)
        variance = max(abs(t - avg_time) for t in times)
        passed = variance < 0.05  # 50ms
        
        print_test("Timing attack resistance", passed, f"Variance: {variance*1000:.2f}ms")
        all_passed = all_passed and passed
    except Exception as e:
        print_test("Timing attack resistance", False, f"Error: {e}")
        all_passed = False
    
    return all_passed

def test_security_headers() -> bool:
    """Test security headers"""
    print(f"\n{COLORS['BLUE']}Testing Security Headers...{COLORS['RESET']}")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        headers = response.headers
        
        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": None,  # Should exist
            "Content-Security-Policy": None,  # Should exist
        }
        
        all_passed = True
        for header, expected_value in required_headers.items():
            has_header = header in headers
            if expected_value:
                passed = has_header and headers.get(header) == expected_value
            else:
                passed = has_header
            
            print_test(f"Header: {header}", passed, f"Value: {headers.get(header, 'MISSING')}")
            all_passed = all_passed and passed
        
        return all_passed
    except Exception as e:
        print_test("Security headers", False, f"Error: {e}")
        return False

def test_file_upload_validation() -> bool:
    """Test file upload validation"""
    print(f"\n{COLORS['BLUE']}Testing File Upload Validation...{COLORS['RESET']}")
    
    all_passed = True
    
    # Test oversized file
    try:
        large_content = b"x" * (26 * 1024 * 1024)  # 26MB (over limit)
        response = requests.post(
            f"{BASE_URL}/process",
            files={"audio": ("test.wav", large_content, "audio/wav")}
        )
        passed = response.status_code == 413
        print_test("Rejects oversized files", passed)
        all_passed = all_passed and passed
    except Exception as e:
        print_test("Rejects oversized files", False, f"Error: {e}")
        all_passed = False
    
    # Test invalid file type
    try:
        response = requests.post(
            f"{BASE_URL}/process",
            files={"audio": ("test.exe", b"fake content", "application/x-executable")}
        )
        passed = response.status_code == 415
        print_test("Rejects invalid file types", passed)
        all_passed = all_passed and passed
    except Exception as e:
        print_test("Rejects invalid file types", False, f"Error: {e}")
        all_passed = False
    
    return all_passed

def test_session_validation() -> bool:
    """Test session validation"""
    print(f"\n{COLORS['BLUE']}Testing Session Validation...{COLORS['RESET']}")
    
    all_passed = True
    
    # Test invalid session ID format
    try:
        response = requests.get(f"{BASE_URL}/session/invalid-session-id/status")
        passed = response.status_code == 400
        print_test("Rejects invalid session ID format", passed)
        all_passed = all_passed and passed
    except Exception as e:
        print_test("Rejects invalid session ID format", False, f"Error: {e}")
        all_passed = False
    
    # Test non-existent session
    try:
        response = requests.get(f"{BASE_URL}/session/12345678-1234-1234-1234-123456789012/status")
        passed = response.status_code == 404
        print_test("Returns 404 for non-existent session", passed)
        all_passed = all_passed and passed
    except Exception as e:
        print_test("Returns 404 for non-existent session", False, f"Error: {e}")
        all_passed = False
    
    return all_passed

def main():
    """Run all security tests"""
    print(f"\n{COLORS['YELLOW']}{'='*60}{COLORS['RESET']}")
    print(f"{COLORS['YELLOW']}AFIRGen Security Test Suite{COLORS['RESET']}")
    print(f"{COLORS['YELLOW']}{'='*60}{COLORS['RESET']}")
    print(f"\nTesting against: {BASE_URL}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"\n{COLORS['RED']}Error: Server is not healthy{COLORS['RESET']}")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print(f"\n{COLORS['RED']}Error: Cannot connect to server at {BASE_URL}{COLORS['RESET']}")
        print("Make sure the server is running: docker-compose up")
        sys.exit(1)
    
    # Run all tests
    results = {
        "CORS Protection": test_cors_protection(),
        "Rate Limiting": test_rate_limiting(),
        "Input Validation": test_input_validation(),
        "Authentication": test_authentication(),
        "Security Headers": test_security_headers(),
        "File Upload Validation": test_file_upload_validation(),
        "Session Validation": test_session_validation(),
    }
    
    # Summary
    print(f"\n{COLORS['YELLOW']}{'='*60}{COLORS['RESET']}")
    print(f"{COLORS['YELLOW']}Test Summary{COLORS['RESET']}")
    print(f"{COLORS['YELLOW']}{'='*60}{COLORS['RESET']}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    for test_name, passed in results.items():
        status = f"{COLORS['GREEN']}PASS{COLORS['RESET']}" if passed else f"{COLORS['RED']}FAIL{COLORS['RESET']}"
        print(f"{test_name:30s}: {status}")
    
    print(f"\n{COLORS['YELLOW']}Total: {passed_count}/{total_count} tests passed{COLORS['RESET']}")
    
    if passed_count == total_count:
        print(f"\n{COLORS['GREEN']}✓ All security tests passed!{COLORS['RESET']}")
        sys.exit(0)
    else:
        print(f"\n{COLORS['RED']}✗ Some security tests failed{COLORS['RESET']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
