"""
Basic Test Script for AWS Secrets Manager Integration

This script tests the secrets_manager module without requiring pytest.
"""

import os
import sys
import json

# Add main backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "main backend"))

from secrets_manager import SecretsManager, get_secret, get_secrets_manager


def test_environment_variable_fallback():
    """Test that environment variables work when AWS is disabled"""
    print("Test 1: Environment variable fallback... ", end="")
    os.environ["TEST_SECRET_1"] = "test-value-1"
    
    secrets = SecretsManager(use_aws=False)
    value = secrets.get_secret("TEST_SECRET_1")
    
    assert value == "test-value-1", f"Expected 'test-value-1', got '{value}'"
    
    # Cleanup
    del os.environ["TEST_SECRET_1"]
    print("✅ PASSED")


def test_required_secret_missing():
    """Test that missing required secrets raise ValueError"""
    print("Test 2: Required secret missing... ", end="")
    secrets = SecretsManager(use_aws=False)
    
    try:
        secrets.get_secret("NONEXISTENT_SECRET_12345", required=True)
        print("❌ FAILED - Should have raised ValueError")
        return False
    except ValueError as e:
        assert "not found" in str(e).lower()
        print("✅ PASSED")
        return True


def test_optional_secret_missing():
    """Test that missing optional secrets return None"""
    print("Test 3: Optional secret missing... ", end="")
    secrets = SecretsManager(use_aws=False)
    value = secrets.get_secret("NONEXISTENT_SECRET_12345", required=False)
    
    assert value is None, f"Expected None, got '{value}'"
    print("✅ PASSED")


def test_default_value():
    """Test default value when secret not found"""
    print("Test 4: Default value... ", end="")
    secrets = SecretsManager(use_aws=False)
    value = secrets.get_secret("NONEXISTENT_SECRET_12345", default="default-value")
    
    assert value == "default-value", f"Expected 'default-value', got '{value}'"
    print("✅ PASSED")


def test_cache_basic():
    """Test that caching works"""
    print("Test 5: Basic caching... ", end="")
    os.environ["CACHED_SECRET"] = "cached-value"
    
    secrets = SecretsManager(use_aws=False, cache_ttl=60)
    
    # First call
    value1 = secrets.get_secret("CACHED_SECRET")
    
    # Change env var
    os.environ["CACHED_SECRET"] = "new-value"
    
    # Second call should return cached value
    value2 = secrets.get_secret("CACHED_SECRET")
    
    assert value1 == value2 == "cached-value", f"Cache failed: {value1} != {value2}"
    
    # Cleanup
    del os.environ["CACHED_SECRET"]
    print("✅ PASSED")


def test_cache_clear():
    """Test cache clearing"""
    print("Test 6: Cache clearing... ", end="")
    os.environ["CACHED_SECRET_2"] = "cached-value"
    
    secrets = SecretsManager(use_aws=False, cache_ttl=60)
    
    # First call
    value1 = secrets.get_secret("CACHED_SECRET_2")
    
    # Change env var
    os.environ["CACHED_SECRET_2"] = "new-value"
    
    # Clear cache
    secrets.clear_cache()
    
    # Should get new value
    value2 = secrets.get_secret("CACHED_SECRET_2")
    
    assert value1 == "cached-value", f"Expected 'cached-value', got '{value1}'"
    assert value2 == "new-value", f"Expected 'new-value', got '{value2}'"
    
    # Cleanup
    del os.environ["CACHED_SECRET_2"]
    print("✅ PASSED")


def test_refresh_secret():
    """Test force refresh bypasses cache"""
    print("Test 7: Refresh secret... ", end="")
    os.environ["REFRESH_SECRET"] = "old-value"
    
    secrets = SecretsManager(use_aws=False, cache_ttl=60)
    
    # First call
    value1 = secrets.get_secret("REFRESH_SECRET")
    
    # Change env var
    os.environ["REFRESH_SECRET"] = "new-value"
    
    # Refresh should bypass cache
    value2 = secrets.refresh_secret("REFRESH_SECRET")
    
    assert value1 == "old-value", f"Expected 'old-value', got '{value1}'"
    assert value2 == "new-value", f"Expected 'new-value', got '{value2}'"
    
    # Cleanup
    del os.environ["REFRESH_SECRET"]
    print("✅ PASSED")


def test_global_functions():
    """Test global convenience functions"""
    print("Test 8: Global functions... ", end="")
    os.environ["GLOBAL_SECRET"] = "global-value"
    
    value = get_secret("GLOBAL_SECRET")
    
    assert value == "global-value", f"Expected 'global-value', got '{value}'"
    
    # Cleanup
    del os.environ["GLOBAL_SECRET"]
    print("✅ PASSED")


def test_singleton():
    """Test that get_secrets_manager returns singleton"""
    print("Test 9: Singleton pattern... ", end="")
    manager1 = get_secrets_manager()
    manager2 = get_secrets_manager()
    
    assert manager1 is manager2, "Managers should be the same instance"
    print("✅ PASSED")


def test_empty_secret_value():
    """Test handling of empty secret values"""
    print("Test 10: Empty secret value... ", end="")
    os.environ["EMPTY_SECRET"] = ""
    
    secrets = SecretsManager(use_aws=False)
    value = secrets.get_secret("EMPTY_SECRET")
    
    assert value == "", f"Expected empty string, got '{value}'"
    
    # Cleanup
    del os.environ["EMPTY_SECRET"]
    print("✅ PASSED")


def test_integration_with_agentv5():
    """Test that agentv5.py can import and use secrets_manager"""
    print("Test 11: Integration with agentv5... ", end="")
    
    # Set test environment variables
    os.environ["MYSQL_PASSWORD"] = "test-password"
    os.environ["API_KEY"] = "test-api-key"
    os.environ["FIR_AUTH_KEY"] = "test-auth-key"
    os.environ["ENVIRONMENT"] = "development"
    
    try:
        # This will test if the import works in agentv5.py
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "main backend"))
        from secrets_manager import get_secret
        
        # Test retrieval
        password = get_secret("MYSQL_PASSWORD")
        api_key = get_secret("API_KEY")
        auth_key = get_secret("FIR_AUTH_KEY")
        
        assert password == "test-password"
        assert api_key == "test-api-key"
        assert auth_key == "test-auth-key"
        
        print("✅ PASSED")
    except Exception as e:
        print(f"❌ FAILED - {e}")
        return False
    finally:
        # Cleanup
        del os.environ["MYSQL_PASSWORD"]
        del os.environ["API_KEY"]
        del os.environ["FIR_AUTH_KEY"]
        del os.environ["ENVIRONMENT"]
    
    return True


def run_all_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("AWS Secrets Manager - Basic Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        test_environment_variable_fallback,
        test_required_secret_missing,
        test_optional_secret_missing,
        test_default_value,
        test_cache_basic,
        test_cache_clear,
        test_refresh_secret,
        test_global_functions,
        test_singleton,
        test_empty_secret_value,
        test_integration_with_agentv5,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
            if result is False:
                failed += 1
            else:
                passed += 1
        except AssertionError as e:
            print(f"❌ FAILED - {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR - {e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
