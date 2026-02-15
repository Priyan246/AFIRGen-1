#!/usr/bin/env python3
"""
Performance Test for FIR Generation
Tests that FIR generation completes in under 30 seconds
"""

import asyncio
import time
import httpx
import json
from typing import Dict, Any, Optional

# Configuration
MAIN_BACKEND_URL = "http://localhost:8000"
TEST_TIMEOUT = 35  # Slightly more than 30s to account for network overhead

# Test data
TEST_TEXT = """
I want to report a theft that occurred yesterday at Central Park. 
Around 3 PM, I was sitting on a bench near the fountain when someone 
approached me and snatched my bag containing my wallet, phone, and 
important documents. The person was wearing a black hoodie and ran 
towards the north exit. I tried to chase them but lost sight. 
My phone had all my banking apps and personal photos. I'm very 
concerned about identity theft. There were a few witnesses who 
saw the incident. I would like to file a formal complaint.
"""

class PerformanceTest:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TEST_TIMEOUT)
        self.results = {
            "total_time": 0,
            "steps": {},
            "success": False,
            "error": None
        }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def check_health(self) -> bool:
        """Check if all services are healthy"""
        try:
            resp = await self.client.get(f"{MAIN_BACKEND_URL}/health")
            resp.raise_for_status()
            health = resp.json()
            
            print(f"Health Status: {health.get('status')}")
            print(f"  Model Server: {health.get('model_server', {}).get('status')}")
            print(f"  ASR/OCR Server: {health.get('asr_ocr_server', {}).get('status')}")
            
            return health.get("status") in ["healthy", "degraded"]
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    async def process_text(self) -> Optional[str]:
        """Start FIR processing with text input"""
        start_time = time.time()
        
        try:
            resp = await self.client.post(
                f"{MAIN_BACKEND_URL}/process",
                data={"text": TEST_TEXT}
            )
            resp.raise_for_status()
            result = resp.json()
            
            elapsed = time.time() - start_time
            self.results["steps"]["process"] = elapsed
            
            if not result.get("success"):
                raise RuntimeError(f"Process failed: {result.get('error')}")
            
            print(f"✅ Process step completed in {elapsed:.2f}s")
            return result.get("session_id")
            
        except Exception as e:
            print(f"❌ Process step failed: {e}")
            self.results["error"] = str(e)
            return None
    
    async def validate_step(self, session_id: str, step_name: str) -> Optional[Dict[str, Any]]:
        """Validate a single step"""
        start_time = time.time()
        
        try:
            resp = await self.client.post(
                f"{MAIN_BACKEND_URL}/validate",
                json={
                    "session_id": session_id,
                    "approved": True,
                    "user_input": None,
                    "regenerate": False
                }
            )
            resp.raise_for_status()
            result = resp.json()
            
            elapsed = time.time() - start_time
            self.results["steps"][step_name] = elapsed
            
            if not result.get("success"):
                raise RuntimeError(f"Validation failed: {result}")
            
            print(f"✅ {step_name} completed in {elapsed:.2f}s")
            return result
            
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            self.results["error"] = str(e)
            return None
    
    async def run_full_workflow(self) -> bool:
        """Run complete FIR generation workflow"""
        print("\n" + "="*60)
        print("FIR Generation Performance Test")
        print("="*60)
        
        # Check health first
        print("\n1. Checking service health...")
        if not await self.check_health():
            print("❌ Services not healthy - aborting test")
            return False
        
        # Start timer
        workflow_start = time.time()
        
        # Step 1: Process text
        print("\n2. Starting FIR processing...")
        session_id = await self.process_text()
        if not session_id:
            return False
        
        # Step 2: Validate transcript (approve immediately)
        print("\n3. Validating transcript...")
        result = await self.validate_step(session_id, "transcript_validation")
        if not result:
            return False
        
        # Step 3: Validate summary
        print("\n4. Validating summary...")
        result = await self.validate_step(session_id, "summary_validation")
        if not result:
            return False
        
        # Step 4: Validate violations
        print("\n5. Validating violations...")
        result = await self.validate_step(session_id, "violations_validation")
        if not result:
            return False
        
        # Step 5: Validate FIR narrative
        print("\n6. Validating FIR narrative...")
        result = await self.validate_step(session_id, "narrative_validation")
        if not result:
            return False
        
        # Step 6: Final review
        print("\n7. Final review...")
        result = await self.validate_step(session_id, "final_review")
        if not result:
            return False
        
        # Calculate total time
        total_time = time.time() - workflow_start
        self.results["total_time"] = total_time
        self.results["success"] = True
        
        # Print results
        print("\n" + "="*60)
        print("Performance Test Results")
        print("="*60)
        print(f"Total Time: {total_time:.2f}s")
        print(f"Target: 30.00s")
        print(f"Status: {'✅ PASS' if total_time < 30 else '❌ FAIL'}")
        print("\nStep Breakdown:")
        for step, duration in self.results["steps"].items():
            print(f"  {step:25s}: {duration:6.2f}s")
        print("="*60)
        
        if result and result.get("completed"):
            fir_number = result.get("content", {}).get("fir_number")
            if fir_number:
                print(f"\n✅ FIR Generated: {fir_number}")
        
        return total_time < 30
    
    async def run_concurrent_test(self, num_requests: int = 5) -> Dict[str, Any]:
        """Test concurrent request handling"""
        print("\n" + "="*60)
        print(f"Concurrent Load Test ({num_requests} requests)")
        print("="*60)
        
        async def single_request():
            start = time.time()
            session_id = await self.process_text()
            if session_id:
                # Just do first validation step
                await self.validate_step(session_id, "test")
            return time.time() - start
        
        start_time = time.time()
        results = await asyncio.gather(*[single_request() for _ in range(num_requests)])
        total_time = time.time() - start_time
        
        successful = [r for r in results if r is not None]
        
        print(f"\nResults:")
        print(f"  Total Time: {total_time:.2f}s")
        print(f"  Successful: {len(successful)}/{num_requests}")
        if successful:
            print(f"  Avg Time: {sum(successful)/len(successful):.2f}s")
            print(f"  Min Time: {min(successful):.2f}s")
            print(f"  Max Time: {max(successful):.2f}s")
        
        return {
            "total_time": total_time,
            "successful": len(successful),
            "total": num_requests,
            "times": successful
        }

async def main():
    """Main test runner"""
    async with PerformanceTest() as test:
        # Run full workflow test
        success = await test.run_full_workflow()
        
        if success:
            print("\n✅ Performance test PASSED - FIR generation under 30 seconds")
            
            # Optionally run concurrent test
            print("\n" + "="*60)
            response = input("Run concurrent load test? (y/n): ")
            if response.lower() == 'y':
                await test.run_concurrent_test(num_requests=5)
        else:
            print("\n❌ Performance test FAILED")
            if test.results.get("error"):
                print(f"Error: {test.results['error']}")
        
        # Save results to file
        with open("performance_test_results.json", "w") as f:
            json.dump(test.results, f, indent=2)
        print("\n📊 Results saved to performance_test_results.json")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
