#!/usr/bin/env python3
"""
Test script to validate model loading with proper error handling
Tests the enhanced model loading validation features
"""

import sys
import asyncio
import httpx
from pathlib import Path

# Test configuration
MODEL_SERVER_URL = "http://localhost:8001"
ASR_OCR_SERVER_URL = "http://localhost:8002"
TIMEOUT = 10.0


async def test_server_health(server_url: str, server_name: str) -> bool:
    """Test if a server is healthy"""
    print(f"\n{'='*60}")
    print(f"Testing {server_name} Health Check")
    print(f"URL: {server_url}/health")
    print(f"{'='*60}")
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(f"{server_url}/health")
            resp.raise_for_status()
            health_data = resp.json()
            
            print(f"✅ Server responded successfully")
            print(f"Status: {health_data.get('status', 'unknown')}")
            print(f"Message: {health_data.get('message', 'No message')}")
            
            if 'models_loaded' in health_data:
                print(f"\nModel Status:")
                for model, loaded in health_data['models_loaded'].items():
                    status = "✅ LOADED" if loaded else "❌ FAILED"
                    print(f"  {model:20s}: {status}")
            
            if 'models' in health_data:
                print(f"\nModel Status:")
                for model, loaded in health_data['models'].items():
                    status = "✅ LOADED" if loaded else "❌ FAILED"
                    print(f"  {model:20s}: {status}")
            
            return health_data.get('status') in ['healthy', 'degraded']
            
    except httpx.ConnectError as e:
        print(f"❌ Connection failed: {e}")
        print(f"   Is the server running at {server_url}?")
        return False
    except httpx.TimeoutException:
        print(f"❌ Request timed out after {TIMEOUT}s")
        return False
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def test_model_inference(model_name: str = "summariser") -> bool:
    """Test model inference with validation"""
    print(f"\n{'='*60}")
    print(f"Testing Model Inference")
    print(f"Model: {model_name}")
    print(f"{'='*60}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model_name": model_name,
                "prompt": "Test prompt for validation",
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            print(f"Sending inference request...")
            resp = await client.post(f"{MODEL_SERVER_URL}/inference", json=payload)
            resp.raise_for_status()
            result = resp.json()
            
            print(f"✅ Inference successful")
            print(f"Result: {result.get('result', 'No result')[:100]}...")
            return True
            
    except httpx.ConnectError as e:
        print(f"❌ Connection failed: {e}")
        return False
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def test_invalid_model() -> bool:
    """Test error handling for invalid model name"""
    print(f"\n{'='*60}")
    print(f"Testing Invalid Model Error Handling")
    print(f"{'='*60}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "model_name": "nonexistent_model",
                "prompt": "Test",
                "max_tokens": 10
            }
            
            print(f"Requesting non-existent model...")
            resp = await client.post(f"{MODEL_SERVER_URL}/inference", json=payload)
            
            if resp.status_code == 400:
                print(f"✅ Server correctly rejected invalid model (400)")
                print(f"   Error message: {resp.json().get('detail', 'No detail')}")
                return True
            elif resp.status_code == 500:
                print(f"✅ Server returned error for unavailable model (500)")
                print(f"   Error message: {resp.json().get('detail', 'No detail')}")
                return True
            else:
                print(f"⚠️  Unexpected status code: {resp.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AFIRGen Model Loading Validation Tests")
    print("="*60)
    
    results = {}
    
    # Test Model Server
    results['model_server_health'] = await test_server_health(
        MODEL_SERVER_URL, "GGUF Model Server"
    )
    
    # Test ASR/OCR Server
    results['asr_ocr_health'] = await test_server_health(
        ASR_OCR_SERVER_URL, "ASR/OCR Server"
    )
    
    # Only test inference if model server is healthy
    if results['model_server_health']:
        results['model_inference'] = await test_model_inference()
        results['invalid_model_handling'] = await test_invalid_model()
    else:
        print("\n⚠️  Skipping inference tests - model server not healthy")
        results['model_inference'] = None
        results['invalid_model_handling'] = None
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, result in results.items():
        if result is None:
            status = "⊘ SKIPPED"
        elif result:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"{test_name:30s}: {status}")
    
    print("="*60)
    
    # Determine overall result
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed > 0:
        print("\n⚠️  Some tests failed. Check server logs for details.")
        return 1
    elif passed == 0:
        print("\n⚠️  No tests passed. Servers may not be running.")
        return 1
    else:
        print("\n✅ All tests passed!")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
