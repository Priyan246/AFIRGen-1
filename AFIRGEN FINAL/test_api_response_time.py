#!/usr/bin/env python3
"""
API Response Time Test
Tests that non-model-inference API endpoints respond in <200ms
"""

import asyncio
import time
import httpx
import json
import statistics
from typing import Dict, List, Tuple

# Configuration
MAIN_BACKEND_URL = "http://localhost:8000"
NUM_ITERATIONS = 10  # Number of times to test each endpoint
TARGET_RESPONSE_TIME = 0.200  # 200ms in seconds

class APIResponseTimeTest:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=5.0)
        self.results = {}
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def measure_endpoint(self, method: str, url: str, name: str, **kwargs) -> List[float]:
        """Measure response time for an endpoint multiple times"""
        times = []
        
        for i in range(NUM_ITERATIONS):
            start = time.perf_counter()
            try:
                if method.upper() == "GET":
                    resp = await self.client.get(url, **kwargs)
                elif method.upper() == "POST":
                    resp = await self.client.post(url, **kwargs)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                resp.raise_for_status()
                elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
                times.append(elapsed)
                
                # Small delay between requests
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"  ❌ Request {i+1} failed: {e}")
                continue
        
        return times
    
    async def test_health_endpoint(self) -> Dict:
        """Test /health endpoint"""
        print("\n📊 Testing /health endpoint...")
        times = await self.measure_endpoint("GET", f"{MAIN_BACKEND_URL}/health", "health")
        return self.analyze_results("GET /health", times)
    
    async def test_session_status(self, session_id: str) -> Dict:
        """Test /session/{session_id}/status endpoint"""
        print(f"\n📊 Testing /session/{{session_id}}/status endpoint...")
        times = await self.measure_endpoint(
            "GET", 
            f"{MAIN_BACKEND_URL}/session/{session_id}/status",
            "session_status"
        )
        return self.analyze_results("GET /session/{id}/status", times)
    
    async def test_fir_status(self, fir_number: str) -> Dict:
        """Test /fir/{fir_number} endpoint"""
        print(f"\n📊 Testing /fir/{{fir_number}} endpoint...")
        times = await self.measure_endpoint(
            "GET",
            f"{MAIN_BACKEND_URL}/fir/{fir_number}",
            "fir_status"
        )
        return self.analyze_results("GET /fir/{number}", times)
    
    async def test_metrics_endpoint(self) -> Dict:
        """Test /metrics endpoint"""
        print("\n📊 Testing /metrics endpoint...")
        times = await self.measure_endpoint("GET", f"{MAIN_BACKEND_URL}/metrics", "metrics")
        return self.analyze_results("GET /metrics", times)
    
    async def test_list_firs(self) -> Dict:
        """Test /list_firs endpoint"""
        print("\n📊 Testing /list_firs endpoint...")
        times = await self.measure_endpoint("GET", f"{MAIN_BACKEND_URL}/list_firs", "list_firs")
        return self.analyze_results("GET /list_firs", times)
    
    def analyze_results(self, endpoint: str, times: List[float]) -> Dict:
        """Analyze timing results"""
        if not times:
            return {
                "endpoint": endpoint,
                "success": False,
                "error": "No successful requests"
            }
        
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        p95_time = sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0]
        p99_time = sorted(times)[int(len(times) * 0.99)] if len(times) > 1 else times[0]
        
        target_ms = TARGET_RESPONSE_TIME * 1000
        passed = avg_time < target_ms
        
        result = {
            "endpoint": endpoint,
            "success": True,
            "passed": passed,
            "target_ms": target_ms,
            "avg_ms": round(avg_time, 2),
            "median_ms": round(median_time, 2),
            "min_ms": round(min_time, 2),
            "max_ms": round(max_time, 2),
            "p95_ms": round(p95_time, 2),
            "p99_ms": round(p99_time, 2),
            "samples": len(times)
        }
        
        # Print results
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {endpoint}")
        print(f"    Avg: {result['avg_ms']:.2f}ms | Median: {result['median_ms']:.2f}ms")
        print(f"    Min: {result['min_ms']:.2f}ms | Max: {result['max_ms']:.2f}ms")
        print(f"    P95: {result['p95_ms']:.2f}ms | P99: {result['p99_ms']:.2f}ms")
        print(f"    Target: {target_ms:.2f}ms")
        
        self.results[endpoint] = result
        return result
    
    async def create_test_session(self) -> Tuple[str, str]:
        """Create a test session and FIR for testing"""
        print("\n🔧 Creating test session and FIR...")
        
        # Create session
        resp = await self.client.post(
            f"{MAIN_BACKEND_URL}/process",
            data={"text": "Test complaint for API response time testing"}
        )
        resp.raise_for_status()
        result = resp.json()
        session_id = result.get("session_id")
        
        # Complete workflow to get FIR number
        for _ in range(5):  # 5 validation steps
            resp = await self.client.post(
                f"{MAIN_BACKEND_URL}/validate",
                json={"session_id": session_id, "approved": True}
            )
            resp.raise_for_status()
            result = resp.json()
            
            if result.get("completed"):
                fir_number = result.get("content", {}).get("fir_number")
                print(f"  ✅ Created session: {session_id}")
                print(f"  ✅ Created FIR: {fir_number}")
                return session_id, fir_number
        
        raise RuntimeError("Failed to create test FIR")
    
    async def run_all_tests(self):
        """Run all API response time tests"""
        print("="*70)
        print("API Response Time Test Suite")
        print("="*70)
        print(f"Target: <{TARGET_RESPONSE_TIME*1000:.0f}ms per request")
        print(f"Iterations per endpoint: {NUM_ITERATIONS}")
        
        # Test health endpoint (doesn't need setup)
        await self.test_health_endpoint()
        
        # Test metrics endpoint
        await self.test_metrics_endpoint()
        
        # Test list_firs endpoint
        await self.test_list_firs()
        
        # Create test data for other endpoints
        try:
            session_id, fir_number = await self.create_test_session()
            
            # Test session status
            await self.test_session_status(session_id)
            
            # Test FIR status
            await self.test_fir_status(fir_number)
            
        except Exception as e:
            print(f"\n⚠️  Could not create test data: {e}")
            print("  Skipping session and FIR status tests")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("Test Summary")
        print("="*70)
        
        passed = sum(1 for r in self.results.values() if r.get("passed", False))
        total = len(self.results)
        
        print(f"\nEndpoints Tested: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        
        print("\nDetailed Results:")
        print(f"{'Endpoint':<30} {'Avg (ms)':<12} {'P95 (ms)':<12} {'Status':<10}")
        print("-"*70)
        
        for endpoint, result in self.results.items():
            if result.get("success"):
                status = "✅ PASS" if result["passed"] else "❌ FAIL"
                print(f"{endpoint:<30} {result['avg_ms']:<12.2f} {result['p95_ms']:<12.2f} {status:<10}")
        
        print("="*70)
        
        if passed == total:
            print("\n✅ All API endpoints meet <200ms response time target!")
        else:
            print(f"\n⚠️  {total - passed} endpoint(s) need optimization")
        
        # Save results
        with open("api_response_time_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print("\n📊 Results saved to api_response_time_results.json")

async def main():
    """Main test runner"""
    async with APIResponseTimeTest() as test:
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
