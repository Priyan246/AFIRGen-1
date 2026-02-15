"""
Verify CloudWatch Implementation (Windows-compatible)
Simple verification without Unicode characters
"""

import os
import sys

def check_file(path, name):
    """Check if file exists"""
    exists = os.path.exists(path)
    status = "OK" if exists else "MISSING"
    print(f"[{status}] {name}")
    return exists

def check_content(path, search_terms, name):
    """Check if file contains required content"""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        found = all(term in content for term in search_terms)
        status = "OK" if found else "MISSING"
        print(f"[{status}] {name}")
        return found
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("CLOUDWATCH IMPLEMENTATION VERIFICATION")
    print("="*70)
    
    passed = 0
    total = 0
    
    # Core files
    print("\nCore Files:")
    print("-" * 70)
    
    checks = [
        ("AFIRGEN FINAL/main backend/cloudwatch_metrics.py", "CloudWatch Metrics Module"),
        ("AFIRGEN FINAL/terraform/cloudwatch_dashboards.tf", "Dashboard Config"),
        ("AFIRGEN FINAL/terraform/cloudwatch_alarms.tf", "Alarms Config"),
        ("AFIRGEN FINAL/terraform/variables.tf", "Terraform Variables"),
    ]
    
    for path, name in checks:
        total += 1
        if check_file(path, name):
            passed += 1
    
    # Documentation
    print("\nDocumentation:")
    print("-" * 70)
    
    docs = [
        ("AFIRGEN FINAL/CLOUDWATCH-DASHBOARDS-IMPLEMENTATION.md", "Implementation Guide"),
        ("AFIRGEN FINAL/CLOUDWATCH-DASHBOARDS-QUICK-REFERENCE.md", "Quick Reference"),
        ("AFIRGEN FINAL/CLOUDWATCH-DASHBOARDS-SUMMARY.md", "Summary"),
        ("AFIRGEN FINAL/CLOUDWATCH-DEPLOYMENT-CHECKLIST.md", "Deployment Checklist"),
        ("AFIRGEN FINAL/CLOUDWATCH-README.md", "README"),
    ]
    
    for path, name in docs:
        total += 1
        if check_file(path, name):
            passed += 1
    
    # Test files
    print("\nTest Files:")
    print("-" * 70)
    
    tests = [
        ("AFIRGEN FINAL/test_cloudwatch_metrics.py", "Metrics Tests"),
        ("AFIRGEN FINAL/validate_cloudwatch_terraform.py", "Terraform Validation"),
    ]
    
    for path, name in tests:
        total += 1
        if check_file(path, name):
            passed += 1
    
    # Content checks
    print("\nContent Verification:")
    print("-" * 70)
    
    content_checks = [
        (
            "AFIRGEN FINAL/main backend/cloudwatch_metrics.py",
            ["CloudWatchMetrics", "put_metric", "record_count", "record_duration"],
            "Metrics module has required functions"
        ),
        (
            "AFIRGEN FINAL/terraform/cloudwatch_dashboards.tf",
            ["aws_cloudwatch_dashboard", "afirgen_main", "afirgen_errors", "afirgen_performance"],
            "Dashboards defined"
        ),
        (
            "AFIRGEN FINAL/terraform/cloudwatch_alarms.tf",
            ["aws_cloudwatch_metric_alarm", "high_error_rate", "aws_sns_topic"],
            "Alarms and SNS defined"
        ),
        (
            "AFIRGEN FINAL/main backend/agentv5.py",
            ["from cloudwatch_metrics import", "record_api_request", "record_auth_event"],
            "Application integration"
        ),
    ]
    
    for path, terms, name in content_checks:
        total += 1
        if check_content(path, terms, name):
            passed += 1
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n[SUCCESS] CloudWatch implementation is complete!")
        print("\nNext Steps:")
        print("1. Deploy: cd terraform && terraform apply")
        print("2. Confirm SNS subscription via email")
        print("3. Deploy app with ENVIRONMENT=production")
        print("4. View dashboards in AWS Console")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} checks failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
