"""
Structured JSON Logging Configuration for AFIRGen
Provides consistent JSON-formatted logging across all services
"""

import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    Outputs logs in JSON format with consistent fields.
    """
    
    def __init__(
        self,
        service_name: str = "afirgen",
        environment: str = "production",
        include_extra: bool = True
    ):
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string"""
        
        # Base log structure
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "environment": self.environment,
        }
        
        # Add source location
        log_data["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }
        
        # Add process/thread info
        log_data["process"] = {
            "pid": record.process,
            "thread": record.thread,
            "thread_name": record.threadName,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self._format_exception(record.exc_info),
            }
        
        # Add extra fields from record
        if self.include_extra:
            extra_fields = self._extract_extra_fields(record)
            if extra_fields:
                log_data["extra"] = extra_fields
        
        return json.dumps(log_data, default=str)
    
    def _format_exception(self, exc_info) -> str:
        """Format exception traceback as string"""
        return "".join(traceback.format_exception(*exc_info))
    
    def _extract_extra_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract custom fields added to log record"""
        # Standard LogRecord attributes to exclude
        standard_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName', 'levelname',
            'levelno', 'lineno', 'module', 'msecs', 'message', 'pathname', 'process',
            'processName', 'relativeCreated', 'thread', 'threadName', 'exc_info',
            'exc_text', 'stack_info', 'getMessage', 'taskName'
        }
        
        extra = {}
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith('_'):
                extra[key] = value
        
        return extra


def setup_json_logging(
    service_name: str,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    environment: str = "production",
    enable_console: bool = True,
) -> logging.Logger:
    """
    Configure structured JSON logging for a service.
    
    Args:
        service_name: Name of the service (e.g., "main-backend", "gguf-server")
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        environment: Environment name (dev, staging, production)
        enable_console: Whether to enable console output
    
    Returns:
        Configured logger instance
    """
    
    # Create formatter
    formatter = JSONFormatter(
        service_name=service_name,
        environment=environment,
        include_extra=True
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Create service-specific logger
    logger = logging.getLogger(service_name)
    
    return logger


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **context
):
    """
    Log a message with additional context fields.
    
    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **context: Additional context fields to include in log
    
    Example:
        log_with_context(
            logger, "info", "FIR generated",
            fir_number="FIR123",
            session_id="abc-123",
            duration_ms=1500
        )
    """
    log_func = getattr(logger, level.lower())
    log_func(message, extra=context)


# Convenience functions for common logging patterns
def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    client_ip: str,
    **extra
):
    """Log HTTP request"""
    log_with_context(
        logger, "info", f"{method} {path}",
        request_method=method,
        request_path=path,
        client_ip=client_ip,
        **extra
    )


def log_response(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    **extra
):
    """Log HTTP response"""
    log_with_context(
        logger, "info", f"{method} {path} - {status_code}",
        request_method=method,
        request_path=path,
        status_code=status_code,
        duration_ms=duration_ms,
        **extra
    )


def log_error(
    logger: logging.Logger,
    message: str,
    error: Optional[Exception] = None,
    **context
):
    """Log error with exception details"""
    if error:
        logger.error(message, exc_info=error, extra=context)
    else:
        log_with_context(logger, "error", message, **context)


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    success: bool = True,
    **metrics
):
    """Log performance metrics"""
    log_with_context(
        logger, "info", f"Performance: {operation}",
        operation=operation,
        duration_ms=duration_ms,
        success=success,
        **metrics
    )


def log_security_event(
    logger: logging.Logger,
    event_type: str,
    severity: str,
    description: str,
    **details
):
    """Log security-related events"""
    log_with_context(
        logger, severity.lower(), f"Security: {event_type}",
        event_type=event_type,
        security_event=True,
        description=description,
        **details
    )
