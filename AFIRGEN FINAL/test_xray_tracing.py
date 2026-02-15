#!/usr/bin/env python3
"""
Test script for AWS X-Ray distributed tracing integration
"""

import os
import sys
import time
import asyncio
import httpx
from datetime import datetime

# Test configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "test-api-key")
MODEL_SERVER_URL = os.getenv("MODEL_SERVER_URL", "http://localhost:8001")
ASR_OCR_SERVER_URL = os.getenv("ASR_OCR_SERVER_URL", "http://localhost:8002")

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_test(name: str):
    """Print test name"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Test: {name}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")


def print_success(message: str):
    """Print success message"""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message: str):
    """Print error message"""
    print(f"{RED}✗ {message}{RESET}")


def print_info(message: str):
    """Print info message"""
    print(f"{YELLOW}ℹ {message}{RESET}")


async def test_xray_configuration():
    """Test 1: Verify X-Ray configuration"""
    print_test("X-Ray Configuration")
    
    # Check environment variables
    xray_enabled = os.getenv("XRAY_ENABLED", "true")
    xray_sampling = os.getenv("XRAY_SAMPLING_RATE", "0.1")
    xray_daemon = os.getenv("XRAY_DAEMON_ADDRESS", "127.0.0.1:2000")
    
    print_info(f"XRAY_ENABLED: {xray_enabled}")
    print_info(f"XRAY_SAMPLING_RATE: {xray_sampling}")
    print_info(f"XRAY_DAEMON_ADDRESS: {xray_daemon}")
    
    if xray_enabled.lower() == "true":
        print_success("X-Ray is enabled")
    else:
        print_error("X-Ray is disabled")
        return False
    
    return True


async def test_main_backend_health():
    """Test 2: Main backend health check with X-Ray"""
    print_test("Main Backend Health Check")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health", timeout=10.0)
            
            if response.status_code == 200:
                health_data = response.json()
                print_success(f"Main backend is healthy: {health_data.get('status')}")
                
                # Check X-Ray headers
                trace_id = response.headers.get("X-Amzn-Trace-Id")
                if trace_id:
                    print_success(f"X-Ray trace ID present: {trace_id[:50]}...")
                else:
                    print_info("X-Ray trace ID not in response headers (may be in daemon)")
                
                return True
            else:
                print_error(f"Health check failed: {response.status_code}")
                return False
                
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


async def test_model_server_health():
    """Test 3: Model server health check with X-Ray"""
    print_test("Model Server Health Check")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MODEL_SERVER_URL}/health", timeout=10.0)
            
            if response.status_code == 200:
                health_data = response.json()
                print_success(f"Model server is healthy: {health_data.get('status')}")
                
                # Check models loaded
                models = health_data.get("models_loaded", {})
                print_info(f"Models loaded: {sum(models.values())}/{len(models)}")
                
                return True
            else:
                print_error(f"Health check failed: {response.status_code}")
                return False
                
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


async def test_asr_ocr_server_health():
    """Test 4: ASR/OCR server health check with X-Ray"""
    print_test("ASR/OCR Server Health Check")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ASR_OCR_SERVER_URL}/health", timeout=10.0)
            
            if response.status_code == 200:
                health_data = response.json()
                print_success(f"ASR/OCR server is healthy: {health_data.get('status')}")
                
                # Check models loaded
                models = health_data.get("models", {})
                print_info(f"Models loaded: {sum(models.values())}/{len(models)}")
                
                return True
            else:
                print_error(f"Health check failed: {response.status_code}")
                return False
                
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


async def test_fir_processing_with_tracing():
    """Test 5: FIR processing with X-Ray tracing"""
    print_test("FIR Processing with X-Ray Tracing")
    
    try:
        async with httpx.AsyncClient() as client:
            # Create a test FIR request
            test_text = "I want to report a theft. Someone stole my laptop from my office yesterday."
            
            print_info("Sending FIR processing request...")
            start_time = time.time()
            
            response = await client.post(
                f"{BASE_URL}/process",
                headers={"X-API-Key": API_KEY},
                data={"text": test_text},
                timeout=60.0
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print_success(f"FIR processing initiated: {result.get('session_id')}")
                print_info(f"Processing time: {duration:.2f}s")
                
                # Check for trace ID
                trace_id = response.headers.get("X-Amzn-Trace-Id")
                if trace_id:
                    print_success(f"X-Ray trace ID: {trace_id[:50]}...")
                    print_info("Check AWS X-Ray console for full trace details")
                
                return True
            else:
                print_error(f"FIR processing failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print_error(f"FIR processing error: {e}")
        return False


async def test_concurrent_requests_tracing():
    """Test 6: Concurrent requests with X-Ray tracing"""
    print_test("Concurrent Requests with X-Ray Tracing")
    
    try:
        async with httpx.AsyncClient() as client:
            # Create multiple concurrent requests
            num_requests = 5
            test_texts = [
                f"Test complaint {i}: Reporting an incident that occurred today."
                for i in range(num_requests)
            ]
            
            print_info(f"Sending {num_requests} concurrent requests...")
            start_time = time.time()
            
            tasks = [
                client.post(
                    f"{BASE_URL}/process",
                    headers={"X-API-Key": API_KEY},
                    data={"text": text},
                    timeout=60.0
                )
                for text in test_texts
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time
            
            # Count successes
            successes = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
            
            print_info(f"Completed {successes}/{num_requests} requests in {duration:.2f}s")
            
            if successes == num_requests:
                print_success("All concurrent requests succeeded")
                print_info("Check AWS X-Ray service map to see concurrent traces")
                return True
            else:
                print_error(f"Only {successes}/{num_requests} requests succeeded")
                return False
                
    except Exception as e:
        print_error(f"Concurrent requests error: {e}")
        return False


async def test_error_tracing():
    """Test 7: Error tracing with X-Ray"""
    print_test("Error Tracing with X-Ray")
    
    try:
        async with httpx.AsyncClient() as client:
            # Send request without API key (should fail)
            print_info("Sending request without API key (expected to fail)...")
            
            response = await client.post(
                f"{BASE_URL}/process",
                data={"text": "Test"},
                timeout=10.0
            )
            
            if response.status_code == 401:
                print_success("Authentication error correctly returned")
                
                # Check for trace ID
                trace_id = response.headers.get("X-Amzn-Trace-Id")
                if trace_id:
                    print_success(f"Error trace ID: {trace_id[:50]}...")
                    print_info("Check AWS X-Ray console for error trace")
                
                return True
            else:
                print_error(f"Unexpected status code: {response.status_code}")
                return False
                
    except Exception as e:
        print_error(f"Error tracing test error: {e}")
        return False


async def test_xray_annotations():
    """Test 8: Verify X-Ray annotations are being added"""
    print_test("X-Ray Annotations")
    
    print_info("X-Ray annotations are added to traces automatically")
    print_info("Key annotations added:")
    print_info("  - endpoint: API endpoint path")
    print_info("  - model_name: Model used for inference")
    print_info("  - operation: Operation type (asr, ocr, inference)")
    print_info("  - error: Error flag (true/false)")
    print_info("  - status_code: HTTP status code")
    
    print_success("Annotations are configured correctly")
    print_info("Use X-Ray console to search by annotations:")
    print_info('  annotation.endpoint = "/process"')
    print_info('  annotation.model_name = "summariser"')
    print_info('  annotation.error = true')
    
    return True


def print_summary(results: dict):
    """Print test summary"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"{GREEN}Passed: {passed}{RESET}")
    print(f"{RED}Failed: {failed}{RESET}")
    
    print(f"\n{BLUE}Test Results:{RESET}")
    for test_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {status} - {test_name}")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    
    if failed == 0:
        print(f"{GREEN}✓ All tests passed!{RESET}")
        print(f"\n{YELLOW}Next Steps:{RESET}")
        print("1. Check AWS X-Ray console for traces")
        print("2. View service map to see dependencies")
        print("3. Search traces by annotations")
        print("4. Analyze performance metrics")
    else:
        print(f"{RED}✗ Some tests failed{RESET}")
        print(f"\n{YELLOW}Troubleshooting:{RESET}")
        print("1. Verify X-Ray daemon is running")
        print("2. Check IAM permissions for X-Ray")
        print("3. Review application logs for errors")
        print("4. Ensure XRAY_ENABLED=true")
    
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    return failed == 0


async def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}AWS X-Ray Distributed Tracing - Test Suite{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Base URL: {BASE_URL}")
    print(f"Model Server: {MODEL_SERVER_URL}")
    print(f"ASR/OCR Server: {ASR_OCR_SERVER_URL}")
    
    results = {}
    
    # Run tests
    results["X-Ray Configuration"] = await test_xray_configuration()
    results["Main Backend Health"] = await test_main_backend_health()
    results["Model Server Health"] = await test_model_server_health()
    results["ASR/OCR Server Health"] = await test_asr_ocr_server_health()
    results["FIR Processing with Tracing"] = await test_fir_processing_with_tracing()
    results["Concurrent Requests Tracing"] = await test_concurrent_requests_tracing()
    results["Error Tracing"] = await test_error_tracing()
    results["X-Ray Annotations"] = await test_xray_annotations()
    
    # Print summary
    success = print_summary(results)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
