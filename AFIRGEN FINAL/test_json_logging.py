"""
Test script for structured JSON logging implementation
Validates that logs are properly formatted as JSON with all required fields
"""

import json
import sys
import os
import tempfile
from pathlib import Path
from io import StringIO

# Add main backend to path
sys.path.insert(0, str(Path(__file__).parent / "main backend"))

from json_logging import (
    setup_json_logging,
    log_with_context,
    log_request,
    log_response,
    log_error,
    log_performance,
    log_security_event,
    JSONFormatter
)


def test_json_formatter():
    """Test that JSONFormatter produces valid JSON"""
    print("Testing JSONFormatter...")
    
    formatter = JSONFormatter(
        service_name="test-service",
        environment="test"
    )
    
    import logging
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="/test/file.py",
        lineno=42,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    formatted = formatter.format(record)
    
    # Validate it's valid JSON
    try:
        log_data = json.loads(formatted)
        print("✓ Valid JSON output")
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}")
        return False
    
    # Check required fields
    required_fields = ["timestamp", "level", "logger", "message", "service", "environment", "source", "process"]
    for field in required_fields:
        if field not in log_data:
            print(f"✗ Missing required field: {field}")
            return False
    
    print(f"✓ All required fields present: {', '.join(required_fields)}")
    
    # Validate field types
    assert isinstance(log_data["timestamp"], str), "timestamp should be string"
    assert isinstance(log_data["level"], str), "level should be string"
    assert isinstance(log_data["message"], str), "message should be string"
    assert isinstance(log_data["source"], dict), "source should be dict"
    assert isinstance(log_data["process"], dict), "process should be dict"
    
    print("✓ Field types correct")
    
    return True


def test_exception_logging():
    """Test that exceptions are properly logged"""
    print("\nTesting exception logging...")
    
    formatter = JSONFormatter(service_name="test-service")
    
    import logging
    
    try:
        raise ValueError("Test exception")
    except ValueError:
        import sys
        exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/test/file.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        if "exception" not in log_data:
            print("✗ Exception info not in log")
            return False
        
        exc = log_data["exception"]
        if "type" not in exc or "message" not in exc or "traceback" not in exc:
            print("✗ Exception missing required fields")
            return False
        
        if exc["type"] != "ValueError":
            print(f"✗ Wrong exception type: {exc['type']}")
            return False
        
        if "Test exception" not in exc["message"]:
            print(f"✗ Wrong exception message: {exc['message']}")
            return False
        
        print("✓ Exception properly logged with type, message, and traceback")
        return True


def test_extra_fields():
    """Test that extra context fields are included"""
    print("\nTesting extra context fields...")
    
    formatter = JSONFormatter(service_name="test-service")
    
    import logging
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="/test/file.py",
        lineno=42,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    # Add extra fields
    record.user_id = "user123"
    record.request_id = "req-456"
    record.duration_ms = 150.5
    
    formatted = formatter.format(record)
    log_data = json.loads(formatted)
    
    if "extra" not in log_data:
        print("✗ Extra fields not in log")
        return False
    
    extra = log_data["extra"]
    if extra.get("user_id") != "user123":
        print(f"✗ Wrong user_id: {extra.get('user_id')}")
        return False
    
    if extra.get("request_id") != "req-456":
        print(f"✗ Wrong request_id: {extra.get('request_id')}")
        return False
    
    if extra.get("duration_ms") != 150.5:
        print(f"✗ Wrong duration_ms: {extra.get('duration_ms')}")
        return False
    
    print("✓ Extra context fields properly included")
    return True


def test_setup_json_logging():
    """Test the setup_json_logging function"""
    print("\nTesting setup_json_logging...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        
        logger = setup_json_logging(
            service_name="test-service",
            log_level="INFO",
            log_file=str(log_file),
            environment="test",
            enable_console=False
        )
        
        # Log a message
        logger.info("Test log message", extra={"test_field": "test_value"})
        
        # Close all handlers to release file lock (Windows)
        import logging
        for handler in logging.getLogger().handlers[:]:
            handler.close()
            logging.getLogger().removeHandler(handler)
        
        # Check file was created
        if not log_file.exists():
            print(f"✗ Log file not created: {log_file}")
            return False
        
        # Read and validate log
        with open(log_file, 'r') as f:
            log_line = f.read().strip()
        
        try:
            log_data = json.loads(log_line)
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON in log file: {e}")
            return False
        
        if log_data.get("message") != "Test log message":
            print(f"✗ Wrong message: {log_data.get('message')}")
            return False
        
        if log_data.get("service") != "test-service":
            print(f"✗ Wrong service: {log_data.get('service')}")
            return False
        
        if log_data.get("environment") != "test":
            print(f"✗ Wrong environment: {log_data.get('environment')}")
            return False
        
        if log_data.get("extra", {}).get("test_field") != "test_value":
            print(f"✗ Extra field not found or wrong value")
            return False
        
        print("✓ setup_json_logging works correctly")
        print(f"✓ Log file created successfully")
        return True


def test_convenience_functions():
    """Test convenience logging functions"""
    print("\nTesting convenience functions...")
    
    import logging
    from io import StringIO
    
    # Capture logs
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    
    from json_logging import JSONFormatter
    formatter = JSONFormatter(service_name="test-service")
    handler.setFormatter(formatter)
    
    logger = logging.getLogger("test-convenience")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Test log_request
    log_request(logger, "GET", "/api/test", "192.168.1.1", user_id="user123")
    
    # Test log_response
    log_response(logger, "GET", "/api/test", 200, 150.5)
    
    # Test log_performance
    log_performance(logger, "database_query", 45.2, success=True, rows=100)
    
    # Test log_security_event
    log_security_event(logger, "auth_failure", "warning", "Invalid API key", ip="192.168.1.1")
    
    # Get logs
    log_output = log_stream.getvalue()
    log_lines = [line for line in log_output.strip().split('\n') if line]
    
    if len(log_lines) != 4:
        print(f"✗ Expected 4 log lines, got {len(log_lines)}")
        return False
    
    # Validate each log is valid JSON
    for i, line in enumerate(log_lines):
        try:
            log_data = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"✗ Log line {i+1} is not valid JSON: {e}")
            return False
    
    print("✓ All convenience functions work correctly")
    return True


def test_log_levels():
    """Test different log levels"""
    print("\nTesting log levels...")
    
    import logging
    from io import StringIO
    
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    
    from json_logging import JSONFormatter
    formatter = JSONFormatter(service_name="test-service")
    handler.setFormatter(formatter)
    
    logger = logging.getLogger("test-levels")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    # Test all levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
    
    log_output = log_stream.getvalue()
    log_lines = [line for line in log_output.strip().split('\n') if line]
    
    if len(log_lines) != 5:
        print(f"✗ Expected 5 log lines, got {len(log_lines)}")
        return False
    
    expected_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    for i, (line, expected_level) in enumerate(zip(log_lines, expected_levels)):
        log_data = json.loads(line)
        if log_data["level"] != expected_level:
            print(f"✗ Log {i+1}: expected level {expected_level}, got {log_data['level']}")
            return False
    
    print("✓ All log levels work correctly")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("JSON Logging Implementation Tests")
    print("=" * 60)
    
    tests = [
        test_json_formatter,
        test_exception_logging,
        test_extra_fields,
        test_setup_json_logging,
        test_convenience_functions,
        test_log_levels,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓ All tests passed! JSON logging is working correctly.")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
