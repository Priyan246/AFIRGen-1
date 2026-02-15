"""
Integration test for JSON logging with FastAPI
Demonstrates JSON logging in a realistic application context
"""

import sys
import json
from pathlib import Path
from io import StringIO
import logging

# Add main backend to path
sys.path.insert(0, str(Path(__file__).parent / "main backend"))

from json_logging import (
    setup_json_logging,
    log_with_context,
    log_request,
    log_response,
    log_error,
    log_performance,
    log_security_event
)


def simulate_fir_generation():
    """Simulate FIR generation workflow with JSON logging"""
    
    # Capture logs
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    
    from json_logging import JSONFormatter
    formatter = JSONFormatter(service_name="main-backend", environment="test")
    handler.setFormatter(formatter)
    
    logger = logging.getLogger("integration-test")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    print("Simulating FIR generation workflow...")
    print("=" * 60)
    
    # 1. Log incoming request
    log_request(
        logger, "POST", "/api/process",
        client_ip="192.168.1.100",
        user_id="user-123"
    )
    
    # 2. Log session creation
    log_with_context(
        logger, "info", "Session created",
        session_id="abc-123",
        user_id="user-123"
    )
    
    # 3. Log ASR processing
    log_performance(
        logger, "whisper_transcribe",
        duration_ms=2500.5,
        success=True,
        audio_duration_sec=30.5
    )
    
    # 4. Log OCR processing
    log_performance(
        logger, "dots_ocr",
        duration_ms=1200.3,
        success=True,
        images_processed=2
    )
    
    # 5. Log summary generation
    log_performance(
        logger, "generate_summary",
        duration_ms=800.2,
        success=True,
        tokens_generated=150
    )
    
    # 6. Log violation checking
    log_with_context(
        logger, "info", "Checking violations",
        session_id="abc-123",
        summary_length=500
    )
    
    log_performance(
        logger, "find_violations",
        duration_ms=1500.7,
        success=True,
        violations_found=3
    )
    
    # 7. Log FIR generation
    log_with_context(
        logger, "info", "FIR generated successfully",
        session_id="abc-123",
        fir_number="FIR-2024-001",
        violations_count=3
    )
    
    # 8. Log database save
    log_performance(
        logger, "database_save",
        duration_ms=45.2,
        success=True,
        fir_number="FIR-2024-001"
    )
    
    # 9. Log response
    log_response(
        logger, "POST", "/api/process",
        status_code=200,
        duration_ms=6046.9,
        session_id="abc-123",
        fir_number="FIR-2024-001"
    )
    
    # Get logs
    log_output = log_stream.getvalue()
    log_lines = [line for line in log_output.strip().split('\n') if line]
    
    print(f"\nGenerated {len(log_lines)} log entries\n")
    
    # Parse and display logs
    for i, line in enumerate(log_lines, 1):
        try:
            log_data = json.loads(line)
            print(f"Log {i}:")
            print(f"  Timestamp: {log_data['timestamp']}")
            print(f"  Level: {log_data['level']}")
            print(f"  Message: {log_data['message']}")
            
            if 'extra' in log_data:
                print(f"  Context:")
                for key, value in log_data['extra'].items():
                    print(f"    {key}: {value}")
            
            print()
            
        except json.JSONDecodeError as e:
            print(f"✗ Log {i} is not valid JSON: {e}")
            return False
    
    print("=" * 60)
    print(f"✓ All {len(log_lines)} logs are valid JSON")
    print("✓ FIR generation workflow logged successfully")
    
    return True


