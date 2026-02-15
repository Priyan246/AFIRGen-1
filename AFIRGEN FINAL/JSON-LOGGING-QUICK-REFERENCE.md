# JSON Logging Quick Reference

## Setup

```python
from json_logging import setup_json_logging

log = setup_json_logging(
    service_name="my-service",
    log_level="INFO",
    log_file="logs/my_service.log",
    environment="production"
)
```

## Basic Logging

```python
log.info("Simple message")
log.warning("Warning message")
log.error("Error message")
```

## Logging with Context

```python
from json_logging import log_with_context

log_with_context(
    log, "info", "Operation completed",
    session_id="abc-123",
    duration_ms=1500,
    success=True
)
```

## HTTP Logging

```python
from json_logging import log_request, log_response

# Request
log_request(log, "POST", "/api/process", "192.168.1.1", user_id="user-123")

# Response
log_response(log, "POST", "/api/process", 200, 1234.5, session_id="abc-123")
```

## Performance Logging

```python
from json_logging import log_performance

log_performance(
    log, "database_query",
    duration_ms=45.2,
    success=True,
    rows=100
)
```

## Error Logging

```python
from json_logging import log_error

try:
    risky_operation()
except Exception as e:
    log_error(log, "Operation failed", error=e, operation="risky_operation")
```

## Security Events

```python
from json_logging import log_security_event

log_security_event(
    log, "auth_failure",
    severity="warning",
    description="Invalid API key",
    ip="192.168.1.1"
)
```

## Log Output Format

```json
{
  "timestamp": "2024-02-12T10:30:45.123456Z",
  "level": "INFO",
  "logger": "main-backend",
  "message": "Operation completed",
  "service": "main-backend",
  "environment": "production",
  "source": {
    "file": "/app/agentv5.py",
    "line": 1234,
    "function": "process_endpoint"
  },
  "process": {
    "pid": 42,
    "thread": 140234567890,
    "thread_name": "MainThread"
  },
  "extra": {
    "session_id": "abc-123",
    "duration_ms": 1500,
    "success": true
  }
}
```

## Environment Variables

```bash
export LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
export ENVIRONMENT=production  # dev, staging, production
```

## CloudWatch Queries

### Find Errors
```sql
fields @timestamp, message, exception.type
| filter level = "ERROR"
| sort @timestamp desc
```

### Performance Metrics
```sql
fields @timestamp, extra.duration_ms
| filter message like /completed/
| stats avg(extra.duration_ms), max(extra.duration_ms)
```

### Security Events
```sql
fields @timestamp, extra.ip_address
| filter extra.security_event = true
| stats count() by extra.ip_address
```

## Testing

```bash
cd "AFIRGEN FINAL"
python test_json_logging.py
```

## Log Files

- Main Backend: `logs/main_backend.log`
- GGUF Server: `logs/gguf_server.log`
- ASR/OCR Server: `logs/asr_ocr_server.log`

## Best Practices

✓ Use context fields instead of string formatting
✓ Include relevant IDs (session_id, user_id, fir_number)
✓ Log performance metrics for monitoring
✓ Use appropriate log levels
✗ Never log passwords or API keys
✗ Avoid logging large payloads
