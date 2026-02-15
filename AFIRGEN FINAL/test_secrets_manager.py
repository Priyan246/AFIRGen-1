"""
Test Suite for AWS Secrets Manager Integration

This test suite validates the secrets_manager module functionality including:
- Environment variable fallback
- AWS Secrets Manager integration (mocked)
- Caching behavior
- Error handling
- Secret bundles
"""

import os
import sys
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add main backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "main backend"))

from secrets_manager import SecretsManager, get_secrets_manager, get_secret, get_secret_bundle


class TestSecretsManagerBasic:
    """Test basic secrets manager functionality"""
    
    def test_environment_variable_fallback(self):
        """Test that environment variables work when AWS is disabled"""
        os.environ["TEST_SECRET_1"] = "test-value-1"
        
        secrets = SecretsManager(use_aws=False)
        value = secrets.get_secret("TEST_SECRET_1")
        
        assert value == "test-value-1"
        
        # Cleanup
        del os.environ["TEST_SECRET_1"]
    
    def test_required_secret_missing(self):
        """Test that missing required secrets raise ValueError"""
        secrets = SecretsManager(use_aws=False)
        
        with pytest.raises(ValueError) as exc_info:
            secrets.get_secret("NONEXISTENT_SECRET_12345", required=True)
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_optional_secret_missing(self):
        """Test that missing optional secrets return None"""
        secrets = SecretsManager(use_aws=False)
        value = secrets.get_secret("NONEXISTENT_SECRET_12345", required=False)
        
        assert value is None
    
    def test_default_value(self):
        """Test default value when secret not found"""
        secrets = SecretsManager(use_aws=False)
        value = secrets.get_secret("NONEXISTENT_SECRET_12345", default="default-value")
        
        assert value == "default-value"
    
    def test_default_value_overrides_required(self):
        """Test that default value prevents error even when required=True"""
        secrets = SecretsManager(use_aws=False)
        value = secrets.get_secret("NONEXISTENT_SECRET_12345", default="default-value", required=True)
        
        assert value == "default-value"


class TestSecretsManagerCaching:
    """Test caching functionality"""
    
    def test_cache_basic(self):
        """Test that caching works"""
        os.environ["CACHED_SECRET"] = "cached-value"
        
        secrets = SecretsManager(use_aws=False, cache_ttl=60)
        
        # First call
        value1 = secrets.get_secret("CACHED_SECRET")
        
        # Change env var
        os.environ["CACHED_SECRET"] = "new-value"
        
        # Second call should return cached value
        value2 = secrets.get_secret("CACHED_SECRET")
        
        assert value1 == value2 == "cached-value"
        
        # Cleanup
        del os.environ["CACHED_SECRET"]
    
    def test_cache_clear(self):
        """Test cache clearing"""
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
        
        assert value1 == "cached-value"
        assert value2 == "new-value"
        
        # Cleanup
        del os.environ["CACHED_SECRET_2"]
    
    def test_cache_expiration(self):
        """Test that cache expires after TTL"""
        os.environ["EXPIRING_SECRET"] = "old-value"
        
        secrets = SecretsManager(use_aws=False, cache_ttl=1)  # 1 second TTL
        
        # First call
        value1 = secrets.get_secret("EXPIRING_SECRET")
        
        # Change env var
        os.environ["EXPIRING_SECRET"] = "new-value"
        
        # Wait for cache to expire
        import time
        time.sleep(1.1)
        
        # Should get new value after expiration
        value2 = secrets.get_secret("EXPIRING_SECRET")
        
        assert value1 == "old-value"
        assert value2 == "new-value"
        
        # Cleanup
        del os.environ["EXPIRING_SECRET"]
    
    def test_refresh_secret(self):
        """Test force refresh bypasses cache"""
        os.environ["REFRESH_SECRET"] = "old-value"
        
        secrets = SecretsManager(use_aws=False, cache_ttl=60)
        
        # First call
        value1 = secrets.get_secret("REFRESH_SECRET")
        
        # Change env var
        os.environ["REFRESH_SECRET"] = "new-value"
        
        # Refresh should bypass cache
        value2 = secrets.refresh_secret("REFRESH_SECRET")
        
        assert value1 == "old-value"
        assert value2 == "new-value"
        
        # Cleanup
        del os.environ["REFRESH_SECRET"]