def simulate_error_scenario():
    """Simulate error scenario with exception logging"""
    
    # Capture logs
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    
    from json_logging import JSONFormatter
    formatter = JSONFormatter(service_name="main-backend", environment="test")
    handler.setFormatter(formatter)
    
    logger = logging.getLogger("error-test")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    print("\nSimulating error scenario...")
    print("=" * 60)
    
    # 1. Log request
    log_request(
        logger, "POST", "/api/process",
        client_ip="192.168.1.100",
        user_id="user-456"
    )
    
    # 2. Simulate error
    try:
        raise ValueError("Invalid audio format: expected WAV, got MP3")
    except Exception as e:
        log_error(
            logger, "Audio processing failed",
            error=e,
            session_id="def-456",
            file_type="MP3"
        )
    
    # 3. Log response with error
    log_response(
        logger, "POST", "/api/process",
        status_code=400,
        duration_ms=150.5,
        session_id="def-456",
        error="Invalid audio format"
    )
    
    # Get logs
    log_output = log_stream.getvalue()
    log_lines = [line for line in log_output.strip().split('\n') if line]
    
    print(f"\nGenerated {len(log_lines)} log entries\n")
    
    # Check error log has exception details
    error_log = None
    for line in log_lines:
        log_data = json.loads(line)
        if log_data['level'] == 'ERROR':
            error_log = log_data
            break
    
    if not error_log:
        print("✗ No ERROR log found")
        return False
    
    print("Error Log Details:")
    print(f"  Message: {error_log['message']}")
    print(f"  Exception Type: {error_log['exception']['type']}")
    print(f"  Exception Message: {error_log['exception']['message']}")
    print(f"  Has Traceback: {'traceback' in error_log['exception']}")
    
    if 'extra' in error_log:
        print(f"  Context:")
        for key, value in error_log['extra'].items():
            print(f"    {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✓ Error scenario logged correctly with exception details")
    
    return True


def simulate_security_events():
    """Simulate security events logging"""
    
    # Capture logs
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    
    from json_logging import JSONFormatter
    formatter = JSONFormatter(service_name="main-backend", environment="test")
    handler.setFormatter(formatter)
    
    logger = logging.getLogger("security-test")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    print("\nSimulating security events...")
    print("=" * 60)
    
    # 1. Authentication failure
    log_security_event(
        logger, "auth_failure",
        severity="warning",
        description="Invalid API key provided",
        ip_address="192.168.1.200",
        endpoint="/api/process",
        api_key_prefix="abc123..."
    )
    
    # 2. Rate limit exceeded
    log_security_event(
        logger, "rate_limit_exceeded",
        severity="warning",
        description="Client exceeded rate limit",
        ip_address="192.168.1.200",
        requests_count=150,
        limit=100
    )
    
    # 3. Suspicious activity
    log_security_event(
        logger, "suspicious_activity",
        severity="error",
        description="Multiple failed authentication attempts",
        ip_address="192.168.1.200",
        failed_attempts=5,
        time_window_sec=60
    )
    
    # Get logs
    log_output = log_stream.getvalue()
    log_lines = [line for line in log_output.strip().split('\n') if line]
    
    print(f"\nGenerated {len(log_lines)} security event logs\n")
    
    # Verify security events
    for i, line in enumerate(log_lines, 1):
        log_data = json.loads(line)
        
        if not log_data.get('extra', {}).get('security_event'):
            print(f"✗ Log {i} is not tagged as security event")
            return False
        
        print(f"Security Event {i}:")
        print(f"  Type: {log_data['extra']['event_type']}")
        print(f"  Severity: {log_data['level']}")
        print(f"  Description: {log_data['extra']['description']}")
        print(f"  IP: {log_data['extra'].get('ip_address', 'N/A')}")
        print()
    
    print("=" * 60)
    print("✓ All security events properly tagged and logged")
    
    return True


def main():
    """Run integration tests"""
    print("=" * 60)
    print("JSON Logging Integration Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("FIR Generation Workflow", simulate_fir_generation),
        ("Error Scenario", simulate_error_scenario),
        ("Security Events", simulate_security_events),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\nTest: {test_name}")
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {test_name} failed")
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Integration Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓ All integration tests passed!")
        print("✓ JSON logging is production-ready")
        return 0
    else:
        print(f"\n✗ {failed} integration test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
