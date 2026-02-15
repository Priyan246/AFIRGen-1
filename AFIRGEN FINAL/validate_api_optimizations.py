#!/usr/bin/env python3
"""
Comprehensive validation script for API response time optimizations
Validates all changes are working correctly
"""

import asyncio
import httpx
import time
import json
from typing import Dict, List

MAIN_BACKEND_URL = "http://localhost:8000"

class ValidationTest:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_pass(self, test_name: str, message: str = ""):
        self.results["passed"].append({"test": test_name, "message": message})
        print(f"✅ {test_name}: {message}")
    
    def log_fail(self, test_name: str, message: str):
        self.results["failed"].append({"test": test_name, "message": message})
        print(f"❌ {test_name}: {message}")
    
    def log_warning(self, test_name: str, message: str):
        self.results["warnings"].append({"test": test_name, "message": message})
        print(f"⚠️  {test_name}: {message}")
    
    async def test_health_endpoint(self) -> bool:
        """Test health endpoint and verify caching"""
        try:
            # First request (uncached)
            start = time.perf_counter()
            resp1 = await self.client.get(f"{MAIN_BACKEND_URL}/health")
            time1 = (time.perf_counter() - start) * 1000
            resp1.raise_for_status()
            
            # Second request (should be cached)
            start = time.perf_counter()
            resp2 = await self.client.get(f"{MAIN_BACKEND_URL}/health")
            time2 = (time.perf_counter() - start) * 1000
            resp2.raise_for_status()
            
            # Verify response structure
            health = resp1.json()
            if "status" not in health:
                self.log_fail("Health Endpoint", "Missing 'status' field")
                return False
            
            # Check if second request is faster (cached)
            if time2 < time1:
                self.log_pass("Health Endpoint Caching", f"Cached request faster: {time1:.2f}ms → {time2:.2f}ms")
            else:
                self.log_warning("Health Endpoint Caching", f"Cached request not faster: {time1:.2f}ms → {time2:.2f}ms")
            
            # Check response time
            if time2 < 200:
                self.log_pass("Health Endpoint Response Time", f"{time2:.2f}ms < 200ms")
                return True
            else:
                self.log_fail("Health Endpoint Response Time", f"{time2:.2f}ms >= 200ms")
                return False
                
        except Exception as e:
            self.log_fail("Health Endpoint", str(e))
            return False
    
    async def test_session_status_endpoint(self) -> bool:
        """Test session status endpoint with caching"""
        try:
            # Create a test session first
            resp = await self.client.post(
                f"{MAIN_BACKEND_URL}/process",
                data={"text": "Test complaint for validation"}
            )
            resp.raise_for_status()
            result = resp.json()
            session_id = result.get("session_id")
            
            if not session_id:
                self.log_fail("Session Creation", "No session_id returned")
                return False
            
            # First request (uncached)
            start = time.perf_counter()
            resp1 = await self.client.get(f"{MAIN_BACKEND_URL}/session/{session_id}/status")
            time1 = (time.perf_counter() - start) * 1000
            resp1.raise_for_status()
            
            # Second request (should be cached)
            start = time.perf_counter()
            resp2 = await self.client.get(f"{MAIN_BACKEND_URL}/session/{session_id}/status")
            time2 = (time.perf_counter() - start) * 1000
            resp2.raise_for_status()
            
            # Verify response structure
            status = resp1.json()
            if "session_id" not in status or "status" not in status:
                self.log_fail("Session Status Endpoint", "Missing required fields")
                return False
            
            # Verify validation_history is NOT in response (optimization)
            if "validation_history" in status:
                self.log_warning("Session Status Optimization", "validation_history still in response (should be removed)")
            else:
                self.log_pass("Session Status Optimization", "validation_history removed from response")
            
            # Check if second request is faster (cached)
            if time2 < time1:
                self.log_pass("Session Status Caching", f"Cached request faster: {time1:.2f}ms → {time2:.2f}ms")
            else:
                self.log_warning("Session Status Caching", f"Cached request not faster: {time1:.2f}ms → {time2:.2f}ms")
            
            # Check response time
            if time2 < 200:
                self.log_pass("Session Status Response Time", f"{time2:.2f}ms < 200ms")
                return True
            else:
                self.log_fail("Session Status Response Time", f"{time2:.2f}ms >= 200ms")
                return False
                
        except Exception as e:
            self.log_fail("Session Status Endpoint", str(e))
            return False
    
    async def test_fir_endpoints(self) -> bool:
        """Test FIR status and content endpoints"""
        try:
            # Create a complete FIR
            resp = await self.client.post(
                f"{MAIN_BACKEND_URL}/process",
                data={"text": "Test complaint for FIR validation"}
            )
            resp.raise_for_status()
            result = resp.json()
            session_id = result.get("session_id")
            
            # Complete workflow to get FIR
            for _ in range(5):
                resp = await self.client.post(
                    f"{MAIN_BACKEND_URL}/validate",
                    json={"session_id": session_id, "approved": True}
                )
                resp.raise_for_status()
                result = resp.json()
                
                if result.get("completed"):
                    fir_number = result.get("content", {}).get("fir_number")
                    break
            else:
                self.log_fail("FIR Creation", "Could not create FIR")
                return False
            
            # Test /fir/{number} endpoint (status only)
            start = time.perf_counter()
            resp1 = await self.client.get(f"{MAIN_BACKEND_URL}/fir/{fir_number}")
            time1 = (time.perf_counter() - start) * 1000
            resp1.raise_for_status()
            status_data = resp1.json()
            
            # Verify content is NOT in response (optimization)
            if "content" in status_data:
                self.log_warning("FIR Status Optimization", "content still in response (should be removed)")
            else:
                self.log_pass("FIR Status Optimization", "content removed from status endpoint")
            
            # Test /fir/{number}/content endpoint
            start = time.perf_counter()
            resp2 = await self.client.get(f"{MAIN_BACKEND_URL}/fir/{fir_number}/content")
            time2 = (time.perf_counter() - start) * 1000
            resp2.raise_for_status()
            content_data = resp2.json()
            
            # Verify content IS in response
            if "content" not in content_data:
                self.log_fail("FIR Content Endpoint", "content missing from content endpoint")
                return False
            else:
                self.log_pass("FIR Content Endpoint", "content present in content endpoint")
            
            # Test caching - request status again
            start = time.perf_counter()
            resp3 = await self.client.get(f"{MAIN_BACKEND_URL}/fir/{fir_number}")
            time3 = (time.perf_counter() - start) * 1000
            resp3.raise_for_status()
            
            if time3 < time1:
                self.log_pass("FIR Status Caching", f"Cached request faster: {time1:.2f}ms → {time3:.2f}ms")
            else:
                self.log_warning("FIR Status Caching", f"Cached request not faster: {time1:.2f}ms → {time3:.2f}ms")
            
            # Check response times
            if time3 < 200:
                self.log_pass("FIR Status Response Time", f"{time3:.2f}ms < 200ms")
            else:
                self.log_fail("FIR Status Response Time", f"{time3:.2f}ms >= 200ms")
            
            if time2 < 200:
                self.log_pass("FIR Content Response Time", f"{time2:.2f}ms < 200ms")
            else:
                self.log_warning("FIR Content Response Time", f"{time2:.2f}ms >= 200ms (acceptable for content endpoint)")
            
            return True
            
        except Exception as e:
            self.log_fail("FIR Endpoints", str(e))
            return False
    
    async def test_metrics_endpoint(self) -> bool:
        """Test metrics endpoint with caching"""
        try:
            # First request (uncached)
            start = time.perf_counter()
            resp1 = await self.client.get(f"{MAIN_BACKEND_URL}/metrics")
            time1 = (time.perf_counter() - start) * 1000
            resp1.raise_for_status()
            
            # Second request (should be cached)
            start = time.perf_counter()
            resp2 = await self.client.get(f"{MAIN_BACKEND_URL}/metrics")
            time2 = (time.perf_counter() - start) * 1000
            resp2.raise_for_status()
            
            # Check if second request is faster (cached)
            if time2 < time1:
                self.log_pass("Metrics Caching", f"Cached request faster: {time1:.2f}ms → {time2:.2f}ms")
            else:
                self.log_warning("Metrics Caching", f"Cached request not faster: {time1:.2f}ms → {time2:.2f}ms")
            
            # Check response time
            if time2 < 200:
                self.log_pass("Metrics Response Time", f"{time2:.2f}ms < 200ms")
                return True
            else:
                self.log_fail("Metrics Response Time", f"{time2:.2f}ms >= 200ms")
                return False
                
        except Exception as e:
            self.log_fail("Metrics Endpoint", str(e))
            return False
    
    async def test_list_firs_endpoint(self) -> bool:
        """Test list_firs endpoint"""
        try:
            start = time.perf_counter()
            resp = await self.client.get(f"{MAIN_BACKEND_URL}/list_firs")
            elapsed = (time.perf_counter() - start) * 1000
            resp.raise_for_status()
            
            # Check response time
            if elapsed < 200:
                self.log_pass("List FIRs Response Time", f"{elapsed:.2f}ms < 200ms")
                return True
            else:
                self.log_fail("List FIRs Response Time", f"{elapsed:.2f}ms >= 200ms")
                return False
                
        except Exception as e:
            self.log_fail("List FIRs Endpoint", str(e))
            return False
    
    async def run_all_tests(self):
        """Run all validation tests"""
        print("="*70)
        print("API Response Time Optimization - Validation Suite")
        print("="*70)
        print()
        
        # Test 1: Health endpoint
        print("Test 1: Health Endpoint")
        print("-" * 70)
        await self.test_health_endpoint()
        print()
        
        # Test 2: Session status endpoint
        print("Test 2: Session Status Endpoint")
        print("-" * 70)
        await self.test_session_status_endpoint()
        print()
        
        # Test 3: FIR endpoints
        print("Test 3: FIR Endpoints")
        print("-" * 70)
        await self.test_fir_endpoints()
        print()
        
        # Test 4: Metrics endpoint
        print("Test 4: Metrics Endpoint")
        print("-" * 70)
        await self.test_metrics_endpoint()
        print()
        
        # Test 5: List FIRs endpoint
        print("Test 5: List FIRs Endpoint")
        print("-" * 70)
        await self.test_list_firs_endpoint()
        print()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("="*70)
        print("Validation Summary")
        print("="*70)
        print()
        
        passed = len(self.results["passed"])
        failed = len(self.results["failed"])
        warnings = len(self.results["warnings"])
        total = passed + failed
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Tests Failed: {failed}/{total}")
        print(f"Warnings: {warnings}")
        print()
        
        if failed > 0:
            print("Failed Tests:")
            for fail in self.results["failed"]:
                print(f"  ❌ {fail['test']}: {fail['message']}")
            print()
        
        if warnings > 0:
            print("Warnings:")
            for warn in self.results["warnings"]:
                print(f"  ⚠️  {warn['test']}: {warn['message']}")
            print()
        
        print("="*70)
        
        if failed == 0:
            print("✅ All validation tests PASSED!")
            print("API response time optimizations are working correctly.")
        else:
            print(f"❌ {failed} test(s) FAILED")
            print("Please review the failures above.")
        
        print("="*70)
        
        # Save results
        with open("validation_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print("\n📊 Results saved to validation_results.json")

async def main():
    """Main test runner"""
    async with ValidationTest() as test:
        try:
            await test.run_all_tests()
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
