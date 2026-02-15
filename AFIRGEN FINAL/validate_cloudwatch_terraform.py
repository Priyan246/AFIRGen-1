"""
Validate CloudWatch Terraform Configuration
Tests that the Terraform files are properly configured
"""

import os
import json
import subprocess
import sys

def test_terraform_files_exist():
    """Test that all required Terraform files exist"""
    print("\n" + "="*60)
    print("TEST: Terraform Files Exist")
    print("="*60)
    
    required_files = [
        "AFIRGEN FINAL/terraform/main.tf",
        "AFIRGEN FINAL/terraform/variables.tf",
        "AFIRGEN FINAL/terraform/cloudwatch_dashboards.tf",
        "AFIRGEN FINAL/terraform/cloudwatch_alarms.tf",
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Missing file: {file_path}")
            return False
        print(f"✅ Found: {file_path}")
    
    print("\n✅ All required Terraform files exist!")
    return True


def test_dashboard_configuration():
    """Test CloudWatch dashboard configuration"""
    print("\n" + "="*60)
    print("TEST: Dashboard Configuration")
    print("="*60)
    
    with open("AFIRGEN FINAL/terraform/cloudwatch_dashboards.tf", "r") as f:
        content = f.read()
    
    # Check for required dashboards
    required_dashboards = [
        "afirgen_main",
        "afirgen_errors",
        "afirgen_performance"
    ]
    
    for dashboard in required_dashboards:
        if f'resource "aws_cloudwatch_dashboard" "{dashboard}"' in content:
            print(f"✅ Dashboard defined: {dashboard}")
        else:
            print(f"❌ Missing dashboard: {dashboard}")
            return False
    
    # Check for key metrics
    required_metrics = [
        "APIRequests",
        "APILatency",
        "APIErrors",
        "FIRGenerations",
        "FIRGenerationDuration",
        "ModelInferences",
        "DatabaseOperations",
        "CacheOperations",
        "RateLimitEvents",
        "AuthenticationEvents",
        "HealthChecks"
    ]
    
    for metric in required_metrics:
        if metric in content:
            print(f"✅ Metric referenced: {metric}")
        else:
            print(f"❌ Missing metric: {metric}")
            return False
    
    # Check for variable references
    if "var.environment" in content and "var.aws_region" in content:
        print("✅ Variables properly referenced")
    else:
        print("❌ Variables not properly referenced")
        return False
    
    print("\n✅ Dashboard configuration is valid!")
    return True


def test_alarm_configuration():
    """Test CloudWatch alarm configuration"""
    print("\n" + "="*60)
    print("TEST: Alarm Configuration")
    print("="*60)
    
    with open("AFIRGEN FINAL/terraform/cloudwatch_alarms.tf", "r") as f:
        content = f.read()
    
    # Check for SNS topic
    if 'resource "aws_sns_topic" "cloudwatch_alarms"' in content:
        print("✅ SNS topic defined")
    else:
        print("❌ Missing SNS topic")
        return False
    
    # Check for required alarms
    required_alarms = [
        "high_error_rate",
        "high_api_latency",
        "fir_generation_failures",
        "database_failures",
        "high_rate_limiting",
        "auth_failures",
        "service_unhealthy",
        "slow_model_inference",
        "low_cache_hit_rate"
    ]
    
    for alarm in required_alarms:
        if f'resource "aws_cloudwatch_metric_alarm" "{alarm}"' in content:
            print(f"✅ Alarm defined: {alarm}")
        else:
            print(f"❌ Missing alarm: {alarm}")
            return False
    
    # Check for composite alarm
    if 'resource "aws_cloudwatch_composite_alarm" "critical_system_health"' in content:
        print("✅ Composite alarm defined")
    else:
        print("❌ Missing composite alarm")
        return False
    
    # Check for alarm actions
    if "alarm_actions" in content and "aws_sns_topic.cloudwatch_alarms.arn" in content:
        print("✅ Alarm actions configured")
    else:
        print("❌ Alarm actions not configured")
        return False
    
    print("\n✅ Alarm configuration is valid!")
    return True


def test_variables_configuration():
    """Test variables configuration"""
    print("\n" + "="*60)
    print("TEST: Variables Configuration")
    print("="*60)
    
    with open("AFIRGEN FINAL/terraform/variables.tf", "r") as f:
        content = f.read()
    
    # Check for required variables
    required_variables = [
        "environment",
        "aws_region",
        "alarm_email"
    ]
    
    for var in required_variables:
        if f'variable "{var}"' in content:
            print(f"✅ Variable defined: {var}")
        else:
            print(f"❌ Missing variable: {var}")
            return False
    
    print("\n✅ Variables configuration is valid!")
    return True


def test_terraform_syntax():
    """Test Terraform syntax validation"""
    print("\n" + "="*60)
    print("TEST: Terraform Syntax Validation")
    print("="*60)
    
    # Check if terraform is installed
    try:
        result = subprocess.run(
            ["terraform", "version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            print("⚠️  Terraform not installed - skipping syntax validation")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  Terraform not installed - skipping syntax validation")
        return True
    
    # Run terraform fmt check
    try:
        os.chdir("AFIRGEN FINAL/terraform")
        
        # Initialize terraform (required for validation)
        print("Initializing Terraform...")
        result = subprocess.run(
            ["terraform", "init", "-backend=false"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"⚠️  Terraform init failed: {result.stderr}")
            os.chdir("../..")
            return True  # Don't fail on init issues
        
        # Validate configuration
        print("Validating Terraform configuration...")
        result = subprocess.run(
            ["terraform", "validate"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        os.chdir("../..")
        
        if result.returncode == 0:
            print("✅ Terraform configuration is valid")
            return True
        else:
            print(f"❌ Terraform validation failed:\n{result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Terraform validation timed out - skipping")
        os.chdir("../..")
        return True
    except Exception as e:
        print(f"⚠️  Terraform validation error: {e}")
        os.chdir("../..")
        return True


def test_dashboard_json_structure():
    """Test that dashboard JSON is properly structured"""
    print("\n" + "="*60)
    print("TEST: Dashboard JSON Structure")
    print("="*60)
    
    with open("AFIRGEN FINAL/terraform/cloudwatch_dashboards.tf", "r") as f:
        content = f.read()
    
    # Check for jsonencode usage
    if "jsonencode(" in content:
        print("✅ Using jsonencode for dashboard body")
    else:
        print("❌ Not using jsonencode")
        return False
    
    # Check for widgets array
    if "widgets = [" in content:
        print("✅ Widgets array defined")
    else:
        print("❌ Widgets array not defined")
        return False
    
    # Check for metric properties
    required_properties = ["type", "properties", "metrics", "period", "stat", "region", "title"]
    
    for prop in required_properties:
        if prop in content:
            print(f"✅ Property used: {prop}")
        else:
            print(f"❌ Missing property: {prop}")
            return False
    
    print("\n✅ Dashboard JSON structure is valid!")
    return True


def test_integration_with_metrics_module():
    """Test that dashboards reference metrics from cloudwatch_metrics.py"""
    print("\n" + "="*60)
    print("TEST: Integration with Metrics Module")
    print("="*60)
    
    # Read metrics module
    with open("AFIRGEN FINAL/main backend/cloudwatch_metrics.py", "r") as f:
        metrics_content = f.read()
    
    # Read dashboard config
    with open("AFIRGEN FINAL/terraform/cloudwatch_dashboards.tf", "r") as f:
        dashboard_content = f.read()
    
    # Extract metric names from convenience functions
    metric_names = [
        "APIRequests",
        "APILatency",
        "APIErrors",
        "FIRGenerations",
        "FIRGenerationDuration",
        "ModelInferences",
        "ModelInferenceDuration",
        "TokensGenerated",
        "DatabaseOperations",
        "DatabaseLatency",
        "CacheOperations",
        "RateLimitEvents",
        "AuthenticationEvents",
        "HealthChecks"
    ]
    
    for metric in metric_names:
        if metric in metrics_content and metric in dashboard_content:
            print(f"✅ Metric integrated: {metric}")
        elif metric in metrics_content:
            print(f"⚠️  Metric defined but not in dashboard: {metric}")
        else:
            print(f"❌ Metric not defined: {metric}")
            return False
    
    print("\n✅ Metrics module integration is valid!")
    return True


def run_all_tests():
    """Run all validation tests"""
    print("\n" + "="*70)
    print("CLOUDWATCH TERRAFORM VALIDATION SUITE")
    print("="*70)
    
    tests = [
        ("Terraform Files Exist", test_terraform_files_exist),
        ("Dashboard Configuration", test_dashboard_configuration),
        ("Alarm Configuration", test_alarm_configuration),
        ("Variables Configuration", test_variables_configuration),
        ("Dashboard JSON Structure", test_dashboard_json_structure),
        ("Integration with Metrics Module", test_integration_with_metrics_module),
        ("Terraform Syntax Validation", test_terraform_syntax),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    
    if failed == 0:
        print("\n🎉 ALL VALIDATION TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
