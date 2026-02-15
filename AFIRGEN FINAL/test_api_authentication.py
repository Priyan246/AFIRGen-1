#!/usr/bin/env python3
"""
API Authentication Test Suite
Tests the API key authentication implementation for AFIRGen
"""

import requests
import os
import sys
import time
from typing import Dict, Any

# Configuration
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "test-key-for-development")
INVALID_KEY = "invalid-key-12345"

# Test results
test_results = []


def log_test(name: str, passed: bool, message: str = ""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if message:
        print(f"   {message}")
    test_results.append({"name": name, "passed": passed, "message": message})


def test_health_endpoint_no_auth():
    """Test that health endpoint works without authentication"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        passed = response.status_code == 200
        log_test(
            "Health endpoint without auth",
            passed,
            f"Status: {response.status_code}"
        )
        return passed
    except Exception as e:
        log_test("Health endpoint without auth", False, f"Error: {e}")
        return False


def test_protected_endpoint_no_auth():
    """Test that protected endpoints reject requests without API key"""
    try:
        response = requests.post(
            f"{API_BASE}/process",
            data={"text": "Test complaint"},
            timeout=5
        )
        passed = response.status_code == 401
        detail = response.json().get("detail", "") if response.status_code == 401 else ""
        log_test(
            "Protected endpoint without auth",
            passed,
            f"Status: {response.status_code}, Detail: {detail}"
        )
        return passed
    except Exception as e:
        log_test("Protected endpoint without auth", False, f"Error: {e}")
        return False


def test_protected_endpoint_invalid_auth():
    """Test that protected endpoints reject requests with invalid API key"""
    try:
        response = requests.post(
            f"{API_BASE}/process",
            headers={"X-API-Key": INVALID_KEY},
            data={"text": "Test complaint"},
            timeout=5
        )
        passed = response.status_code == 401
        detail = response.json().get("detail", "") if response.status_code == 401 else ""
        log_test(
            "Protected endpoint with invalid auth",
            passed,
            f"Status: {response.status_code}, Detail: {detail}"
        )
        return passed
    except Exception as e:
        log_test("Protected endpoint with invalid auth", False, f"Error: {e}")
        return False


def test_protected_endpoint_valid_auth_x_api_key():
    """Test that protected endpoints accept requests with valid X-API-Key header"""
    try:
        response = requests.post(
            f"{API_BASE}/process",
            headers={"X-API-Key": API_KEY},
            data={"text": "This is a test complaint about a theft incident"},
            timeout=30
        )
        passed = response.status_code in [200, 400]  # 200 or 400 (validation error) is OK
        log_test(
            "Protected endpoint with valid X-API-Key",
            passed,
            f"Status: {response.status_code}"
        )
        return passed
    except Exception as e:
        log_test("Protected endpoint with valid X-API-Key", False, f"Error: {e}")
        return False


def test_protected_endpoint_valid_auth_bearer():
    """Test that protected endpoints accept requests with valid Bearer token"""
    try:
        response = requests.post(
            f"{API_BASE}/process",
            headers={"Authorization": f"Bearer {API_KEY}"},
            data={"text": "This is a test complaint about a theft incident"},
            timeout=30
        )
        passed = response.status_code in [200, 400]  # 200 or 400 (validation error) is OK
        log_test(
            "Protected endpoint with valid Bearer token",
            passed,
            f"Status: {response.status_code}"
        )
        return passed
    except Exception as e:
        log_test("Protected endpoint with valid Bearer token", False, f"Error: {e}")
        return False


def test_timing_attack_resistance():
    """Test that authentication is resistant to timing attacks"""
    try:
        # Test with invalid key
        start1 = time.time()
        requests.post(
            f"{API_BASE}/process",
            headers={"X-API-Key": INVALID_KEY},
            data={"text": "Test"},
            timeout=5
        )
        time1 = time.time() - start1
        
        # Test with another invalid key
        start2 = time.time()
        requests.post(
            f"{API_BASE}/process",
            headers={"X-API-Key": "different-invalid-key"},
            data={"text": "Test"},
            timeout=5
        )
        time2 = time.time() - start2
        
        # Times should be similar (within 50ms)
        time_diff = abs(time1 - time2)
        passed = time_diff < 0.05
        log_test(
            "Timing attack resistance",
            passed,
            f"Time difference: {time_diff*1000:.2f}ms (should be <50ms)"
        )
        return passed
    except Exception as e:
        log_test("Timing attack resistance", False, f"Error: {e}")
        return False


def test_multiple_endpoints():
    """Test authentication on multiple endpoints"""
    endpoints = [
        ("GET", "/metrics"),
        ("GET", "/reliability/status"),
    ]
    
    all_passed = True
    for method, endpoint in endpoints:
        try:
            if method == "GET":
                # Without auth
                response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
                no_auth_passed = response.status_code == 401
                
                # With auth
                response = requests.get(
                    f"{API_BASE}{endpoint}",
                    headers={"X-API-Key": API_KEY},
                    timeout=5
                )
                with_auth_passed = response.status_code == 200
                
                passed = no_auth_passed and with_auth_passed
                log_test(
                    f"Authentication on {method} {endpoint}",
                    passed,
                    f"No auth: {401 if no_auth_passed else 'wrong'}, With auth: {200 if with_auth_passed else 'wrong'}"
                )
                all_passed = all_passed and passed
        except Exception as e:
            log_test(f"Authentication on {method} {endpoint}", False, f"Error: {e}")
            all_passed = False
    
    return all_passed


def test_cors_with_auth():
    """Test that CORS works with authentication headers"""
    try:
        # Preflight request
        response = requests.options(
            f"{API_BASE}/process",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-API-Key"
            },
            timeout=5
        )
        
        # Check if X-API-Key is allowed
        allowed_headers = response.headers.get("Access-Control-Allow-Headers", "")
        passed = "X-API-Key" in allowed_headers or "Authorization" in allowed_headers
        log_test(
            "CORS with authentication headers",
            passed,
            f"Allowed headers: {allowed_headers}"
        )
        return passed
    except Exception as e:
        log_test("CORS with authentication headers", False, f"Error: {e}")
        return False


def test_rate_limiting_with_auth():
    """Test that rate limiting works with authentication"""
    try:
        # Make multiple requests quickly
        responses = []
        for i in range(5):
            response = requests.get(
                f"{API_BASE}/metrics",
                headers={"X-API-Key": API_KEY},
                timeout=5
            )
            responses.append(response.status_code)
        
        # All should succeed (not rate limited yet)
        passed = all(status == 200 for status in responses)
        log_test(
            "Rate limiting with authentication",
            passed,
            f"Responses: {responses}"
        )
        return passed
    except Exception as e:
        log_test("Rate limiting with authentication", False, f"Error: {e}")
        return False


def test_error_messages():
    """Test that error messages are informative but don't leak sensitive info"""
    try:
        # Test missing key
        response = requests.post(f"{API_BASE}/process", data={"text": "Test"}, timeout=5)
        missing_key_msg = response.json().get("detail", "")
        missing_key_ok = "API key required" in missing_key_msg and API_KEY not in missing_key_msg
        
        # Test invalid key
        response = requests.post(
            f"{API_BASE}/process",
            headers={"X-API-Key": INVALID_KEY},
            data={"text": "Test"},
            timeout=5
        )
        invalid_key_msg = response.json().get("detail", "")
        invalid_key_ok = "Invalid API key" in invalid_key_msg and API_KEY not in invalid_key_msg
        
        passed = missing_key_ok and invalid_key_ok
        log_test(
            "Error messages don't leak sensitive info",
            passed,
            f"Missing: '{missing_key_msg}', Invalid: '{invalid_key_msg}'"
        )
        return passed
    except Exception as e:
        log_test("Error messages don't leak sensitive info", False, f"Error: {e}")
        return False


def run_all_tests():
    """Run all authentication tests"""
    print("=" * 60)
    print("API Authentication Test Suite")
    print("=" * 60)
    print(f"API Base URL: {API_BASE}")
    print(f"API Key: {'*' * (len(API_KEY) - 4)}{API_KEY[-4:]}")
    print("=" * 60)
    print()
    
    # Run tests
    tests = [
        test_health_endpoint_no_auth,
        test_protected_endpoint_no_auth,
        test_protected_endpoint_invalid_auth,
        test_protected_endpoint_valid_auth_x_api_key,
        test_protected_endpoint_valid_auth_bearer,
        test_timing_attack_resistance,
        test_multiple_endpoints,
        test_cors_with_auth,
        test_rate_limiting_with_auth,
        test_error_messages,
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ FAIL: {test.__name__} - Unexpected error: {e}")
        print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    total = len(test_results)
    passed = sum(1 for r in test_results if r["passed"])
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    print("=" * 60)
    
    if failed > 0:
        print("\nFailed Tests:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['name']}: {result['message']}")
    
    return failed == 0


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)
