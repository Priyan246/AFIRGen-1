#!/usr/bin/env python3
"""
Test suite for input validation on all AFIRGen API endpoints
"""
import requests
import json
import uuid
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key-12345"  # Replace with actual API key from environment

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}

def log_test(test_name, passed, message=""):
    """Log test result"""
    if passed:
        test_results["passed"] += 1
        print(f"✅ PASS: {test_name}")
    else:
        test_results["failed"] += 1
        test_results["errors"].append(f"{test_name}: {message}")
        print(f"❌ FAIL: {test_name} - {message}")

def make_request(method, endpoint, **kwargs):
    """Make HTTP request with API key"""
    headers = kwargs.get("headers", {})
    headers["X-API-Key"] = API_KEY
    kwargs["headers"] = headers
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            return requests.get(url, **kwargs)
        elif method == "POST":
            return requests.post(url, **kwargs)
        elif method == "PUT":
            return requests.put(url, **kwargs)
        elif method == "DELETE":
            return requests.delete(url, **kwargs)
    except Exception as e:
        return None

# ============================================================================
# TEST 1: /process endpoint validation
# ============================================================================
def test_process_endpoint():
    print("\n" + "="*60)
    print("TEST 1: /process endpoint validation")
    print("="*60)
    
    # Test 1.1: No input provided
    resp = make_request("POST", "/process")
    log_test(
        "1.1 /process - No input provided",
        resp and resp.status_code == 400,
        f"Expected 400, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 1.2: Text too short
    resp = make_request("POST", "/process", json={"text": "short"})
    log_test(
        "1.2 /process - Text too short",
        resp and resp.status_code == 400,
        f"Expected 400, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 1.3: Text too long
    long_text = "A" * 60000  # Exceeds MAX_TEXT_LENGTH
    resp = make_request("POST", "/process", json={"text": long_text})
    log_test(
        "1.3 /process - Text too long",
        resp and resp.status_code == 413,
        f"Expected 413, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 1.4: XSS attempt in text
    xss_text = "<script>alert('XSS')</script>" + "A" * 100
    resp = make_request("POST", "/process", json={"text": xss_text})
    log_test(
        "1.4 /process - XSS attempt blocked",
        resp and resp.status_code == 400,
        f"Expected 400, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 1.5: Valid text input
    valid_text = "I want to report a theft that occurred yesterday at the market. The suspect stole my wallet containing cash and credit cards."
    resp = make_request("POST", "/process", json={"text": valid_text})
    log_test(
        "1.5 /process - Valid text input",
        resp and resp.status_code == 200,
        f"Expected 200, got {resp.status_code if resp else 'No response'}"
    )
    
    return resp.json().get("session_id") if resp and resp.status_code == 200 else None

# ============================================================================
# TEST 2: /validate endpoint validation
# ============================================================================
def test_validate_endpoint(session_id):
    print("\n" + "="*60)
    print("TEST 2: /validate endpoint validation")
    print("="*60)
    
    # Test 2.1: Invalid session ID format
    resp = make_request("POST", "/validate", json={
        "session_id": "invalid-uuid",
        "approved": True
    })
    log_test(
        "2.1 /validate - Invalid session ID format",
        resp and resp.status_code == 422,  # Pydantic validation error
        f"Expected 422, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 2.2: Non-existent session ID
    fake_uuid = str(uuid.uuid4())
    resp = make_request("POST", "/validate", json={
        "session_id": fake_uuid,
        "approved": True
    })
    log_test(
        "2.2 /validate - Non-existent session ID",
        resp and resp.status_code == 404,
        f"Expected 404, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 2.3: User input too long
    if session_id:
        long_input = "A" * 15000  # Exceeds MAX_USER_INPUT_LENGTH
        resp = make_request("POST", "/validate", json={
            "session_id": session_id,
            "approved": True,
            "user_input": long_input
        })
        log_test(
            "2.3 /validate - User input too long",
            resp and resp.status_code == 422,
            f"Expected 422, got {resp.status_code if resp else 'No response'}"
        )
    
    # Test 2.4: XSS attempt in user input
    if session_id:
        xss_input = "<script>alert('XSS')</script>"
        resp = make_request("POST", "/validate", json={
            "session_id": session_id,
            "approved": True,
            "user_input": xss_input
        })
        log_test(
            "2.4 /validate - XSS attempt in user input",
            resp and resp.status_code == 400,
            f"Expected 400, got {resp.status_code if resp else 'No response'}"
        )
    
    # Test 2.5: Valid validation request
    if session_id:
        resp = make_request("POST", "/validate", json={
            "session_id": session_id,
            "approved": True,
            "user_input": "Additional context about the incident"
        })
        log_test(
            "2.5 /validate - Valid validation request",
            resp and resp.status_code == 200,
            f"Expected 200, got {resp.status_code if resp else 'No response'}"
        )

# ============================================================================
# TEST 3: /session/{session_id}/status endpoint validation
# ============================================================================
def test_session_status_endpoint(session_id):
    print("\n" + "="*60)
    print("TEST 3: /session/{session_id}/status endpoint validation")
    print("="*60)
    
    # Test 3.1: Invalid session ID format
    resp = make_request("GET", "/session/invalid-uuid/status")
    log_test(
        "3.1 /session/status - Invalid session ID format",
        resp and resp.status_code == 400,
        f"Expected 400, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 3.2: Non-existent session ID
    fake_uuid = str(uuid.uuid4())
    resp = make_request("GET", f"/session/{fake_uuid}/status")
    log_test(
        "3.2 /session/status - Non-existent session ID",
        resp and resp.status_code == 404,
        f"Expected 404, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 3.3: Valid session ID
    if session_id:
        resp = make_request("GET", f"/session/{session_id}/status")
        log_test(
            "3.3 /session/status - Valid session ID",
            resp and resp.status_code == 200,
            f"Expected 200, got {resp.status_code if resp else 'No response'}"
        )

# ============================================================================
# TEST 4: /authenticate endpoint validation
# ============================================================================
def test_authenticate_endpoint():
    print("\n" + "="*60)
    print("TEST 4: /authenticate endpoint validation")
    print("="*60)
    
    # Test 4.1: Invalid FIR number format
    resp = make_request("POST", "/authenticate", json={
        "fir_number": "invalid-fir",
        "auth_key": "test-auth-key"
    })
    log_test(
        "4.1 /authenticate - Invalid FIR number format",
        resp and resp.status_code == 422,
        f"Expected 422, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 4.2: Auth key too short
    resp = make_request("POST", "/authenticate", json={
        "fir_number": "FIR-12345678-20240101120000",
        "auth_key": "short"
    })
    log_test(
        "4.2 /authenticate - Auth key too short",
        resp and resp.status_code == 422,
        f"Expected 422, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 4.3: Non-existent FIR
    resp = make_request("POST", "/authenticate", json={
        "fir_number": "FIR-12345678-20240101120000",
        "auth_key": "valid-auth-key-12345"
    })
    log_test(
        "4.3 /authenticate - Non-existent FIR",
        resp and resp.status_code in [401, 404],  # Either invalid auth or FIR not found
        f"Expected 401 or 404, got {resp.status_code if resp else 'No response'}"
    )

# ============================================================================
# TEST 5: /fir/{fir_number} endpoint validation
# ============================================================================
def test_fir_endpoints():
    print("\n" + "="*60)
    print("TEST 5: /fir/{fir_number} endpoint validation")
    print("="*60)
    
    # Test 5.1: Invalid FIR number format
    resp = make_request("GET", "/fir/invalid-fir")
    log_test(
        "5.1 /fir/{fir_number} - Invalid FIR number format",
        resp and resp.status_code == 400,
        f"Expected 400, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 5.2: Non-existent FIR
    resp = make_request("GET", "/fir/FIR-12345678-20240101120000")
    log_test(
        "5.2 /fir/{fir_number} - Non-existent FIR",
        resp and resp.status_code == 404,
        f"Expected 404, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 5.3: Invalid FIR number format for content endpoint
    resp = make_request("GET", "/fir/invalid-fir/content")
    log_test(
        "5.3 /fir/{fir_number}/content - Invalid FIR number format",
        resp and resp.status_code == 400,
        f"Expected 400, got {resp.status_code if resp else 'No response'}"
    )

# ============================================================================
# TEST 6: /list_firs endpoint validation
# ============================================================================
def test_list_firs_endpoint():
    print("\n" + "="*60)
    print("TEST 6: /list_firs endpoint validation")
    print("="*60)
    
    # Test 6.1: Valid request without parameters
    resp = make_request("GET", "/list_firs")
    log_test(
        "6.1 /list_firs - Valid request without parameters",
        resp and resp.status_code == 200,
        f"Expected 200, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 6.2: Valid request with limit
    resp = make_request("GET", "/list_firs?limit=10")
    log_test(
        "6.2 /list_firs - Valid request with limit",
        resp and resp.status_code == 200,
        f"Expected 200, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 6.3: Invalid limit (too large)
    resp = make_request("GET", "/list_firs?limit=2000")
    log_test(
        "6.3 /list_firs - Invalid limit (too large)",
        resp and resp.status_code == 400,
        f"Expected 400, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 6.4: Invalid limit (negative)
    resp = make_request("GET", "/list_firs?limit=-1")
    log_test(
        "6.4 /list_firs - Invalid limit (negative)",
        resp and resp.status_code == 400,
        f"Expected 400, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 6.5: Invalid offset (negative)
    resp = make_request("GET", "/list_firs?offset=-1")
    log_test(
        "6.5 /list_firs - Invalid offset (negative)",
        resp and resp.status_code == 400,
        f"Expected 400, got {resp.status_code if resp else 'No response'}"
    )

# ============================================================================
# TEST 7: Circuit breaker endpoint validation
# ============================================================================
def test_circuit_breaker_endpoints():
    print("\n" + "="*60)
    print("TEST 7: Circuit breaker endpoint validation")
    print("="*60)
    
    # Test 7.1: Invalid circuit breaker name
    resp = make_request("POST", "/reliability/circuit-breaker/invalid_name/reset")
    log_test(
        "7.1 /reliability/circuit-breaker - Invalid name",
        resp and resp.status_code == 404,
        f"Expected 404, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 7.2: Valid circuit breaker name
    resp = make_request("POST", "/reliability/circuit-breaker/model_server/reset")
    log_test(
        "7.2 /reliability/circuit-breaker - Valid name",
        resp and resp.status_code == 200,
        f"Expected 200, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 7.3: Invalid recovery handler name
    resp = make_request("POST", "/reliability/auto-recovery/invalid_name/trigger")
    log_test(
        "7.3 /reliability/auto-recovery - Invalid name",
        resp and resp.status_code == 404,
        f"Expected 404, got {resp.status_code if resp else 'No response'}"
    )

# ============================================================================
# TEST 8: API authentication validation
# ============================================================================
def test_api_authentication():
    print("\n" + "="*60)
    print("TEST 8: API authentication validation")
    print("="*60)
    
    # Test 8.1: Missing API key
    resp = requests.get(f"{BASE_URL}/list_firs")
    log_test(
        "8.1 API Auth - Missing API key",
        resp and resp.status_code == 401,
        f"Expected 401, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 8.2: Invalid API key
    resp = requests.get(f"{BASE_URL}/list_firs", headers={"X-API-Key": "invalid-key"})
    log_test(
        "8.2 API Auth - Invalid API key",
        resp and resp.status_code == 401,
        f"Expected 401, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 8.3: Valid API key
    resp = requests.get(f"{BASE_URL}/list_firs", headers={"X-API-Key": API_KEY})
    log_test(
        "8.3 API Auth - Valid API key",
        resp and resp.status_code == 200,
        f"Expected 200, got {resp.status_code if resp else 'No response'}"
    )
    
    # Test 8.4: Health endpoint should not require auth
    resp = requests.get(f"{BASE_URL}/health")
    log_test(
        "8.4 API Auth - Health endpoint public",
        resp and resp.status_code == 200,
        f"Expected 200, got {resp.status_code if resp else 'No response'}"
    )

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================
def main():
    print("\n" + "="*60)
    print("AFIRGen Input Validation Test Suite")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:10]}..." if len(API_KEY) > 10 else API_KEY)
    
    # Check if server is running
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code != 200:
            print("\n❌ ERROR: Server is not healthy")
            return
    except Exception as e:
        print(f"\n❌ ERROR: Cannot connect to server: {e}")
        print("Please ensure the AFIRGen backend is running on", BASE_URL)
        return
    
    print("✅ Server is running and healthy\n")
    
    # Run all tests
    session_id = test_process_endpoint()
    test_validate_endpoint(session_id)
    test_session_status_endpoint(session_id)
    test_authenticate_endpoint()
    test_fir_endpoints()
    test_list_firs_endpoint()
    test_circuit_breaker_endpoints()
    test_api_authentication()
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"📊 Total: {test_results['passed'] + test_results['failed']}")
    
    if test_results['failed'] > 0:
        print("\n❌ FAILED TESTS:")
        for error in test_results['errors']:
            print(f"  - {error}")
    
    print("\n" + "="*60)
    
    # Exit with appropriate code
    exit(0 if test_results['failed'] == 0 else 1)

if __name__ == "__main__":
    main()
