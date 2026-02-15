"""
AWS Secrets Manager Integration Module

This module provides a unified interface for retrieving secrets from AWS Secrets Manager
with fallback to environment variables for local development.

Features:
- Automatic AWS Secrets Manager integration for production
- Environment variable fallback for local development
- Caching to minimize API calls
- Structured error handling
- Support for both individual secrets and secret bundles (JSON)
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from functools import lru_cache

# AWS SDK - optional import for local development
try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

# Note: Logger will be configured by json_logging module when imported by main application
# For standalone usage, basic logging is configured
logger = logging.getLogger("secrets-manager")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)
    if not AWS_AVAILABLE:
        logger.warning("boto3 not available - AWS Secrets Manager disabled, using environment variables only")


logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Unified secrets management with AWS Secrets Manager and environment variable fallback.
    
    Usage:
        secrets = SecretsManager()
        db_password = secrets.get_secret("MYSQL_PASSWORD")
        all_secrets = secrets.get_secret_bundle("afirgen/production")
    """
    
    def __init__(
        self,
        region_name: Optional[str] = None,
        use_aws: Optional[bool] = None,
        cache_ttl: int = 300  # 5 minutes default cache
    ):
        """
        Initialize the secrets manager.
        
        Args:
            region_name: AWS region (defaults to AWS_REGION env var or us-east-1)
            use_aws: Force AWS usage (defaults to auto-detect based on environment)
            cache_ttl: Cache time-to-live in seconds
        """
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        
        # Determine if we should use AWS Secrets Manager
        if use_aws is None:
            # Auto-detect: use AWS if boto3 is available and we're not in local dev
            self.use_aws = AWS_AVAILABLE and os.getenv("ENVIRONMENT", "development") != "development"
        else:
            self.use_aws = use_aws and AWS_AVAILABLE
        
        # Initialize AWS client if needed
        self.client = None
        if self.use_aws:
            try:
                self.client = boto3.client("secretsmanager", region_name=self.region_name)
                logger.info(f"AWS Secrets Manager initialized for region: {self.region_name}")
            except Exception as e:
                logger.error(f"Failed to initialize AWS Secrets Manager: {e}")
                self.use_aws = False
        
        if not self.use_aws:
            logger.info("Using environment variables for secrets (local development mode)")
    
    def get_secret(
        self,
        secret_name: str,
        default: Optional[str] = None,
        required: bool = True
    ) -> Optional[str]:
        """
        Get a secret value from AWS Secrets Manager or environment variables.
        
        Args:
            secret_name: Name of the secret (env var name or AWS secret name)
            default: Default value if secret not found
            required: If True, raise error when secret not found and no default
        
        Returns:
            Secret value as string, or None if not found and not required
        
        Raises:
            ValueError: If secret is required but not found
        """
        # Check cache first
        cached_value = self._get_from_cache(secret_name)
        if cached_value is not None:
            return cached_value
        
        value = None
        
        # Try AWS Secrets Manager first if enabled
        if self.use_aws:
            try:
                value = self._get_from_aws(secret_name)
                if value is not None:
                    logger.debug(f"Retrieved secret '{secret_name}' from AWS Secrets Manager")
            except Exception as e:
                logger.warning(f"Failed to get secret '{secret_name}' from AWS: {e}")
        
        # Fallback to environment variable
        if value is None:
            value = os.getenv(secret_name, default)
            if value is not None:
                logger.debug(f"Retrieved secret '{secret_name}' from environment variable")
        
        # Handle missing required secrets
        if value is None and required:
            raise ValueError(
                f"Required secret '{secret_name}' not found in AWS Secrets Manager or environment variables"
            )
        
        # Cache the value
        if value is not None:
            self._add_to_cache(secret_name, value)
        
        return value
    
    def get_secret_bundle(
        self,
        secret_name: str,
        required: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get a bundle of secrets stored as JSON in AWS Secrets Manager.
        
        This is useful for storing multiple related secrets together, e.g.:
        {
            "MYSQL_PASSWORD": "secret123",
            "API_KEY": "key456",
            "FIR_AUTH_KEY": "auth789"
        }
        
        Args:
            secret_name: Name of the secret bundle in AWS
            required: If True, raise error when secret not found
        
        Returns:
            Dictionary of secret key-value pairs, or None if not found
        
        Raises:
            ValueError: If secret is required but not found
            json.JSONDecodeError: If secret value is not valid JSON
        """
        # Check cache first
        cached_value = self._get_from_cache(secret_name)
        if cached_value is not None:
            return cached_value
        
        if not self.use_aws:
            logger.warning(f"Secret bundle '{secret_name}' requested but AWS Secrets Manager not available")
            if required:
                raise ValueError(f"Secret bundle '{secret_name}' requires AWS Secrets Manager")
            return None
        
        try:
            secret_string = self._get_from_aws(secret_name)
            if secret_string is None:
                if required:
                    raise ValueError(f"Required secret bundle '{secret_name}' not found in AWS Secrets Manager")
                return None
            
            # Parse JSON
            secret_dict = json.loads(secret_string)
            logger.info(f"Retrieved secret bundle '{secret_name}' with {len(secret_dict)} keys")
            
            # Cache the bundle
            self._add_to_cache(secret_name, secret_dict)
            
            return secret_dict
            
        except json.JSONDecodeError as e:
            logger.error(f"Secret bundle '{secret_name}' contains invalid JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get secret bundle '{secret_name}': {e}")
            if required:
                raise
            return None
    
    def _get_from_aws(self, secret_name: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        if not self.client:
            return None
        
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            
            # Secrets can be stored as SecretString or SecretBinary
            if "SecretString" in response:
                return response["SecretString"]
            else:
                # Binary secrets (less common)
                import base64
                return base64.b64decode(response["SecretBinary"]).decode("utf-8")
                
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                logger.debug(f"Secret '{secret_name}' not found in AWS Secrets Manager")
            elif error_code == "AccessDeniedException":
                logger.error(f"Access denied to secret '{secret_name}' - check IAM permissions")
            elif error_code == "InvalidRequestException":
                logger.error(f"Invalid request for secret '{secret_name}': {e}")
            else:
                logger.error(f"AWS error getting secret '{secret_name}': {e}")
            return None
        except BotoCoreError as e:
            logger.error(f"BotoCore error getting secret '{secret_name}': {e}")
            return None
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return value
            else:
                # Expired - remove from cache
                del self._cache[key]
        return None
    
    def _add_to_cache(self, key: str, value: Any) -> None:
        """Add value to cache with current timestamp."""
        self._cache[key] = (value, datetime.now())
    
    def clear_cache(self) -> None:
        """Clear the secrets cache. Useful for testing or forcing refresh."""
        self._cache.clear()
        logger.debug("Secrets cache cleared")
    
    def refresh_secret(self, secret_name: str) -> Optional[str]:
        """
        Force refresh a secret from AWS Secrets Manager, bypassing cache.
        
        Args:
            secret_name: Name of the secret to refresh
        
        Returns:
            Updated secret value
        """
        # Remove from cache
        if secret_name in self._cache:
            del self._cache[secret_name]
        
        # Fetch fresh value
        return self.get_secret(secret_name, required=False)


# Global singleton instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """
    Get the global SecretsManager instance (singleton pattern).
    
    Returns:
        SecretsManager instance
    """
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def get_secret(secret_name: str, default: Optional[str] = None, required: bool = True) -> Optional[str]:
    """
    Convenience function to get a secret using the global SecretsManager instance.
    
    Args:
        secret_name: Name of the secret
        default: Default value if not found
        required: If True, raise error when not found
    
    Returns:
        Secret value
    """
    return get_secrets_manager().get_secret(secret_name, default, required)


def get_secret_bundle(secret_name: str, required: bool = True) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get a secret bundle using the global SecretsManager instance.
    
    Args:
        secret_name: Name of the secret bundle
        required: If True, raise error when not found
    
    Returns:
        Dictionary of secrets
    """
    return get_secrets_manager().get_secret_bundle(secret_name, required)
