# xray_tracing.py
# -------------------------------------------------------------
# AWS X-Ray Distributed Tracing Integration
# -------------------------------------------------------------

import os
import logging
from typing import Optional, Dict, Any, Callable
from functools import wraps
import asyncio

# X-Ray SDK imports
from aws_xray_sdk.core import xray_recorder, patch_all
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.ext.fastapi.middleware import XRayMiddleware
from aws_xray_sdk.core.models.segment import Segment
from aws_xray_sdk.core.models.subsegment import Subsegment

log = logging.getLogger(__name__)

# Configuration
XRAY_CONFIG = {
    "enabled": os.getenv("XRAY_ENABLED", "true").lower() == "true",
    "service_name": os.getenv("XRAY_SERVICE_NAME", "afirgen-main-backend"),
    "sampling_rate": float(os.getenv("XRAY_SAMPLING_RATE", "0.1")),  # 10% sampling for cost optimization
    "daemon_address": os.getenv("XRAY_DAEMON_ADDRESS", "127.0.0.1:2000"),
    "context_missing": os.getenv("XRAY_CONTEXT_MISSING", "LOG_ERROR"),  # LOG_ERROR or RUNTIME_ERROR
}


def setup_xray(app, service_name: Optional[str] = None):
    """
    Configure AWS X-Ray for FastAPI application
    
    Args:
        app: FastAPI application instance
        service_name: Optional service name override
    """
    if not XRAY_CONFIG["enabled"]:
        log.info("X-Ray tracing is disabled")
        return
    
    try:
        # Set service name
        service_name = service_name or XRAY_CONFIG["service_name"]
        
        # Configure X-Ray recorder
        xray_recorder.configure(
            service=service_name,
            sampling=XRAY_CONFIG["sampling_rate"] < 1.0,  # Enable sampling if rate < 100%
            context_missing=XRAY_CONFIG["context_missing"],
            daemon_address=XRAY_CONFIG["daemon_address"],
        )
        
        # Patch supported libraries for automatic instrumentation
        # This will automatically trace: httpx, requests, boto3, mysql, etc.
        patch_all()
        
        # Add X-Ray middleware to FastAPI
        app.add_middleware(XRayMiddleware, recorder=xray_recorder)
        
        log.info(f"✅ X-Ray tracing enabled for service: {service_name}")
        log.info(f"   Sampling rate: {XRAY_CONFIG['sampling_rate'] * 100}%")
        log.info(f"   Daemon address: {XRAY_CONFIG['daemon_address']}")
        log.info(f"   Context missing: {XRAY_CONFIG['context_missing']}")
        
    except Exception as e:
        log.error(f"Failed to configure X-Ray: {e}")
        if XRAY_CONFIG["context_missing"] == "RUNTIME_ERROR":
            raise


