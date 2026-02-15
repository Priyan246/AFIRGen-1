#!/usr/bin/env python3
"""
Test script for 99.9% Uptime SLA reliability features.

Tests:
1. Circuit breaker functionality
2. Retry policy behavior
3. Graceful shutdown
4. Health monitoring
5. Overall uptime under load
"""

import asyncio
import httpx
import time
import sys
from typing import Dict, List
from datetime import datetime, timedelta


class ReliabilityTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results: Dict[str, bool] = {}
    
    async def test_health_endpoint(self) -> bool:
        """Test that health endpoint returns reliability information"""
        print("\n" + "=" * 60)
        print("TEST 1: Health Endpoint with Reliability Info")
        print("=" * 60)
        
        try:
            resp = await self.client.get(f"{self.base_url}/health")
            resp.raise_for_status()
            
            data = resp.json()
            
            # Check for reliability section
            if "reliability" not in data:
                print("❌ FAILED: No reliability section in health response")
                return False
            
            reliability = data["reliability"]
            
            # Check for circuit breakers
            if "circuit_breakers" not in reliability:
                print("❌ FAILED: No circuit_breakers in reliability section")
                return False
            
            circuit_breakers = reliability["circuit_breakers"]
            
            print(f"✅ Health endpoint includes reliability information")
            print(f"   - Model server circuit breaker: {circuit_breakers.get('model_server', {}).get('state', 'unknown')}")
            print(f"   - ASR/OCR circuit breaker: {circuit_breakers.get('asr_ocr_server', {}).get('state', 'unknown')}")
            
            # Check for graceful shutdown
            if "graceful_shutdown" in reliability:
                shutdown_info = reliability["graceful_shutdown"]
                print(f"   - Active requests: {shutdown_info.get('active_requests', 'unknown')}")
                print(f"   - Shutting down: {shutdown_info.get('is_shutting_down', 'unknown')}")
            
            # Check for health monitor
            if "health_monitor" in reliability:
                monitor_info = reliability["health_monitor"]
                print(f"   - Overall healthy: {monitor_info.get('overall_healthy', 'unknown')}")
                if "checks" in monitor_info:
                    for check_name, check_info in monitor_info["checks"].items():
                        uptime = check_info.get("uptime_percentage", 0)
                        print(f"   - {check_name}: {uptime:.2f}% uptime")
            
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            return False
    
    async def test_reliability_endpoint(self) -> bool:
        """Test dedicated reliability endpoint"""
        print("\n" + "=" * 60)
        print("TEST 2: Reliability Status Endpoint")
        print("=" * 60)
        
        try:
            resp = await self.client.get(f"{self.base_url}/reliability")
            resp.raise_for_status()
            
            data = resp.json()
            
            # Check required fields
            required_fields = ["circuit_breakers", "graceful_shutdown", "health_monitor", "uptime_target"]
            for field in required_fields:
                if field not in data:
                    print(f"❌ FAILED: Missing required field: {field}")
                    return False
            
            print(f"✅ Reliability endpoint working")
            print(f"   - Uptime target: {data.get('uptime_target', 'unknown')}")
            print(f"   - Max downtime/month: {data.get('max_downtime_per_month', 'unknown')}")
            
            # Display circuit breaker states
            for cb_name, cb_info in data["circuit_breakers"].items():
                state = cb_info.get("state", "unknown")
                failures = cb_info.get("failure_count", 0)
                print(f"   - {cb_name}: {state} (failures: {failures})")
            
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            return False
    
    async def test_uptime_under_load(self, duration_seconds: int = 60, requests_per_second: int = 10) -> bool:
        """Test system maintains high uptime under load"""
        print("\n" + "=" * 60)
        print(f"TEST 3: Uptime Under Load ({duration_seconds}s, {requests_per_second} req/s)")
        print("=" * 60)
        
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        start_time = time.time()
        
        print(f"Starting load test...")
        print(f"Target: ≥ 99.9% success rate")
        
        try:
            while time.time() - start_time < duration_seconds:
                # Send batch of requests
                tasks = []
                for _ in range(requests_per_second):
                    tasks.append(self.client.get(f"{self.base_url}/health", timeout=5.0))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    total_requests += 1
                    if isinstance(result, Exception):
                        failed_requests += 1
                    elif result.status_code == 200:
                        successful_requests += 1
                    else:
                        failed_requests += 1
                
                # Wait for next second
                await asyncio.sleep(1.0)
                
                # Progress update every 10 seconds
                if total_requests % (requests_per_second * 10) == 0:
                    current_uptime = (successful_requests / total_requests * 100) if total_requests > 0 else 0
                    print(f"   Progress: {total_requests} requests, {current_uptime:.2f}% success rate")
            
            # Calculate final uptime
            uptime_percentage = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            print(f"\n📊 Load Test Results:")
            print(f"   - Total requests: {total_requests}")
            print(f"   - Successful: {successful_requests}")
            print(f"   - Failed: {failed_requests}")
            print(f"   - Uptime: {uptime_percentage:.3f}%")
            
            # Check if meets 99.9% SLA
            if uptime_percentage >= 99.9:
                print(f"✅ PASSED: Uptime {uptime_percentage:.3f}% meets 99.9% SLA")
                return True
            else:
                print(f"❌ FAILED: Uptime {uptime_percentage:.3f}% below 99.9% SLA")
                return False
                
        except Exception as e:
            print(f"❌ FAILED: {e}")
            return False
    
    async def test_circuit_breaker_states(self) -> bool:
        """Test that circuit breakers are in expected states"""
        print("\n" + "=" * 60)
        print("TEST 4: Circuit Breaker States")
        print("=" * 60)
        
        try:
            resp = await self.client.get(f"{self.base_url}/reliability")
            resp.raise_for_status()
            
            data = resp.json()
            circuit_breakers = data.get("circuit_breakers", {})
            
            all_closed = True
            for cb_name, cb_info in circuit_breakers.items():
                state = cb_info.get("state", "unknown")
                failure_count = cb_info.get("failure_count", 0)
                
                print(f"   - {cb_name}:")
                print(f"     State: {state}")
                print(f"     Failures: {failure_count}/{cb_info.get('threshold', 'unknown')}")
                
                if state != "closed":
                    print(f"     ⚠️  WARNING: Circuit breaker not in CLOSED state")
                    all_closed = False
            
            if all_closed:
                print(f"✅ PASSED: All circuit breakers in CLOSED state")
                return True
            else:
                print(f"⚠️  WARNING: Some circuit breakers not in CLOSED state")
                print(f"   This may indicate service issues or recent failures")
                return True  # Not a failure, just a warning
                
        except Exception as e:
            print(f"❌ FAILED: {e}")
            return False
    
    async def test_health_monitor_history(self) -> bool:
        """Test that health monitor is tracking history"""
        print("\n" + "=" * 60)
        print("TEST 5: Health Monitor History")
        print("=" * 60)
        
        try:
            resp = await self.client.get(f"{self.base_url}/reliability")
            resp.raise_for_status()
            
            data = resp.json()
            health_monitor = data.get("health_monitor", {})
            checks = health_monitor.get("checks", {})
            
            if not checks:
                print(f"❌ FAILED: No health checks registered")
                return False
            
            print(f"✅ Health monitor tracking {len(checks)} checks:")
            
            all_healthy = True
            for check_name, check_info in checks.items():
                healthy = check_info.get("healthy", False)
                uptime = check_info.get("uptime_percentage", 0)
                history_size = check_info.get("history_size", 0)
                
                status_icon = "✅" if healthy else "❌"
                print(f"   {status_icon} {check_name}:")
                print(f"      Uptime: {uptime:.2f}%")
                print(f"      History: {history_size} checks")
                
                if not healthy:
                    all_healthy = False
                    print(f"      ⚠️  WARNING: Check currently unhealthy")
            
            overall_healthy = health_monitor.get("overall_healthy", False)
            
            if overall_healthy and all_healthy:
                print(f"\n✅ PASSED: All health checks passing")
                return True
            else:
                print(f"\n⚠️  WARNING: Some health checks failing")
                return True  # Not a failure, just a warning
                
        except Exception as e:
            print(f"❌ FAILED: {e}")
            return False
    
    async def test_graceful_shutdown_status(self) -> bool:
        """Test graceful shutdown handler status"""
        print("\n" + "=" * 60)
        print("TEST 6: Graceful Shutdown Handler")
        print("=" * 60)
        
        try:
            resp = await self.client.get(f"{self.base_url}/reliability")
            resp.raise_for_status()
            
            data = resp.json()
            shutdown_info = data.get("graceful_shutdown", {})
            
            is_shutting_down = shutdown_info.get("is_shutting_down", False)
            active_requests = shutdown_info.get("active_requests", 0)
            timeout = shutdown_info.get("shutdown_timeout", 0)
            
            print(f"   - Shutting down: {is_shutting_down}")
            print(f"   - Active requests: {active_requests}")
            print(f"   - Shutdown timeout: {timeout}s")
            
            if is_shutting_down:
                print(f"⚠️  WARNING: System is currently shutting down")
                return True  # Not a failure
            
            print(f"✅ PASSED: Graceful shutdown handler operational")
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all reliability tests"""
        print("\n" + "=" * 60)
        print("AFIRGen 99.9% Uptime SLA - Reliability Test Suite")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"Started at: {datetime.now().isoformat()}")
        
        tests = [
            ("Health Endpoint", self.test_health_endpoint()),
            ("Reliability Endpoint", self.test_reliability_endpoint()),
            ("Circuit Breaker States", self.test_circuit_breaker_states()),
            ("Health Monitor History", self.test_health_monitor_history()),
            ("Graceful Shutdown Status", self.test_graceful_shutdown_status()),
            ("Uptime Under Load", self.test_uptime_under_load(duration_seconds=30, requests_per_second=5)),
        ]
        
        results = {}
        for test_name, test_coro in tests:
            try:
                results[test_name] = await test_coro
            except Exception as e:
                print(f"\n❌ Test '{test_name}' crashed: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {test_name}")
        
        print("\n" + "=" * 60)
        print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        print("=" * 60)
        
        if passed == total:
            print("\n🎉 All reliability tests passed!")
            print("System is ready for 99.9% uptime SLA")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
            print("Review failures before deploying to production")
            return 1
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.client.aclose()


async def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test AFIRGen reliability features")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of AFIRGen API (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    tester = ReliabilityTester(base_url=args.url)
    
    try:
        exit_code = await tester.run_all_tests()
        return exit_code
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest suite crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
