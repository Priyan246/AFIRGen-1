#!/usr/bin/env python3
"""
Concurrency Test for AFIRGen System
Tests that the system can handle 10 concurrent FIR generation requests
"""

import asyncio
import time
import httpx
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configuration
MAIN_BACKEND_URL = "http://localhost:8000"
TEST_TIMEOUT = 60  # 60 seconds for concurrent test
NUM_CONCURRENT_REQUESTS = 10

# Test data - different complaints for each request
TEST_COMPLAINTS = [
    "I want to report a theft at Central Park yesterday around 3 PM. Someone snatched my bag with wallet and phone.",
    "My car was broken into last night on Main Street. The window was smashed and my laptop was stolen.",
    "I witnessed an assault near the metro station this morning. A person was attacked by two individuals.",
    "My house was burglarized while I was at work. Electronics and jewelry were taken from the bedroom.",
    "I want to report a fraud case. Someone used my credit card details to make unauthorized purchases online.",
    "There was a hit and run accident on Highway 5. The driver fled the scene after hitting a pedestrian.",
    "I'm reporting harassment by my neighbor. They have been threatening me and my family for weeks.",
    "My bicycle was stolen from the parking lot of my apartment building last night.",
    "I want to file a complaint about vandalism. Someone spray-painted graffiti on my shop's wall.",
    "I'm reporting a case of identity theft. Someone opened bank accounts using my personal information."
]

