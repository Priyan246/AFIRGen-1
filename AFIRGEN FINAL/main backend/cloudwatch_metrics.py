"""
CloudWatch Metrics Integration for AFIRGen
Publishes custom application metrics to AWS CloudWatch
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from functools import wraps
import time
import asyncio

logger = logging.getLogger(__name__)

# AWS SDK - optional import for local development
try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    # Create dummy exception classes for when boto3 is not available
    ClientError = Exception
    BotoCoreError = Exception
    logger.warning("boto3 not available - CloudWatch metrics disabled")


class CloudWatchMetrics:
    """
    CloudWatch metrics publisher for AFIRGen application.
    Publishes custom metrics to CloudWatch for monitoring and alerting.
    """
    
    def __init__(
        self,
        namespace: str = "AFIRGen",
        region_name: Optional[str] = None,
        enabled: Optional[bool] = None,
        buffer_size: int = 20,
        flush_interval: int = 60
    ):
        """
        Initialize CloudWatch metrics publisher.
        
        Args:
            namespace: CloudWatch namespace for metrics
            region_name: AWS region (defaults to AWS_REGION env var or us-east-1)
            enabled: Whether to enable CloudWatch publishing (auto-detects if None)
            buffer_size: Number of metrics to buffer before flushing
            flush_interval: Seconds between automatic flushes
        """
        self.namespace = namespace
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        
        # Determine if CloudWatch should be enabled
        if enabled is None:
            # Auto-detect: enable if boto3 available and not in local dev
            self.enabled = AWS_AVAILABLE and os.getenv("ENVIRONMENT", "development") != "development"
        else:
            self.enabled = enabled and AWS_AVAILABLE
        
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.metric_buffer: List[Dict[str, Any]] = []
        self.last_flush = time.time()
        
        # Initialize CloudWatch client
        self.client = None
        if self.enabled:
            try:
                self.client = boto3.client("cloudwatch", region_name=self.region_name)
                logger.info(f"CloudWatch metrics enabled for namespace: {self.namespace}")
            except Exception as e:
                logger.error(f"Failed to initialize CloudWatch client: {e}")
                self.enabled = False
        else:
            logger.info("CloudWatch metrics disabled (local development mode)")
    
    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "None",
        dimensions: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Publish a single metric to CloudWatch.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: CloudWatch unit (Count, Seconds, Milliseconds, etc.)
            dimensions: Metric dimensions (e.g., {"Service": "MainBackend"})
            timestamp: Metric timestamp (defaults to now)
        """
        if not self.enabled:
            return
        
        metric_data = {
            "MetricName": metric_name,
            "Value": value,
            "Unit": unit,
            "Timestamp": timestamp or datetime.utcnow()
        }
        
        if dimensions:
            metric_data["Dimensions"] = [
                {"Name": k, "Value": v} for k, v in dimensions.items()
            ]
        
        self.metric_buffer.append(metric_data)
        
        # Auto-flush if buffer is full or interval exceeded
        if len(self.metric_buffer) >= self.buffer_size or \
           (time.time() - self.last_flush) >= self.flush_interval:
            self.flush()
    
    def flush(self):
        """Flush buffered metrics to CloudWatch"""
        if not self.enabled or not self.metric_buffer:
            return
        
        try:
            # CloudWatch allows max 20 metrics per request
            for i in range(0, len(self.metric_buffer), 20):
                batch = self.metric_buffer[i:i+20]
                self.client.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=batch
                )
            
            logger.debug(f"Flushed {len(self.metric_buffer)} metrics to CloudWatch")
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to publish metrics to CloudWatch: {e}")
        except Exception as e:
            logger.error(f"Unexpected error publishing metrics: {e}")
        finally:
            # Always clear buffer and update last flush time, even on error
            self.metric_buffer.clear()
            self.last_flush = time.time()
    
    def record_count(
        self,
        metric_name: str,
        count: int = 1,
        dimensions: Optional[Dict[str, str]] = None
    ):
        """Record a count metric"""
        self.put_metric(metric_name, count, unit="Count", dimensions=dimensions)
    
    def record_duration(
        self,
        metric_name: str,
        duration_ms: float,
        dimensions: Optional[Dict[str, str]] = None
    ):
        """Record a duration metric in milliseconds"""
        self.put_metric(metric_name, duration_ms, unit="Milliseconds", dimensions=dimensions)
    
    def record_percentage(
        self,
        metric_name: str,
        percentage: float,
        dimensions: Optional[Dict[str, str]] = None
    ):
        """Record a percentage metric"""
        self.put_metric(metric_name, percentage, unit="Percent", dimensions=dimensions)
    
    def record_size(
        self,
        metric_name: str,
        size_bytes: int,
        dimensions: Optional[Dict[str, str]] = None
    ):
        """Record a size metric in bytes"""
        self.put_metric(metric_name, size_bytes, unit="Bytes", dimensions=dimensions)
    
    async def flush_async(self):
        """Async version of flush for use in async contexts"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.flush)
    
    def __del__(self):
        """Ensure metrics are flushed on cleanup"""
        try:
            self.flush()
        except:
            pass


# Global metrics instance
_metrics_instance: Optional[CloudWatchMetrics] = None


def get_metrics() -> CloudWatchMetrics:
    """Get or create global CloudWatch metrics instance"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = CloudWatchMetrics()
    return _metrics_instance


