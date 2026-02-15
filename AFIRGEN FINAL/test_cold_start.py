#!/usr/bin/env python3
"""
Cold Start Performance Test
Tests model loading time from scratch to ensure it's under 2 minutes
"""

import sys
import time
import asyncio
import httpx
import subprocess
import signal
from pathlib import Path

# Test configuration
MODEL_SERVER_PORT = 8001
ASR_OCR_SERVER_PORT = 8002
TIMEOUT = 180  # 3 minutes max wait
TARGET_TIME = 120  # 2 minutes target


class ServerProcess:
    """Manage server process lifecycle"""
    def __init__(self, name: str, script_path: str, port: int):
        self.name = name
        self.script_path = script_path
        self.port = port
        self.process = None
        self.start_time = None
        self.ready_time = None
    
    def start(self):
        """Start the server process"""
        print(f"\n{'='*60}")
        print(f"Starting {self.name}...")
        print(f"Script: {self.script_path}")
        print(f"Port: {self.port}")
        print(f"{'='*60}")
        
        self.start_time = time.time()
        
        # Start process
        self.process = subprocess.Popen(
            [sys.executable, self.script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        print(f"✅ Process started (PID: {self.process.pid})")
    
    async def wait_for_ready(self, timeout: int = TIMEOUT) -> bool:
        """Wait for server to be ready"""
        print(f"\nWaiting for {self.name} to be ready...")
        print(f"Checking health endpoint: http://localhost:{self.port}/health")
        
        start_wait = time.time()
        last_error = None
        
        async with httpx.AsyncClient() as client:
            while time.time() - start_wait < timeout:
                try:
                    resp = await client.get(
                        f"http://localhost:{self.port}/health",
                        timeout=5.0
                    )
                    
                    if resp.status_code == 200:
                        health_data = resp.json()
                        status = health_data.get("status", "unknown")
                        
                        # Accept healthy or degraded (some models loaded)
                        if status in ["healthy", "degraded"]:
                            self.ready_time = time.time()
                            elapsed = self.ready_time - self.start_time
                            
                            print(f"✅ {self.name} is ready!")
                            print(f"   Status: {status}")
                            print(f"   Message: {health_data.get('message', 'N/A')}")
                            print(f"   Cold start time: {elapsed:.2f} seconds")
                            
                            return True
                        else:
                            last_error = f"Status: {status}"
                    else:
                        last_error = f"HTTP {resp.status_code}"
                
                except httpx.ConnectError:
                    last_error = "Connection refused"
                except httpx.TimeoutException:
                    last_error = "Timeout"
                except Exception as e:
                    last_error = str(e)
                
                # Show progress
                elapsed = time.time() - start_wait
                print(f"   Waiting... ({elapsed:.1f}s) - Last error: {last_error}", end='\r')
                
                await asyncio.sleep(2)
        
        print(f"\n❌ {self.name} failed to become ready within {timeout}s")
        print(f"   Last error: {last_error}")
        return False
    
    def stop(self):
        """Stop the server process"""
        if self.process:
            print(f"\nStopping {self.name}...")
            try:
                self.process.send_signal(signal.SIGTERM)
                self.process.wait(timeout=10)
                print(f"✅ {self.name} stopped")
            except subprocess.TimeoutExpired:
                print(f"⚠️  Force killing {self.name}...")
                self.process.kill()
                self.process.wait()
            except Exception as e:
                print(f"⚠️  Error stopping {self.name}: {e}")
    
    def get_cold_start_time(self) -> float:
        """Get cold start time in seconds"""
        if self.start_time and self.ready_time:
            return self.ready_time - self.start_time
        return 0.0


async def test_cold_start():
    """Test cold start performance"""
    print("\n" + "="*60)
    print("AFIRGen Cold Start Performance Test")
    print("="*60)
    print(f"Target: Model loading under {TARGET_TIME} seconds")
    print(f"Timeout: {TIMEOUT} seconds")
    print("="*60)
    
    # Define servers
    servers = [
        ServerProcess(
            "GGUF Model Server",
            "AFIRGEN FINAL/gguf model server/llm_server.py",
            MODEL_SERVER_PORT
        ),
        ServerProcess(
            "ASR/OCR Server",
            "AFIRGEN FINAL/asr ocr model server/asr_ocr.py",
            ASR_OCR_SERVER_PORT
        )
    ]
    
    try:
        # Start all servers
        for server in servers:
            server.start()
        
        # Wait for all servers to be ready
        results = {}
        for server in servers:
            results[server.name] = await server.wait_for_ready()
        
        # Calculate total cold start time (max of all servers)
        cold_start_times = {
            server.name: server.get_cold_start_time()
            for server in servers
            if server.ready_time
        }
        
        # Print summary
        print("\n" + "="*60)
        print("Cold Start Performance Summary")
        print("="*60)
        
        for server_name, ready in results.items():
            status = "✅ READY" if ready else "❌ FAILED"
            cold_start = cold_start_times.get(server_name, 0)
            print(f"{server_name:25s}: {status}")
            if ready:
                print(f"  Cold start time: {cold_start:.2f}s")
        
        print("="*60)
        
        # Overall result
        if all(results.values()):
            max_cold_start = max(cold_start_times.values())
            print(f"\n✅ All servers started successfully")
            print(f"Maximum cold start time: {max_cold_start:.2f} seconds")
            
            if max_cold_start <= TARGET_TIME:
                print(f"✅ PASSED: Cold start time is under {TARGET_TIME} seconds!")
                return 0
            else:
                print(f"❌ FAILED: Cold start time exceeds {TARGET_TIME} seconds")
                print(f"   Exceeded by: {max_cold_start - TARGET_TIME:.2f} seconds")
                return 1
        else:
            print(f"\n❌ Some servers failed to start")
            return 1
    
    finally:
        # Cleanup - stop all servers
        print("\n" + "="*60)
        print("Cleanup")
        print("="*60)
        for server in servers:
            server.stop()


def main():
    """Main entry point"""
    try:
        exit_code = asyncio.run(test_cold_start())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