class TestSecretsManagerAWS:
    """Test AWS Secrets Manager integration (mocked)"""
    
    @patch('secrets_manager.boto3')
    def test_aws_secret_retrieval(self, mock_boto3):
        """Test retrieving secret from AWS Secrets Manager"""
        # Mock AWS client
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            "SecretString": "aws-secret-value"
        }
        mock_boto3.client.return_value = mock_client
        
        secrets = SecretsManager(use_aws=True)
        value = secrets.get_secret("AWS_SECRET")
        
        assert value == "aws-secret-value"
        mock_client.get_secret_value.assert_called_once_with(SecretId="AWS_SECRET")
    
    @patch('secrets_manager.boto3')
    def test_aws_secret_not_found_fallback(self, mock_boto3):
        """Test fallback to env var when AWS secret not found"""
        from botocore.exceptions import ClientError
        
        # Mock AWS client to raise ResourceNotFoundException
        mock_client = Mock()
        mock_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException"}},
            "GetSecretValue"
        )
        mock_boto3.client.return_value = mock_client
        
        os.environ["FALLBACK_SECRET"] = "env-var-value"
        
        secrets = SecretsManager(use_aws=True)
        value = secrets.get_secret("FALLBACK_SECRET")
        
        assert value == "env-var-value"
        
        # Cleanup
        del os.environ["FALLBACK_SECRET"]
    
    @patch('secrets_manager.boto3')
    def test_aws_access_denied(self, mock_boto3):
        """Test handling of access denied errors"""
        from botocore.exceptions import ClientError
        
        # Mock AWS client to raise AccessDeniedException
        mock_client = Mock()
        mock_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException"}},
            "GetSecretValue"
        )
        mock_boto3.client.return_value = mock_client
        
        os.environ["DENIED_SECRET"] = "fallback-value"
        
        secrets = SecretsManager(use_aws=True)
        value = secrets.get_secret("DENIED_SECRET")
        
        # Should fallback to env var
        assert value == "fallback-value"
        
        # Cleanup
        del os.environ["DENIED_SECRET"]
    
    @patch('secrets_manager.boto3')
    def test_aws_binary_secret(self, mock_boto3):
        """Test retrieving binary secret from AWS"""
        import base64
        
        # Mock AWS client with binary secret
        mock_client = Mock()
        secret_value = "binary-secret-value"
        mock_client.get_secret_value.return_value = {
            "SecretBinary": base64.b64encode(secret_value.encode("utf-8"))
        }
        mock_boto3.client.return_value = mock_client
        
        secrets = SecretsManager(use_aws=True)
        value = secrets.get_secret("BINARY_SECRET")
        
        assert value == secret_value


class TestSecretsManagerBundles:
    """Test secret bundle functionality"""
    
    @patch('secrets_manager.boto3')
    def test_secret_bundle_retrieval(self, mock_boto3):
        """Test retrieving secret bundle from AWS"""
        # Mock AWS client
        mock_client = Mock()
        bundle_data = {
            "MYSQL_PASSWORD": "db-password",
            "API_KEY": "api-key-value",
            "FIR_AUTH_KEY": "auth-key-value"
        }
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(bundle_data)
        }
        mock_boto3.client.return_value = mock_client
        
        secrets = SecretsManager(use_aws=True)
        bundle = secrets.get_secret_bundle("afirgen/production/secrets")
        
        assert bundle == bundle_data
        assert bundle["MYSQL_PASSWORD"] == "db-password"
        assert bundle["API_KEY"] == "api-key-value"
    
    @patch('secrets_manager.boto3')
    def test_secret_bundle_invalid_json(self, mock_boto3):
        """Test handling of invalid JSON in secret bundle"""
        # Mock AWS client with invalid JSON
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            "SecretString": "not-valid-json"
        }
        mock_boto3.client.return_value = mock_client
        
        secrets = SecretsManager(use_aws=True)
        
        with pytest.raises(json.JSONDecodeError):
            secrets.get_secret_bundle("invalid-bundle")
    
    def test_secret_bundle_without_aws(self):
        """Test that secret bundle requires AWS"""
        secrets = SecretsManager(use_aws=False)
        
        with pytest.raises(ValueError) as exc_info:
            secrets.get_secret_bundle("test-bundle", required=True)
        
        assert "requires AWS Secrets Manager" in str(exc_info.value)
    
    @patch('secrets_manager.boto3')
    def test_secret_bundle_caching(self, mock_boto3):
        """Test that secret bundles are cached"""
        # Mock AWS client
        mock_client = Mock()
        bundle_data = {"KEY1": "value1", "KEY2": "value2"}
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(bundle_data)
        }
        mock_boto3.client.return_value = mock_client
        
        secrets = SecretsManager(use_aws=True, cache_ttl=60)
        
        # First call
        bundle1 = secrets.get_secret_bundle("test-bundle")
        
        # Second call should use cache
        bundle2 = secrets.get_secret_bundle("test-bundle")
        
        assert bundle1 == bundle2
        # Should only call AWS once
        assert mock_client.get_secret_value.call_count == 1


