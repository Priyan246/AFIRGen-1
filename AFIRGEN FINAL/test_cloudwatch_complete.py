"""
Complete CloudWatch Implementation Test
Verifies all components of the CloudWatch implementation
"""

import os
import sys
import subprocess

def run_test_suite(test_file, description):
    """Run a test suite and return results"""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print('='*70)
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"❌ Test timed out: {test_file}")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False


def check_file_exists(file_path, description):
    """Check if a file exists"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ Missing {description}: {file_path}")
        return False


def main():
    """Run complete CloudWatch implementation verification"""
    print("\n" + "="*70)
    print("CLOUDWATCH COMPLETE IMPLEMENTATION TEST")
    print("="*70)
    
    results = {
        "files": 0,
        "tests": 0,
        "total_files": 0,
        "total_tests": 0
    }
    
    # Check core files
    print("\n" + "="*70)
    print("CHECKING CORE FILES")
    print("="*70)
    
    core_files = [
        ("AFIRGEN FINAL/main backend/cloudwatch_metrics.py", "CloudWatch Metrics Module"),
        ("AFIRGEN FINAL/terraform/cloudwatch_dashboards.tf", "Dashboard Terraform Config"),
        ("AFIRGEN FINAL/terraform/cloudwatch_alarms.tf", "Alarms Terraform Config"),
        ("AFIRGEN FINAL/terraform/variables.tf", "Terraform Variables"),
    ]
    
    for file_path, description in core_files:
        results["total_files"] += 1
        if check_file_exists(file_path, description):
            results["files"] += 1
    
    # Check documentation files
    print("\n" + "="*70)
    print("CHECKING DOCUMENTATION FILES")
    print("="*70)
    
    doc_files = [
        ("AFIRGEN FINAL/CLOUDWATCH-DASHBOARDS-IMPLEMENTATION.md", "Implementation Guide"),
        ("AFIRGEN FINAL/CLOUDWATCH-DASHBOARDS-QUICK-REFERENCE.md", "Quick Reference"),
        ("AFIRGEN FINAL/CLOUDWATCH-DASHBOARDS-SUMMARY.md", "Summary"),
        ("AFIRGEN FINAL/CLOUDWATCH-DEPLOYMENT-CHECKLIST.md", "Deployment Checklist"),
        ("AFIRGEN FINAL/CLOUDWATCH-README.md", "README"),
    ]
    
    for file_path, description in doc_files:
        results["total_files"] += 1
        if check_file_exists(file_path, description):
            results["files"] += 1
    
    # Check test files
    print("\n" + "="*70)
    print("CHECKING TEST FILES")
    print("="*70)
    
    test_files = [
        ("AFIRGEN FINAL/test_cloudwatch_metrics.py", "Metrics Test Suite"),
        ("AFIRGEN FINAL/validate_cloudwatch_terraform.py", "Terraform Validation"),
    ]
    
    for file_path, description in test_files:
        results["total_files"] += 1
        if check_file_exists(file_path, description):
            results["files"] += 1
    
    # Run test suites
    print("\n" + "="*70)
    print("RUNNING TEST SUITES")
    print("="*70)
    
    test_suites = [
        ("AFIRGEN FINAL/test_cloudwatch_metrics.py", "CloudWatch Metrics Tests"),
        ("AFIRGEN FINAL/validate_cloudwatch_terraform.py", "Terraform Validation Tests"),
    ]
    
    for test_file, description in test_suites:
        results["total_tests"] += 1
        if run_test_suite(test_file, description):
            results["tests"] += 1
    
    # Check integration
    print("\n" + "="*70)
    print("CHECKING APPLICATION INTEGRATION")
    print("="*70)
    
    try:
        with open("AFIRGEN FINAL/main backend/agentv5.py", "r") as f:
            content = f.read()
            
        integration_checks = [
            ("from cloudwatch_metrics import", "CloudWatch metrics import"),
            ("record_api_request", "API request recording"),
            ("record_rate_limit_event", "Rate limit event recording"),
            ("record_auth_event", "Auth event recording"),
            ("record_health_check", "Health check recording"),
        ]
        
        integration_ok = True
        for check, description in integration_checks:
            if check in content:
                print(f"✅ {description} integrated")
            else:
                print(f"❌ {description} not found")
                integration_ok = False
        
        if integration_ok:
            print("\n✅ Application integration complete")
        else:
            print("\n❌ Application integration incomplete")
            
    except Exception as e:
        print(f"❌ Error checking integration: {e}")
        integration_ok = False
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Files: {results['files']}/{results['total_files']} ✅")
    print(f"Test Suites: {results['tests']}/{results['total_tests']} ✅")
    print(f"Integration: {'✅' if integration_ok else '❌'}")
    
    all_passed = (
        results['files'] == results['total_files'] and
        results['tests'] == results['total_tests'] and
        integration_ok
    )
    
    if all_passed:
        print("\n" + "="*70)
        print("🎉 ALL CHECKS PASSED - CLOUDWATCH IMPLEMENTATION COMPLETE!")
        print("="*70)
        print("\nNext Steps:")
        print("1. Deploy infrastructure: cd terraform && terraform apply")
        print("2. Confirm SNS subscription via email")
        print("3. Deploy application with ENVIRONMENT=production")
        print("4. View dashboards in AWS Console")
        print("\nDocumentation:")
        print("- Implementation Guide: CLOUDWATCH-DASHBOARDS-IMPLEMENTATION.md")
        print("- Quick Reference: CLOUDWATCH-DASHBOARDS-QUICK-REFERENCE.md")
        print("- Deployment Checklist: CLOUDWATCH-DEPLOYMENT-CHECKLIST.md")
        return 0
    else:
        print("\n" + "="*70)
        print("⚠️  SOME CHECKS FAILED")
        print("="*70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