def track_duration(metric_name: str, dimensions: Optional[Dict[str, str]] = None):
    """
    Decorator to track function execution duration.
    
    Example:
        @track_duration("FIRGeneration", {"Service": "MainBackend"})
        async def generate_fir(data):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000
                get_metrics().record_duration(metric_name, duration_ms, dimensions)
                return result
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                error_dims = {**(dimensions or {}), "Status": "Error"}
                get_metrics().record_duration(metric_name, duration_ms, error_dims)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000
                get_metrics().record_duration(metric_name, duration_ms, dimensions)
                return result
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                error_dims = {**(dimensions or {}), "Status": "Error"}
                get_metrics().record_duration(metric_name, duration_ms, error_dims)
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# Convenience functions for common metrics
def record_api_request(endpoint: str, method: str, status_code: int, duration_ms: float):
    """Record API request metrics"""
    metrics = get_metrics()
    dimensions = {
        "Endpoint": endpoint,
        "Method": method,
        "StatusCode": str(status_code)
    }
    metrics.record_count("APIRequests", 1, dimensions)
    metrics.record_duration("APILatency", duration_ms, dimensions)
    
    # Record error if status >= 400
    if status_code >= 400:
        error_dims = {"Endpoint": endpoint, "StatusCode": str(status_code)}
        metrics.record_count("APIErrors", 1, error_dims)


def record_fir_generation(success: bool, duration_ms: float, step: Optional[str] = None):
    """Record FIR generation metrics"""
    metrics = get_metrics()
    dimensions = {"Status": "Success" if success else "Failure"}
    if step:
        dimensions["Step"] = step
    
    metrics.record_count("FIRGenerations", 1, dimensions)
    metrics.record_duration("FIRGenerationDuration", duration_ms, dimensions)


def record_model_inference(model_name: str, duration_ms: float, token_count: Optional[int] = None):
    """Record model inference metrics"""
    metrics = get_metrics()
    dimensions = {"Model": model_name}
    
    metrics.record_count("ModelInferences", 1, dimensions)
    metrics.record_duration("ModelInferenceDuration", duration_ms, dimensions)
    
    if token_count:
        metrics.record_count("TokensGenerated", token_count, dimensions)


def record_database_operation(operation: str, duration_ms: float, success: bool = True):
    """Record database operation metrics"""
    metrics = get_metrics()
    dimensions = {
        "Operation": operation,
        "Status": "Success" if success else "Failure"
    }
    
    metrics.record_count("DatabaseOperations", 1, dimensions)
    metrics.record_duration("DatabaseLatency", duration_ms, dimensions)


def record_cache_operation(cache_name: str, hit: bool):
    """Record cache hit/miss metrics"""
    metrics = get_metrics()
    dimensions = {
        "Cache": cache_name,
        "Result": "Hit" if hit else "Miss"
    }
    metrics.record_count("CacheOperations", 1, dimensions)


def record_rate_limit_event(client_ip: str, blocked: bool):
    """Record rate limiting events"""
    metrics = get_metrics()
    dimensions = {
        "Result": "Blocked" if blocked else "Allowed"
    }
    metrics.record_count("RateLimitEvents", 1, dimensions)


def record_auth_event(success: bool, reason: Optional[str] = None):
    """Record authentication events"""
    metrics = get_metrics()
    dimensions = {"Status": "Success" if success else "Failure"}
    if reason:
        dimensions["Reason"] = reason
    
    metrics.record_count("AuthenticationEvents", 1, dimensions)


def record_health_check(service: str, healthy: bool, response_time_ms: float):
    """Record health check metrics"""
    metrics = get_metrics()
    dimensions = {
        "Service": service,
        "Status": "Healthy" if healthy else "Unhealthy"
    }
    
    metrics.record_count("HealthChecks", 1, dimensions)
    metrics.record_duration("HealthCheckDuration", response_time_ms, dimensions)