class ConcurrencyTest:
    def __init__(self):
        self.results = {
            "test_start": None,
            "test_end": None,
            "total_duration": 0,
            "num_requests": NUM_CONCURRENT_REQUESTS,
            "successful": 0,
            "failed": 0,
            "request_details": [],
            "errors": []
        }
    
    async def check_health(self) -> bool:
        """Check if all services are healthy"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{MAIN_BACKEND_URL}/health")
                resp.raise_for_status()
                health = resp.json()
                
                print(f"\n{'='*60}")
                print("System Health Check")
                print(f"{'='*60}")
                print(f"Overall Status: {health.get('status')}")
                print(f"Model Server: {health.get('model_server', {}).get('status')}")
                print(f"ASR/OCR Server: {health.get('asr_ocr_server', {}).get('status')}")
                print(f"Database: {health.get('database')}")
                
                concurrency_config = health.get('concurrency', {})
                if concurrency_config:
                    print(f"\nConcurrency Configuration:")
                    print(f"  Max Concurrent Requests: {concurrency_config.get('max_concurrent_requests')}")
                    print(f"  Max Concurrent Model Calls: {concurrency_config.get('max_concurrent_model_calls')}")
                    print(f"  HTTP Pool Size: {concurrency_config.get('http_pool_size')}")
                
                print(f"{'='*60}\n")
                
                return health.get("status") in ["healthy", "degraded"]
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    async def process_single_request(self, request_id: int, complaint_text: str) -> Dict[str, Any]:
        """Process a single FIR generation request"""
        result = {
            "request_id": request_id,
            "start_time": None,
            "end_time": None,
            "duration": 0,
            "success": False,
            "session_id": None,
            "fir_number": None,
            "error": None,
            "steps_completed": 0
        }
        
        try:
            result["start_time"] = time.time()
            
            async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
                # Step 1: Process text
                resp = await client.post(
                    f"{MAIN_BACKEND_URL}/process",
                    data={"text": complaint_text}
                )
                resp.raise_for_status()
                process_result = resp.json()
                
                if not process_result.get("success"):
                    raise RuntimeError(f"Process failed: {process_result.get('error')}")
                
                session_id = process_result.get("session_id")
                result["session_id"] = session_id
                result["steps_completed"] = 1
                
                # Step 2-6: Validate all steps
                validation_steps = [
                    "transcript_validation",
                    "summary_validation",
                    "violations_validation",
                    "narrative_validation",
                    "final_review"
                ]
                
                for step_name in validation_steps:
                    resp = await client.post(
                        f"{MAIN_BACKEND_URL}/validate",
                        json={
                            "session_id": session_id,
                            "approved": True,
                            "user_input": None,
                            "regenerate": False
                        }
                    )
                    resp.raise_for_status()
                    validation_result = resp.json()
                    
                    if not validation_result.get("success"):
                        raise RuntimeError(f"Validation failed at {step_name}")
                    
                    result["steps_completed"] += 1
                    
                    # Check if completed
                    if validation_result.get("completed"):
                        fir_number = validation_result.get("content", {}).get("fir_number")
                        result["fir_number"] = fir_number
                        break
                
                result["success"] = True
                
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ Request {request_id} failed: {e}")
        
        finally:
            result["end_time"] = time.time()
            result["duration"] = result["end_time"] - result["start_time"]
        
        return result
    
    async def run_concurrent_test(self) -> bool:
        """Run concurrent FIR generation test"""
        print(f"\n{'='*60}")
        print(f"Concurrent Load Test - {NUM_CONCURRENT_REQUESTS} Requests")
        print(f"{'='*60}\n")
        
        # Check health first
        print("Checking system health...")
        if not await self.check_health():
            print("❌ System not healthy - aborting test")
            return False
        
        print(f"Starting {NUM_CONCURRENT_REQUESTS} concurrent FIR generation requests...\n")
        
        # Start timer
        self.results["test_start"] = time.time()
        
        # Create tasks for concurrent requests
        tasks = [
            self.process_single_request(i+1, TEST_COMPLAINTS[i])
            for i in range(NUM_CONCURRENT_REQUESTS)
        ]
        
        # Run all requests concurrently
        request_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # End timer
        self.results["test_end"] = time.time()
        self.results["total_duration"] = self.results["test_end"] - self.results["test_start"]
        
        # Process results
        for result in request_results:
            if isinstance(result, Exception):
                self.results["failed"] += 1
                self.results["errors"].append(str(result))
            elif isinstance(result, dict):
                self.results["request_details"].append(result)
                if result.get("success"):
                    self.results["successful"] += 1
                else:
                    self.results["failed"] += 1
                    if result.get("error"):
                        self.results["errors"].append(f"Request {result['request_id']}: {result['error']}")
        
        # Print results
        self.print_results()
        
        # Test passes if at least 10 requests succeeded
        return self.results["successful"] >= 10
    
    def print_results(self):
        """Print detailed test results"""
        print(f"\n{'='*60}")
        print("Concurrency Test Results")
        print(f"{'='*60}")
        print(f"Total Duration: {self.results['total_duration']:.2f}s")
        print(f"Requests: {self.results['num_requests']}")
        print(f"Successful: {self.results['successful']}")
        print(f"Failed: {self.results['failed']}")
        print(f"Success Rate: {(self.results['successful']/self.results['num_requests']*100):.1f}%")
        
        if self.results["request_details"]:
            durations = [r["duration"] for r in self.results["request_details"] if r.get("duration")]
            if durations:
                print(f"\nRequest Duration Statistics:")
                print(f"  Average: {sum(durations)/len(durations):.2f}s")
                print(f"  Min: {min(durations):.2f}s")
                print(f"  Max: {max(durations):.2f}s")
                print(f"  Median: {sorted(durations)[len(durations)//2]:.2f}s")
        
        print(f"\nDetailed Request Results:")
        print(f"{'ID':<4} {'Duration':<10} {'Steps':<7} {'Status':<10} {'FIR Number':<30}")
        print(f"{'-'*4} {'-'*10} {'-'*7} {'-'*10} {'-'*30}")
        
        for r in self.results["request_details"]:
            status = "✅ SUCCESS" if r.get("success") else "❌ FAILED"
            fir_num = r.get("fir_number", "N/A")[:28] if r.get("fir_number") else "N/A"
            print(f"{r['request_id']:<4} {r['duration']:>8.2f}s  {r['steps_completed']:<7} {status:<10} {fir_num:<30}")
        
        if self.results["errors"]:
            print(f"\nErrors:")
            for error in self.results["errors"][:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(self.results["errors"]) > 5:
                print(f"  ... and {len(self.results['errors']) - 5} more errors")
        
        print(f"{'='*60}")
        
        # Overall result
        if self.results["successful"] >= 10:
            print(f"\n✅ TEST PASSED - System handled {self.results['successful']} concurrent requests")
        else:
            print(f"\n❌ TEST FAILED - Only {self.results['successful']}/10 requests succeeded")
        
        print(f"{'='*60}\n")
    
    def save_results(self, filename: str = "concurrency_test_results.json"):
        """Save results to JSON file"""
        output = {
            **self.results,
            "test_timestamp": datetime.now().isoformat(),
            "test_config": {
                "backend_url": MAIN_BACKEND_URL,
                "num_concurrent_requests": NUM_CONCURRENT_REQUESTS,
                "timeout": TEST_TIMEOUT
            }
        }
        
        with open(filename, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"📊 Results saved to {filename}")

async def main():
    """Main test runner"""
    test = ConcurrencyTest()
    
    try:
        success = await test.run_concurrent_test()
        test.save_results()
        
        # Exit with appropriate code
        exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        test.save_results("concurrency_test_interrupted.json")
        exit(2)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        test.save_results("concurrency_test_error.json")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