class TestGlobalFunctions:
    """Test global convenience functions"""
    
    def test_get_secret_function(self):
        """Test global get_secret function"""
        os.environ["GLOBAL_SECRET"] = "global-value"
        
        value = get_secret("GLOBAL_SECRET")
        
        assert value == "global-value"
        
        # Cleanup
        del os.environ["GLOBAL_SECRET"]
    
    @patch('secrets_manager.boto3')
    def test_get_secret_bundle_function(self, mock_boto3):
        """Test global get_secret_bundle function"""
        # Mock AWS client
        mock_client = Mock()
        bundle_data = {"KEY": "value"}
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(bundle_data)
        }
        mock_boto3.client.return_value = mock_client
        
        # Force AWS usage for this test
        import secrets_manager
        secrets_manager._secrets_manager = SecretsManager(use_aws=True)
        
        bundle = get_secret_bundle("test-bundle")
        
        assert bundle == bundle_data
        
        # Reset global instance
        secrets_manager._secrets_manager = None
    
    def test_get_secrets_manager_singleton(self):
        """Test that get_secrets_manager returns singleton"""
        manager1 = get_secrets_manager()
        manager2 = get_secrets_manager()
        
        assert manager1 is manager2


class TestEnvironmentDetection:
    """Test automatic environment detection"""
    
    @patch('secrets_manager.boto3')
    def test_production_environment_enables_aws(self, mock_boto3):
        """Test that production environment enables AWS"""
        os.environ["ENVIRONMENT"] = "production"
        
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        
        secrets = SecretsManager()
        
        assert secrets.use_aws is True
        
        # Cleanup
        del os.environ["ENVIRONMENT"]
    
    def test_development_environment_disables_aws(self):
        """Test that development environment disables AWS"""
        os.environ["ENVIRONMENT"] = "development"
        
        secrets = SecretsManager()
        
        assert secrets.use_aws is False
        
        # Cleanup
        del os.environ["ENVIRONMENT"]
    
    @patch('secrets_manager.AWS_AVAILABLE', False)
    def test_boto3_unavailable_disables_aws(self):
        """Test that missing boto3 disables AWS"""
        os.environ["ENVIRONMENT"] = "production"
        
        secrets = SecretsManager()
        
        assert secrets.use_aws is False
        
        # Cleanup
        del os.environ["ENVIRONMENT"]


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_empty_secret_value(self):
        """Test handling of empty secret values"""
        os.environ["EMPTY_SECRET"] = ""
        
        secrets = SecretsManager(use_aws=False)
        value = secrets.get_secret("EMPTY_SECRET")
        
        assert value == ""
        
        # Cleanup
        del os.environ["EMPTY_SECRET"]
    
    def test_whitespace_secret_value(self):
        """Test handling of whitespace-only secret values"""
        os.environ["WHITESPACE_SECRET"] = "   "
        
        secrets = SecretsManager(use_aws=False)
        value = secrets.get_secret("WHITESPACE_SECRET")
        
        assert value == "   "
        
        # Cleanup
        del os.environ["WHITESPACE_SECRET"]
    
    @patch('secrets_manager.boto3')
    def test_aws_client_initialization_failure(self, mock_boto3):
        """Test handling of AWS client initialization failure"""
        mock_boto3.client.side_effect = Exception("AWS initialization failed")
        
        os.environ["FALLBACK_SECRET_2"] = "fallback-value"
        
        secrets = SecretsManager(use_aws=True)
        
        # Should fallback to env vars
        assert secrets.use_aws is False
        
        value = secrets.get_secret("FALLBACK_SECRET_2")
        assert value == "fallback-value"
        
        # Cleanup
        del os.environ["FALLBACK_SECRET_2"]


def run_tests():
    """Run all tests and print results"""
    print("=" * 60)
    print("AWS Secrets Manager Test Suite")
    print("=" * 60)
    print()
    
    # Run pytest
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])
    
    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests())
