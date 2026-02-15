# Structured JSON Logging for AFIRGen

## Overview

AFIRGen now uses structured JSON logging across all services, providing consistent, machine-readable logs ideal for production monitoring and debugging.

## Quick Start

### Basic Usage

```python
from json_logging import setup_json_logging

# Configure logging for your service
log = setup_json_logging(
    service_name="my-service",
    log_level="INFO",
    log_file="logs/my_service.log"
)

# Log messages
log.info("Service started")
log.warning("High memory usage")
log.error("Operation failed")
```

### Logging with Context

```python
from json_logging import log_with_context

log_with_context(
    log, "info", "FIR generated",
    fir_number="FIR-2024-001",
    session_id="abc-123",
    duration_ms=1500
)
```

### Output

```json
{
  "timestamp": "2024-02-12T10:30:45.123456Z",
  "level": "INFO",
  "logger": "my-service",
  "message": "FIR generated",
  "service": "my-service",
  "environment": "production",
  "source": {
    "file": "/app/service.py",
    "line": 123,
    "function": "generate_fir"
  },
  "process": {
    "pid": 42,
    "thread": 140234567890,
    "thread_name": "MainThread"
  },
  "extra": {
    "fir_number": "FIR-2024-001",
    "session_id": "abc-123",
    "duration_ms": 1500
  }
}
```

## Features

- ✅ **Machine-Readable**: JSON format for easy parsing
- ✅ **Structured Context**: Consistent field names
- ✅ **Exception Tracking**: Full traceback in structured format
- ✅ **Performance Monitoring**: Built-in performance logging
- ✅ **Security Auditing**: Tagged security events
- ✅ **CloudWatch Ready**: Compatible with CloudWatch Logs Insights

## Services Using JSON Logging

1. **Main Backend** (`main-backend`)
2. **GGUF Model Server** (`gguf-server`)
3. **ASR/OCR Server** (`asr-ocr-server`)

## Configuration

### Environment Variables

```bash
export LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
export ENVIRONMENT=production  # dev, staging, production
```

### Log Files

- `logs/main_backend.log`
- `logs/gguf_server.log`
- `logs/asr_ocr_server.log`

## Common Patterns

### HTTP Request/Response

```python
from json_logging import log_request, log_response

log_request(log, "POST", "/api/process", "192.168.1.1", user_id="user-123")
log_response(log, "POST", "/api/process", 200, 1234.5, session_id="abc-123")
```

### Performance Metrics

```python
from json_logging import log_performance

log_performance(
    log, "database_query",
    duration_ms=45.2,
    success=True,
    rows=100
)
```

### Error Handling

```python
from json_logging import log_error

try:
    risky_operation()
except Exception as e:
    log_error(log, "Operation failed", error=e, operation="risky_operation")
```

### Security Events

```python
from json_logging import log_security_event

log_security_event(
    log, "auth_failure",
    severity="warning",
    description="Invalid API key",
    ip="192.168.1.1"
)
```

## CloudWatch Integration

### Query Examples

Find all errors:
```sql
fields @timestamp, message, exception.type
| filter level = "ERROR"
| sort @timestamp desc
```

Performance metrics:
```sql
fields @timestamp, extra.duration_ms
| filter message like /completed/
| stats avg(extra.duration_ms), max(extra.duration_ms)
```

Security events:
```sql
fields @timestamp, extra.ip_address
| filter extra.security_event = true
| stats count() by extra.ip_address
```

## Testing

Run the test suite:

```bash
cd "AFIRGEN FINAL"
python test_json_logging.py
```

Expected output:
```
============================================================
JSON Logging Implementation Tests
============================================================
✓ All tests passed! JSON logging is working correctly.
```

## Documentation

- **Implementation Guide**: `JSON-LOGGING-IMPLEMENTATION.md`
- **Quick Reference**: `JSON-LOGGING-QUICK-REFERENCE.md`
- **Summary**: `JSON-LOGGING-SUMMARY.md`
- **Validation Checklist**: `JSON-LOGGING-VALIDATION-CHECKLIST.md`

## Best Practices

### Do ✓

- Use context fields for structured data
- Include relevant IDs (session_id, user_id, fir_number)
- Log performance metrics
- Use appropriate log levels
- Log security events with proper tagging

### Don't ✗

- Log passwords or API keys
- Log large payloads
- Use string formatting instead of context fields
- Log PII without proper handling
- Ignore log levels

## Troubleshooting

### Logs Not Appearing

1. Check log level: `export LOG_LEVEL=DEBUG`
2. Verify log directory: `mkdir -p logs`
3. Check file permissions

### Invalid JSON

1. Ensure extra fields are JSON-serializable
2. Check for circular references
3. Use `default=str` for custom objects

### Performance Issues

1. Reduce log level
2. Use appropriate log levels
3. Consider log sampling for high volume

## Support

For questions or issues:
1. See `JSON-LOGGING-IMPLEMENTATION.md` for detailed guide
2. See `JSON-LOGGING-QUICK-REFERENCE.md` for examples
3. Run `python test_json_logging.py` to validate setup

## Version

- **Version**: 1.0.0
- **Status**: Production Ready
- **Last Updated**: 2024-02-12
