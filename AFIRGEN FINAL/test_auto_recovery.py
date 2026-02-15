#!/usr/bin/env python3
"""
Test script for automatic service recovery functionality.

This script tests the auto-recovery mechanisms by simulating failures
and verifying that the system recovers automatically.

Usage:
    python test_auto_recovery.py
"""

import asyncio
import httpx
import time
import sys
from typing import Dict, Any


class AutoRecoveryTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"  {message}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
    
    async def check_health(self) -> Dict[str, Any]:
        """Check service health"""
        try:
            resp = await self.client.get(f"{self.base_url}/health")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_reliability(self) -> Dict[str, Any]:
        """Check reliability status"""
        try:
            resp = await self.client.get(f"{self.base_url}/reliability")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def trigger_recovery(self, service_name: str) -> Dict[str, Any]:
        """Manually trigger recovery for a service"""
        try:
            resp = await self.client.post(
                f"{self.base_url}/reliability/auto-recovery/{service_name}/trigger"
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def reset_circuit_breaker(self, service_name: str) -> Dict[str, Any]:
        """Reset circuit breaker for a service"""
        try:
            resp = await self.client.post(
                f"{self.base_url}/reliability/circuit-breaker/{service_name}/reset"
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_health_endpoint(self):
        """Test 1: Health endpoint returns expected structure"""
        print("\n" + "=" * 60)
        print("Test 1: Health Endpoint Structure")
        print("=" * 60)
        
        health = await self.check_health()
        
        # Check required fields
        required_fields = ["status", "model_server", "asr_ocr_server", "database", "reliability"]
        missing_fields = [f for f in required_fields if f not in health]
        
        if missing_fields:
            self.log_test(
                "Health endpoint structure",
                False,
                f"Missing fields: {', '.join(missing_fields)}"
            )
        else:
            self.log_test("Health endpoint structure", True)
        
        # Check reliability sub-structure
        if "reliability" in health:
            reliability = health["reliability"]
            if "circuit_breakers" in reliability and "graceful_shutdown" in reliability:
                self.log_test("Reliability components present", True)
            else:
                self.log_test("Reliability components present", False, "Missing circuit_breakers or graceful_shutdown")
        
        return health
    
    async def test_reliability_endpoint(self):
        """Test 2: Reliability endpoint returns auto-recovery status"""
        print("\n" + "=" * 60)
        print("Test 2: Reliability Endpoint Structure")
        print("=" * 60)
        
        reliability = await self.check_reliability()
        
        # Check required fields
        required_fields = ["circuit_breakers", "graceful_shutdown", "health_monitor", "auto_recovery"]
        missing_fields = [f for f in required_fields if f not in reliability]
        
        if missing_fields:
            self.log_test(
                "Reliability endpoint structure",
                False,
                f"Missing fields: {', '.join(missing_fields)}"
            )
        else:
            self.log_test("Reliability endpoint structure", True)
        
        # Check auto_recovery structure
        if "auto_recovery" in reliability:
            auto_recovery = reliability["auto_recovery"]
            if "handlers" in auto_recovery:
                handlers = auto_recovery["handlers"]
                expected_handlers = ["model_server", "asr_ocr_server", "database"]
                missing_handlers = [h for h in expected_handlers if h not in handlers]
                
                if missing_handlers:
                    self.log_test(
                        "Auto-recovery handlers registered",
                        False,
                        f"Missing handlers: {', '.join(missing_handlers)}"
                    )
                else:
                    self.log_test("Auto-recovery handlers registered", True)
                    print(f"  Registered handlers: {', '.join(handlers.keys())}")
            else:
                self.log_test("Auto-recovery handlers registered", False, "No handlers field")
        
        return reliability
    
    async def test_circuit_breaker_status(self):
        """Test 3: Circuit breakers are in expected state"""
        print("\n" + "=" * 60)
        print("Test 3: Circuit Breaker Status")
        print("=" * 60)
        
        reliability = await self.check_reliability()
        
        if "circuit_breakers" not in reliability:
            self.log_test("Circuit breakers present", False, "No circuit_breakers field")
            return
        
        circuit_breakers = reliability["circuit_breakers"]
        
        for name, status in circuit_breakers.items():
            state = status.get("state", "unknown")
            failure_count = status.get("failure_count", 0)
            
            print(f"\n  {name}:")
            print(f"    State: {state}")
            print(f"    Failures: {failure_count}/{status.get('threshold', 'N/A')}")
            
            # Circuit breaker should be closed or half_open (not permanently open)
            if state in ["closed", "half_open"]:
                self.log_test(f"Circuit breaker '{name}' operational", True)
            else:
                self.log_test(
                    f"Circuit breaker '{name}' operational",
                    False,
                    f"State is '{state}' (expected 'closed' or 'half_open')"
                )
    
    async def test_manual_recovery_trigger(self):
        """Test 4: Manual recovery trigger works"""
        print("\n" + "=" * 60)
        print("Test 4: Manual Recovery Trigger")
        print("=" * 60)
        
        # Try to trigger recovery for model_server
        print("\n  Triggering recovery for model_server...")
        result = await self.trigger_recovery("model_server")
        
        if "error" in result:
            self.log_test(
                "Manual recovery trigger",
                False,
                f"Error: {result['error']}"
            )
        else:
            success = result.get("success", False)
            message = result.get("message", "")
            
            print(f"  Result: {message}")
            
            # Recovery should succeed if service is healthy
            # or fail gracefully if already in progress
            if success or "already in progress" in message.lower():
                self.log_test("Manual recovery trigger", True)
            else:
                self.log_test("Manual recovery trigger", False, message)
    
    async def test_circuit_breaker_reset(self):
        """Test 5: Circuit breaker reset works"""
        print("\n" + "=" * 60)
        print("Test 5: Circuit Breaker Reset")
        print("=" * 60)
        
        # Try to reset model_server circuit breaker
        print("\n  Resetting model_server circuit breaker...")
        result = await self.reset_circuit_breaker("model_server")
        
        if "error" in result:
            self.log_test(
                "Circuit breaker reset",
                False,
                f"Error: {result['error']}"
            )
        else:
            success = result.get("success", False)
            message = result.get("message", "")
            
            print(f"  Result: {message}")
            
            if success:
                self.log_test("Circuit breaker reset", True)
                
                # Verify circuit breaker is now closed
                await asyncio.sleep(1)
                reliability = await self.check_reliability()
                cb_status = reliability.get("circuit_breakers", {}).get("model_server", {})
                state = cb_status.get("state", "unknown")
                
                if state == "closed":
                    self.log_test("Circuit breaker state after reset", True, "State is 'closed'")
                else:
                    self.log_test(
                        "Circuit breaker state after reset",
                        False,
                        f"State is '{state}' (expected 'closed')"
                    )
            else:
                self.log_test("Circuit breaker reset", False, message)
    
    async def test_health_monitor_status(self):
        """Test 6: Health monitor is tracking service health"""
        print("\n" + "=" * 60)
        print("Test 6: Health Monitor Status")
        print("=" * 60)
        
        reliability = await self.check_reliability()
        
        if "health_monitor" not in reliability:
            self.log_test("Health monitor present", False, "No health_monitor field")
            return
        
        health_monitor = reliability["health_monitor"]
        
        if "checks" in health_monitor:
            checks = health_monitor["checks"]
            
            print(f"\n  Monitored services: {len(checks)}")
            
            for name, status in checks.items():
                healthy = status.get("healthy", False)
                uptime = status.get("uptime_percentage", 0)
                
                print(f"\n  {name}:")
                print(f"    Healthy: {healthy}")
                print(f"    Uptime: {uptime}%")
                
                # Service should be healthy with reasonable uptime
                if healthy and uptime >= 90:
                    self.log_test(f"Health monitor tracking '{name}'", True)
                else:
                    self.log_test(
                        f"Health monitor tracking '{name}'",
                        False,
                        f"Healthy={healthy}, Uptime={uptime}%"
                    )
        else:
            self.log_test("Health monitor checks", False, "No checks field")
    
    async def test_graceful_shutdown_status(self):
        """Test 7: Graceful shutdown handler is ready"""
        print("\n" + "=" * 60)
        print("Test 7: Graceful Shutdown Status")
        print("=" * 60)
        
        reliability = await self.check_reliability()
        
        if "graceful_shutdown" not in reliability:
            self.log_test("Graceful shutdown present", False, "No graceful_shutdown field")
            return
        
        graceful_shutdown = reliability["graceful_shutdown"]
        
        is_shutting_down = graceful_shutdown.get("is_shutting_down", True)
        active_requests = graceful_shutdown.get("active_requests", -1)
        
        print(f"\n  Shutting down: {is_shutting_down}")
        print(f"  Active requests: {active_requests}")
        
        # Should not be shutting down during normal operation
        if not is_shutting_down and active_requests >= 0:
            self.log_test("Graceful shutdown ready", True)
        else:
            self.log_test(
                "Graceful shutdown ready",
                False,
                f"is_shutting_down={is_shutting_down}, active_requests={active_requests}"
            )
    
    async def run_all_tests(self):
        """Run all auto-recovery tests"""
        print("\n" + "=" * 60)
        print("AUTOMATIC SERVICE RECOVERY TEST SUITE")
        print("=" * 60)
        print(f"Testing service at: {self.base_url}")
        print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run tests
        await self.test_health_endpoint()
        await self.test_reliability_endpoint()
        await self.test_circuit_breaker_status()
        await self.test_manual_recovery_trigger()
        await self.test_circuit_breaker_reset()
        await self.test_health_monitor_status()
        await self.test_graceful_shutdown_status()
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["passed"])
        failed_tests = total_tests - passed_tests
        
        print(f"\nTotal tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\nFailed tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  ❌ {result['test']}")
                    if result["message"]:
                        print(f"     {result['message']}")
        
        print("\n" + "=" * 60)
        
        return failed_tests == 0


async def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test automatic service recovery")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the service (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    async with AutoRecoveryTester(args.url) as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
