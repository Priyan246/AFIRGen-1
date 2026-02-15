# xray_tracing.py - Simplified X-Ray integration for model servers
# -------------------------------------------------------------

import os
import logging
from typing import Optional

# X-Ray SDK imports
from aws_xray_sdk.core import xray_recorder, patch_all
from aws_xray_sdk.ext.fastapi.middleware import XRayMiddleware

log = logging.getLogger(__name__)

# Configuration
XRAY_CONFIG = {
    "enabled": os.getenv("XRAY_ENABLED", "true").lower() == "true",
    "sampling_rate": float(os.getenv("XRAY_SAMPLING_RATE", "0.1")),
    "daemon_address": os.getenv("XRAY_DAEMON_ADDRESS", "127.0.0.1:2000"),
    "context_missing": os.getenv("XRAY_CONTEXT_MISSING", "LOG_ERROR"),
}


def setup_xray(app, service_name: str):
    """
    Configure AWS X-Ray for FastAPI application
    
    Args:
        app: FastAPI application instance
        service_name: Service name for X-Ray
    """
    if not XRAY_CONFIG["enabled"]:
        log.info("X-Ray tracing is disabled")
        return
    
    try:
        # Configure X-Ray recorder
        xray_recorder.configure(
            service=service_name,
            sampling=XRAY_CONFIG["sampling_rate"] < 1.0,
            context_missing=XRAY_CONFIG["context_missing"],
            daemon_address=XRAY_CONFIG["daemon_address"],
        )
        
        # Patch supported libraries
        patch_all()
        
        # Add X-Ray middleware to FastAPI
        app.add_middleware(XRayMiddleware, recorder=xray_recorder)
        
        log.info(f"✅ X-Ray tracing enabled for service: {service_name}")
        log.info(f"   Sampling rate: {XRAY_CONFIG['sampling_rate'] * 100}%")
        log.info(f"   Daemon address: {XRAY_CONFIG['daemon_address']}")
        
    except Exception as e:
        log.error(f"Failed to configure X-Ray: {e}")
        if XRAY_CONFIG["context_missing"] == "RUNTIME_ERROR":
            raise


def add_trace_annotation(key: str, value):
    """Add annotation to current X-Ray segment"""
    if not XRAY_CONFIG["enabled"]:
        return
    
    try:
        current_segment = xray_recorder.current_segment()
        if current_segment:
            current_segment.put_annotation(key, value)
    except Exception as e:
        log.debug(f"Failed to add X-Ray annotation: {e}")


def add_trace_metadata(key: str, value, namespace: str = "default"):
    """Add metadata to current X-Ray segment"""
    if not XRAY_CONFIG["enabled"]:
        return
    
    try:
        current_segment = xray_recorder.current_segment()
        if current_segment:
            current_segment.put_metadata(key, value, namespace)
    except Exception as e:
        log.debug(f"Failed to add X-Ray metadata: {e}")