def trace_segment(name: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Decorator to create a custom X-Ray segment for a function
    
    Usage:
        @trace_segment("process_fir")
        def process_fir(data):
            ...
    
    Args:
        name: Segment name
        metadata: Optional metadata to attach to segment
    """
    def decorator(func: Callable):
        if not XRAY_CONFIG["enabled"]:
            return func
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                segment = xray_recorder.begin_segment(name)
                
                # Add metadata
                if metadata:
                    for key, value in metadata.items():
                        segment.put_metadata(key, value)
                
                # Add function info
                segment.put_annotation("function", func.__name__)
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    segment.put_annotation("error", True)
                    segment.put_metadata("exception", str(e))
                    raise
                finally:
                    xray_recorder.end_segment()
                    
            except Exception as e:
                log.error(f"X-Ray segment error: {e}")
                # Fall back to executing function without tracing
                return func(*args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                segment = xray_recorder.begin_segment(name)
                
                # Add metadata
                if metadata:
                    for key, value in metadata.items():
                        segment.put_metadata(key, value)
                
                # Add function info
                segment.put_annotation("function", func.__name__)
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    segment.put_annotation("error", True)
                    segment.put_metadata("exception", str(e))
                    raise
                finally:
                    xray_recorder.end_segment()
                    
            except Exception as e:
                log.error(f"X-Ray segment error: {e}")
                # Fall back to executing function without tracing
                return await func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def trace_subsegment(name: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Decorator to create a custom X-Ray subsegment for a function
    
    Usage:
        @trace_subsegment("database_query")
        async def query_database(query):
            ...
    
    Args:
        name: Subsegment name
        metadata: Optional metadata to attach to subsegment
    """
    def decorator(func: Callable):
        if not XRAY_CONFIG["enabled"]:
            return func
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                subsegment = xray_recorder.begin_subsegment(name)
                
                # Add metadata
                if metadata:
                    for key, value in metadata.items():
                        subsegment.put_metadata(key, value)
                
                # Add function info
                subsegment.put_annotation("function", func.__name__)
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    subsegment.put_annotation("error", True)
                    subsegment.put_metadata("exception", str(e))
                    raise
                finally:
                    xray_recorder.end_subsegment()
                    
            except Exception as e:
                log.error(f"X-Ray subsegment error: {e}")
                # Fall back to executing function without tracing
                return func(*args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                subsegment = xray_recorder.begin_subsegment(name)
                
                # Add metadata
                if metadata:
                    for key, value in metadata.items():
                        subsegment.put_metadata(key, value)
                
                # Add function info
                subsegment.put_annotation("function", func.__name__)
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    subsegment.put_annotation("error", True)
                    subsegment.put_metadata("exception", str(e))
                    raise
                finally:
                    xray_recorder.end_subsegment()
                    
            except Exception as e:
                log.error(f"X-Ray subsegment error: {e}")
                # Fall back to executing function without tracing
                return await func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def add_trace_annotation(key: str, value: Any):
    """
    Add an annotation to the current X-Ray segment/subsegment
    
    Annotations are indexed and searchable in X-Ray console
    
    Args:
        key: Annotation key
        value: Annotation value (must be string, number, or boolean)
    """
    if not XRAY_CONFIG["enabled"]:
        return
    
    try:
        current_segment = xray_recorder.current_segment()
        if current_segment:
            current_segment.put_annotation(key, value)
    except Exception as e:
        log.debug(f"Failed to add X-Ray annotation: {e}")


def add_trace_metadata(key: str, value: Any, namespace: str = "default"):
    """
    Add metadata to the current X-Ray segment/subsegment
    
    Metadata is not indexed but can store complex objects
    
    Args:
        key: Metadata key
        value: Metadata value (can be any JSON-serializable object)
        namespace: Metadata namespace for organization
    """
    if not XRAY_CONFIG["enabled"]:
        return
    
    try:
        current_segment = xray_recorder.current_segment()
        if current_segment:
            current_segment.put_metadata(key, value, namespace)
    except Exception as e:
        log.debug(f"Failed to add X-Ray metadata: {e}")


def get_trace_id() -> Optional[str]:
    """
    Get the current X-Ray trace ID
    
    Returns:
        Trace ID string or None if not available
    """
    if not XRAY_CONFIG["enabled"]:
        return None
    
    try:
        current_segment = xray_recorder.current_segment()
        if current_segment:
            return current_segment.trace_id
    except Exception:
        pass
    
    return None


# Context manager for manual subsegment creation
class XRaySubsegment:
    """
    Context manager for creating X-Ray subsegments
    
    Usage:
        with XRaySubsegment("database_operation") as subsegment:
            # Your code here
            subsegment.put_annotation("query_type", "SELECT")
    """
    
    def __init__(self, name: str):
        self.name = name
        self.subsegment = None
    
    def __enter__(self):
        if XRAY_CONFIG["enabled"]:
            try:
                self.subsegment = xray_recorder.begin_subsegment(self.name)
                return self.subsegment
            except Exception as e:
                log.debug(f"Failed to create X-Ray subsegment: {e}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if XRAY_CONFIG["enabled"] and self.subsegment:
            try:
                if exc_type:
                    self.subsegment.put_annotation("error", True)
                    self.subsegment.put_metadata("exception", str(exc_val))
                xray_recorder.end_subsegment()
            except Exception as e:
                log.debug(f"Failed to end X-Ray subsegment: {e}")
    
    def put_annotation(self, key: str, value: Any):
        """Add annotation to subsegment"""
        if self.subsegment:
            try:
                self.subsegment.put_annotation(key, value)
            except Exception as e:
                log.debug(f"Failed to add annotation: {e}")
    
    def put_metadata(self, key: str, value: Any, namespace: str = "default"):
        """Add metadata to subsegment"""
        if self.subsegment:
            try:
                self.subsegment.put_metadata(key, value, namespace)
            except Exception as e:
                log.debug(f"Failed to add metadata: {e}")


# Async context manager for subsegments
class AsyncXRaySubsegment:
    """
    Async context manager for creating X-Ray subsegments
    
    Usage:
        async with AsyncXRaySubsegment("async_operation") as subsegment:
            # Your async code here
            subsegment.put_annotation("operation_type", "async")
    """
    
    def __init__(self, name: str):
        self.name = name
        self.subsegment = None
    
    async def __aenter__(self):
        if XRAY_CONFIG["enabled"]:
            try:
                self.subsegment = xray_recorder.begin_subsegment(self.name)
                return self.subsegment
            except Exception as e:
                log.debug(f"Failed to create X-Ray subsegment: {e}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if XRAY_CONFIG["enabled"] and self.subsegment:
            try:
                if exc_type:
                    self.subsegment.put_annotation("error", True)
                    self.subsegment.put_metadata("exception", str(exc_val))
                xray_recorder.end_subsegment()
            except Exception as e:
                log.debug(f"Failed to end X-Ray subsegment: {e}")
    
    def put_annotation(self, key: str, value: Any):
        """Add annotation to subsegment"""
        if self.subsegment:
            try:
                self.subsegment.put_annotation(key, value)
            except Exception as e:
                log.debug(f"Failed to add annotation: {e}")
    
    def put_metadata(self, key: str, value: Any, namespace: str = "default"):
        """Add metadata to subsegment"""
        if self.subsegment:
            try:
                self.subsegment.put_metadata(key, value, namespace)
            except Exception as e:
                log.debug(f"Failed to add metadata: {e}")
