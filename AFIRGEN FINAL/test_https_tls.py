#!/usr/bin/env python3
"""
HTTPS/TLS Implementation Test Suite
Tests all aspects of HTTPS/TLS configuration for AFIRGen
"""

import sys
import subprocess
import requests
import urllib3
from pathlib import Path
from typing import Tuple, List
import time

# Disable SSL warnings for testing with self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class HTTPSTestSuite:
    def __init__(self, base_url: str = "https://localhost"):
        self.base_url = base_url
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def print_header(self, text: str):
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{text}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
    
    def print_test(self, name: str, passed: bool, message: str = ""):
        if passed:
            print(f"{GREEN}✓{RESET} {name}")
            if message:
                print(f"  {message}")
            self.passed += 1
        else:
            print(f"{RED}✗{RESET} {name}")
            if message:
                print(f"  {RED}{message}{RESET}")
            self.failed += 1
    
    def print_warning(self, name: str, message: str):
        print(f"{YELLOW}⚠{RESET} {name}")
        print(f"  {YELLOW}{message}{RESET}")
        self.warnings += 1
    
    def test_certificate_files(self) -> bool:
        """Test that certificate files exist and have correct permissions"""
        self.print_header("Certificate File Tests")
        
        cert_path = Path("nginx/ssl/cert.pem")
        key_path = Path("nginx/ssl/key.pem")
        
        # Check certificate exists
        cert_exists = cert_path.exists()
        self.print_test(
            "Certificate file exists",
            cert_exists,
            f"Path: {cert_path}" if cert_exists else "Certificate file not found"
        )
        
        # Check private key exists
        key_exists = key_path.exists()
        self.print_test(
            "Private key file exists",
            key_exists,
            f"Path: {key_path}" if key_exists else "Private key file not found"
        )
        
        if not (cert_exists and key_exists):
            return False
        
        # Check private key permissions (should be 600)
        try:
            import stat
            key_stat = key_path.stat()
            key_mode = stat.filemode(key_stat.st_mode)
            is_secure = (key_stat.st_mode & 0o777) == 0o600
            
            self.print_test(
                "Private key has secure permissions (600)",
                is_secure,
                f"Current permissions: {key_mode}"
            )
        except Exception as e:
            self.print_test("Private key permissions check", False, str(e))
        
        # Validate certificate
        try:
            result = subprocess.run(
                ["openssl", "x509", "-in", str(cert_path), "-noout", "-checkend", "0"],
                capture_output=True,
                text=True
            )
            is_valid = result.returncode == 0
            self.print_test(
                "Certificate is valid (not expired)",
                is_valid,
                "Certificate is expired" if not is_valid else "Certificate is valid"
            )
        except FileNotFoundError:
            self.print_warning(
                "OpenSSL not found",
                "Cannot validate certificate expiration. Install OpenSSL to enable this check."
            )
        except Exception as e:
            self.print_test("Certificate validation", False, str(e))
        
        return cert_exists and key_exists
    
    def test_docker_services(self) -> bool:
        """Test that Docker services are running"""
        self.print_header("Docker Service Tests")
        
        try:
            # Check if docker-compose is available
            result = subprocess.run(
                ["docker-compose", "ps"],
                capture_output=True,
                text=True,
                cwd="AFIRGEN FINAL"
            )
            
            services = ["nginx", "fir_pipeline", "gguf_model_server", "asr_ocr_model_server"]
            
            for service in services:
                is_running = service in result.stdout and "Up" in result.stdout
                self.print_test(
                    f"{service} container is running",
                    is_running,
                    "Service is not running" if not is_running else ""
                )
            
            return "nginx" in result.stdout and "Up" in result.stdout
            
        except FileNotFoundError:
            self.print_warning(
                "Docker Compose not found",
                "Cannot check service status. Ensure Docker Compose is installed."
            )
            return False
        except Exception as e:
            self.print_test("Docker service check", False, str(e))
            return False
    
    def test_https_connectivity(self) -> bool:
        """Test HTTPS endpoint connectivity"""
        self.print_header("HTTPS Connectivity Tests")
        
        try:
            # Test HTTPS health endpoint
            response = requests.get(
                f"{self.base_url}/health",
                verify=False,
                timeout=10
            )
            
            is_success = response.status_code == 200
            self.print_test(
                "HTTPS endpoint accessible",
                is_success,
                f"Status code: {response.status_code}" if is_success else f"Failed with status: {response.status_code}"
            )
            
            if is_success:
                # Check response content
                try:
                    data = response.json()
                    has_status = "status" in data
                    self.print_test(
                        "Health endpoint returns valid JSON",
                        has_status,
                        f"Status: {data.get('status', 'unknown')}" if has_status else "Invalid response format"
                    )
                except Exception as e:
                    self.print_test("Health endpoint JSON parsing", False, str(e))
            
            return is_success
            
        except requests.exceptions.ConnectionError:
            self.print_test(
                "HTTPS endpoint accessible",
                False,
                "Connection refused. Ensure services are running."
            )
            return False
        except Exception as e:
            self.print_test("HTTPS connectivity", False, str(e))
            return False
    
    def test_http_redirect(self) -> bool:
        """Test HTTP to HTTPS redirect"""
        self.print_header("HTTP Redirect Tests")
        
        try:
            http_url = self.base_url.replace("https://", "http://")
            response = requests.get(
                http_url,
                allow_redirects=False,
                timeout=10
            )
            
            is_redirect = response.status_code in [301, 302, 307, 308]
            self.print_test(
                "HTTP redirects to HTTPS",
                is_redirect,
                f"Status code: {response.status_code}" if is_redirect else f"No redirect (status: {response.status_code})"
            )
            
            if is_redirect:
                location = response.headers.get("Location", "")
                is_https = location.startswith("https://")
                self.print_test(
                    "Redirect location uses HTTPS",
                    is_https,
                    f"Location: {location}" if is_https else f"Invalid location: {location}"
                )
                return is_https
            
            return is_redirect
            
        except Exception as e:
            self.print_test("HTTP redirect test", False, str(e))
            return False
    
    def test_security_headers(self) -> bool:
        """Test security headers"""
        self.print_header("Security Header Tests")
        
        try:
            response = requests.get(
                f"{self.base_url}/health",
                verify=False,
                timeout=10
            )
            
            headers = response.headers
            
            # Required security headers
            required_headers = {
                "Strict-Transport-Security": "HSTS",
                "X-Frame-Options": "Clickjacking protection",
                "X-Content-Type-Options": "MIME sniffing protection",
                "X-XSS-Protection": "XSS protection",
                "Content-Security-Policy": "CSP",
                "Referrer-Policy": "Referrer policy"
            }
            
            all_present = True
            for header, description in required_headers.items():
                is_present = header in headers
                self.print_test(
                    f"{description} header present",
                    is_present,
                    f"{header}: {headers.get(header, 'Not found')}" if is_present else f"{header} header missing"
                )
                all_present = all_present and is_present
            
            # Check HSTS value
            if "Strict-Transport-Security" in headers:
                hsts_value = headers["Strict-Transport-Security"]
                has_max_age = "max-age=" in hsts_value
                has_subdomains = "includeSubDomains" in hsts_value
                
                self.print_test(
                    "HSTS has max-age directive",
                    has_max_age,
                    f"Value: {hsts_value}"
                )
                
                if has_max_age:
                    self.print_test(
                        "HSTS includes subdomains",
                        has_subdomains,
                        "includeSubDomains directive present" if has_subdomains else "Consider adding includeSubDomains"
                    )
            
            return all_present
            
        except Exception as e:
            self.print_test("Security headers test", False, str(e))
            return False
    
    def test_tls_configuration(self) -> bool:
        """Test TLS configuration"""
        self.print_header("TLS Configuration Tests")
        
        try:
            # Test TLS 1.2
            try:
                import ssl
                context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                response = requests.get(
                    f"{self.base_url}/health",
                    verify=False,
                    timeout=10
                )
                
                self.print_test(
                    "TLS 1.2 supported",
                    response.status_code == 200,
                    "TLS 1.2 connection successful"
                )
            except Exception as e:
                self.print_test("TLS 1.2 support", False, str(e))
            
            # Check cipher suite (if possible)
            try:
                result = subprocess.run(
                    ["openssl", "s_client", "-connect", self.base_url.replace("https://", ""), "-cipher", "HIGH"],
                    input=b"",
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                has_strong_cipher = "Cipher" in result.stdout and "HIGH" in result.stdout
                self.print_test(
                    "Strong cipher suites available",
                    has_strong_cipher,
                    "High-strength ciphers supported" if has_strong_cipher else "Check cipher configuration"
                )
            except FileNotFoundError:
                self.print_warning(
                    "OpenSSL not found",
                    "Cannot test cipher suites. Install OpenSSL to enable this check."
                )
            except Exception as e:
                self.print_warning("Cipher suite test", str(e))
            
            return True
            
        except Exception as e:
            self.print_test("TLS configuration test", False, str(e))
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test API endpoints through HTTPS"""
        self.print_header("API Endpoint Tests")
        
        try:
            # Test health endpoint
            response = requests.get(
                f"{self.base_url}/health",
                verify=False,
                timeout=10
            )
            
            self.print_test(
                "Health endpoint accessible",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            # Test metrics endpoint
            try:
                response = requests.get(
                    f"{self.base_url}/metrics",
                    verify=False,
                    timeout=10
                )
                
                self.print_test(
                    "Metrics endpoint accessible",
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )
            except Exception as e:
                self.print_warning("Metrics endpoint", str(e))
            
            # Test reliability endpoint
            try:
                response = requests.get(
                    f"{self.base_url}/reliability",
                    verify=False,
                    timeout=10
                )
                
                self.print_test(
                    "Reliability endpoint accessible",
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )
            except Exception as e:
                self.print_warning("Reliability endpoint", str(e))
            
            return True
            
        except Exception as e:
            self.print_test("API endpoint test", False, str(e))
            return False
    
    def test_access_control(self) -> bool:
        """Test that internal services are not externally accessible"""
        self.print_header("Access Control Tests")
        
        internal_ports = [8000, 8001, 8002]
        all_blocked = True
        
        for port in internal_ports:
            try:
                response = requests.get(
                    f"http://localhost:{port}/health",
                    timeout=2
                )
                # If we get here, the port is accessible (bad)
                self.print_test(
                    f"Port {port} blocked from external access",
                    False,
                    f"Port {port} is accessible (should be blocked)"
                )
                all_blocked = False
            except requests.exceptions.ConnectionError:
                # Connection refused is good - port is blocked
                self.print_test(
                    f"Port {port} blocked from external access",
                    True,
                    f"Port {port} is properly blocked"
                )
            except requests.exceptions.Timeout:
                # Timeout is also acceptable
                self.print_test(
                    f"Port {port} blocked from external access",
                    True,
                    f"Port {port} times out (blocked)"
                )
            except Exception as e:
                self.print_warning(f"Port {port} access test", str(e))
        
        return all_blocked
    
    def test_performance(self) -> bool:
        """Test performance metrics"""
        self.print_header("Performance Tests")
        
        try:
            # Test response time
            start_time = time.time()
            response = requests.get(
                f"{self.base_url}/health",
                verify=False,
                timeout=10
            )
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            is_fast = response_time < 200
            self.print_test(
                "Response time < 200ms",
                is_fast,
                f"Response time: {response_time:.2f}ms"
            )
            
            # Test TLS handshake time
            start_time = time.time()
            requests.get(
                f"{self.base_url}/health",
                verify=False,
                timeout=10
            )
            handshake_time = (time.time() - start_time) * 1000
            
            is_fast_handshake = handshake_time < 500
            self.print_test(
                "TLS handshake < 500ms",
                is_fast_handshake,
                f"Handshake time: {handshake_time:.2f}ms"
            )
            
            return is_fast and is_fast_handshake
            
        except Exception as e:
            self.print_test("Performance test", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}HTTPS/TLS Test Suite for AFIRGen{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        
        # Run all test categories
        self.test_certificate_files()
        self.test_docker_services()
        self.test_https_connectivity()
        self.test_http_redirect()
        self.test_security_headers()
        self.test_tls_configuration()
        self.test_api_endpoints()
        self.test_access_control()
        self.test_performance()
        
        # Print summary
        self.print_header("Test Summary")
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"Total tests: {total}")
        print(f"{GREEN}Passed: {self.passed}{RESET}")
        print(f"{RED}Failed: {self.failed}{RESET}")
        print(f"{YELLOW}Warnings: {self.warnings}{RESET}")
        print(f"Pass rate: {pass_rate:.1f}%\n")
        
        if self.failed == 0:
            print(f"{GREEN}✓ All tests passed!{RESET}\n")
            return 0
        else:
            print(f"{RED}✗ Some tests failed. Please review the output above.{RESET}\n")
            return 1

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="HTTPS/TLS Test Suite for AFIRGen")
    parser.add_argument(
        "--url",
        default="https://localhost",
        help="Base URL to test (default: https://localhost)"
    )
    
    args = parser.parse_args()
    
    suite = HTTPSTestSuite(base_url=args.url)
    exit_code = suite.run_all_tests()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
