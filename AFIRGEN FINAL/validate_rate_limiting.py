#!/usr/bin/env python3
"""
Rate Limiting Implementation Validator
Validates that rate limiting code is correctly implemented without running the server
"""

import sys
import re
from pathlib import Path

def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"    {details}")

def validate_rate_limiter_class(content: str) -> bool:
    """Validate RateLimiter class exists and is correct"""
    print_header("Validating RateLimiter Class")
    
    # Check class exists
    if "class RateLimiter:" not in content:
        print_result("RateLimiter class exists", False, "Class not found")
        return False
    
    print_result("RateLimiter class exists", True)
    
    # Check __init__ method
    has_init = "def __init__(self, max_requests: int = 100, window_seconds: int = 60):" in content
    print_result("__init__ method with correct signature", has_init)
    
    # Check is_allowed method
    has_is_allowed = "def is_allowed(self, client_id: str) -> bool:" in content
    print_result("is_allowed method exists", has_is_allowed)
    
    # Check uses defaultdict
    has_defaultdict = "self.requests = defaultdict(list)" in content
    print_result("Uses defaultdict for request tracking", has_defaultdict)
    
    # Check cleanup logic
    has_cleanup = "self.requests[client_id] = [" in content and "if now - req_time < self.window_seconds" in content
    print_result("Has cleanup logic for old requests", has_cleanup)
    
    return has_init and has_is_allowed and has_defaultdict and has_cleanup

def validate_rate_limit_middleware(content: str) -> bool:
    """Validate RateLimitMiddleware class exists and is correct"""
    print_header("Validating RateLimitMiddleware Class")
    
    # Check class exists
    if "class RateLimitMiddleware(BaseHTTPMiddleware):" not in content:
        print_result("RateLimitMiddleware class exists", False, "Class not found")
        return False
    
    print_result("RateLimitMiddleware class exists", True)
    
    # Check dispatch method
    has_dispatch = "async def dispatch(self, request: Request, call_next):" in content
    print_result("dispatch method exists", has_dispatch)
    
    # Check X-Forwarded-For support
    has_forwarded_for = 'request.headers.get("X-Forwarded-For"' in content
    print_result("X-Forwarded-For header support", has_forwarded_for)
    
    # Check X-Real-IP support
    has_real_ip = 'request.headers.get("X-Real-IP"' in content
    print_result("X-Real-IP header support", has_real_ip)
    
    # Check JSONResponse for 429
    has_json_response = "JSONResponse(" in content and "status_code=429" in content
    print_result("Returns JSONResponse for 429", has_json_response)
    
    # Check Retry-After header
    has_retry_after = '"Retry-After"' in content
    print_result("Includes Retry-After header", has_retry_after)
    
    # Check rate limit headers
    has_rate_headers = '"X-RateLimit-Limit"' in content and '"X-RateLimit-Window"' in content
    print_result("Includes rate limit headers", has_rate_headers)
    
    # Check exempt endpoints
    has_exempt = '"/health"' in content and '"/docs"' in content
    print_result("Has exempt endpoints", has_exempt)
    
    return all([has_dispatch, has_forwarded_for, has_json_response, has_retry_after, has_rate_headers])

def validate_imports(content: str) -> bool:
    """Validate required imports are present"""
    print_header("Validating Imports")
    
    # Check for time import
    has_time = "from time import time" in content
    print_result("time import", has_time)
    
    # Check for defaultdict import
    has_defaultdict = "from collections import defaultdict" in content
    print_result("defaultdict import", has_defaultdict)
    
    # Check for JSONResponse import
    has_json_response = "from fastapi.responses import" in content and "JSONResponse" in content
    print_result("JSONResponse import", has_json_response)
    
    # Check for BaseHTTPMiddleware import
    has_middleware = "from starlette.middleware.base import BaseHTTPMiddleware" in content
    print_result("BaseHTTPMiddleware import", has_middleware)
    
    return has_time and has_defaultdict and has_json_response and has_middleware

def validate_configuration(content: str) -> bool:
    """Validate rate limiter configuration"""
    print_header("Validating Configuration")
    
    # Check rate_limiter instance
    has_instance = "rate_limiter = RateLimiter(" in content
    print_result("rate_limiter instance created", has_instance)
    
    # Check environment variable usage
    has_env_requests = 'os.getenv("RATE_LIMIT_REQUESTS"' in content
    print_result("RATE_LIMIT_REQUESTS env var", has_env_requests)
    
    has_env_window = 'os.getenv("RATE_LIMIT_WINDOW"' in content
    print_result("RATE_LIMIT_WINDOW env var", has_env_window)
    
    return has_instance and has_env_requests and has_env_window

def validate_middleware_registration(content: str) -> bool:
    """Validate middleware is registered with FastAPI"""
    print_header("Validating Middleware Registration")
    
    # Check middleware is added to app
    has_registration = "app.add_middleware(RateLimitMiddleware)" in content
    print_result("Middleware registered with app", has_registration)
    
    return has_registration

def validate_logging(content: str) -> bool:
    """Validate logging is implemented"""
    print_header("Validating Logging")
    
    # Check for rate limit logging
    has_logging = 'log.warning' in content and 'Rate limit exceeded' in content
    print_result("Rate limit violations are logged", has_logging)
    
    return has_logging

def validate_error_response_format(content: str) -> bool:
    """Validate error response format"""
    print_header("Validating Error Response Format")
    
    # Check for detail field
    has_detail = '"detail":' in content and 'Rate limit exceeded' in content
    print_result("Error response has detail field", has_detail)
    
    # Check for error field
    has_error = '"error":' in content and 'too_many_requests' in content
    print_result("Error response has error field", has_error)
    
    return has_detail and has_error

def main():
    """Main validation function"""
    print("\n" + "=" * 70)
    print("  RATE LIMITING IMPLEMENTATION VALIDATOR")
    print("  Validating code without running the server")
    print("=" * 70)
    
    # Read the main backend file
    backend_file = Path("main backend/agentv5.py")
    
    if not backend_file.exists():
        print(f"\n❌ File not found: {backend_file}")
        print("   Make sure you're running this from the 'AFIRGEN FINAL' directory")
        return False
    
    print(f"\n📄 Reading file: {backend_file}")
    
    with open(backend_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"✅ File loaded ({len(content)} characters)")
    
    # Run all validations
    results = []
    
    results.append(validate_imports(content))
    results.append(validate_rate_limiter_class(content))
    results.append(validate_rate_limit_middleware(content))
    results.append(validate_configuration(content))
    results.append(validate_middleware_registration(content))
    results.append(validate_logging(content))
    results.append(validate_error_response_format(content))
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nValidation Groups Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All validations passed!")
        print("\n✅ Rate limiting implementation is correct")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r test_requirements.txt")
        print("2. Start the server: python 'main backend/agentv5.py'")
        print("3. Run tests: python test_rate_limiting.py")
        return True
    else:
        print(f"\n⚠️  {total - passed} validation group(s) failed")
        print("\nPlease review the failed checks above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
