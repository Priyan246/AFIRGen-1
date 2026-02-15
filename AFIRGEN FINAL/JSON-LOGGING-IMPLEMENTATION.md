# Structured JSON Logging Implementation

## Overview

AFIRGen now uses structured JSON logging across all services, providing consistent, machine-readable logs that are ideal for log aggregation systems like CloudWatch Logs, ELK Stack, or Splunk.

## What Changed

### Before
```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("fir_pipeline.log"), logging.StreamHandler()],
)
log = logging.getLogger("pipeline")
log.info("Processing FIR request")
```

Output:
```
2024-02-12 10:30:45 [INFO] Processing FIR request
```

### After
```python
from json_logging import setup_json_logging, log_with_context

log = setup_json_logging(
    service_name="main-backend",
    log_level="INFO",
    log_file="logs/main_backend.log",
    environment="production"
)

log_with_context(
    log, "info", "Processing FIR request",
    session_id="abc-123",
    user_id="user-456"
)
```

Output:
```json
{
  "timestamp": "2024-02-12T10:30:45.123456Z",
  "level": "INFO",
  "logger": "main-backend",
  "message": "Processing FIR request",
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
    "user_id": "user-456"
  }
}
```

## Benefits

1. **Machine-Readable**: Logs can be easily parsed and analyzed by log aggregation tools
2. **Structured Context**: Additional context fields are included in a consistent format
3. **Better Searchability**: Query logs by specific fields (e.g., all logs for a session_id)
4. **Exception Tracking**: Exceptions include full traceback in structured format
5. **Performance Monitoring**: Easy to extract metrics from logs
6. **Security Auditing**: Security events are clearly tagged and searchable

## Implementation Details

### Core Module: `json_logging.py`

Located in `main backend/json_logging.py`, this module provides:

- `JSONFormatter`: Custom formatter that outputs logs as JSON
- `setup_json_logging()`: Configure logging for a service
- Convenience functions for common logging patterns

### Services Updated

1. **Main Backend** (`main backend/agentv5.py`)
   - Service name: `main-backend`
   - Log file: `logs/main_backend.log`

2. **GGUF Model Server** (`gguf model server/llm_server.py`)
   - Service name: `gguf-server`
   - Log file: `logs/gguf_server.log`

3. **ASR/OCR Server** (`asr ocr model server/asr_ocr.py`)
   - Service name: `asr-ocr-server`
   - Log file: `logs/asr_ocr_server.log`

4. **Supporting Modules**
   - `secrets_manager.py`: Uses structured logging
   - `input_validation.py`: Uses structured logging
   - `reliability.py`: Uses structured logging

## Log Structure

Every log entry includes:

### Standard Fields
- `timestamp`: ISO 8601 UTC timestamp
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logger`: Logger name
- `message`: Log message
- `service`: Service name
- `environment`: Environment (dev, staging, production)

### Source Information
- `source.file`: Source file path
- `source.line`: Line number
- `source.function`: Function name

### Process Information
- `process.pid`: Process ID
- `process.thread`: Thread ID
- `process.thread_name`: Thread name

### Optional Fields
- `extra`: Custom context fields
- `exception`: Exception details (type, message, traceback)

## Usage Examples

### Basic Logging

```python
from json_logging import setup_json_logging

log = setup_json_logging(
    service_name="my-service",
    log_level="INFO",
    log_file="logs/my_service.log"
)

log.info("Service started")
log.warning("High memory usage detected")
log.error("Database connection failed")
```

### Logging with Context

```python
from json_logging import log_with_context

log_with_context(
    log, "info", "FIR generated successfully",
    fir_number="FIR-2024-001",
    session_id="abc-123",
    duration_ms=1500,
    violations_found=3
)
```

### HTTP Request/Response Logging

```python
from json_logging import log_request, log_response

# Log incoming request
log_request(
    log, "POST", "/api/process",
    client_ip="192.168.1.100",
    user_id="user-123"
)

# Log response
log_response(
    log, "POST", "/api/process",
    status_code=200,
    duration_ms=1234.5,
    session_id="abc-123"
)
```

### Performance Logging

```python
from json_logging import log_performance

log_performance(
    log, "database_query",
    duration_ms=45.2,
    success=True,
    rows_returned=100,
    query_type="SELECT"
)
```

### Security Event Logging

```python
from json_logging import log_security_event

log_security_event(
    log, "auth_failure",
    severity="warning",
    description="Invalid API key provided",
    ip_address="192.168.1.100",
    endpoint="/api/process"
)
```

### Error Logging with Exceptions

```python
from json_logging import log_error

try:
    # Some operation
    result = risky_operation()
except Exception as e:
    log_error(
        log, "Operation failed",
        error=e,
        operation="risky_operation",
        input_data=input_value
    )
```

## Configuration

### Environment Variables

- `LOG_LEVEL`: Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Default: `INFO`
  - Example: `export LOG_LEVEL=DEBUG`

- `ENVIRONMENT`: Set environment name
  - Default: `production`
  - Values: `dev`, `staging`, `production`
  - Example: `export ENVIRONMENT=staging`

### Log Files

All services write logs to the `logs/` directory:
- `logs/main_backend.log`
- `logs/gguf_server.log`
- `logs/asr_ocr_server.log`

Logs are also output to console (stdout) for Docker container logging.

## CloudWatch Integration

JSON logs are ideal for CloudWatch Logs:

1. **Log Groups**: Create separate log groups per service
   - `/aws/ecs/afirgen/main-backend`
   - `/aws/ecs/afirgen/gguf-server`
   - `/aws/ecs/afirgen/asr-ocr-server`

2. **CloudWatch Insights Queries**:

```sql
-- Find all errors in the last hour
fields @timestamp, message, exception.type, exception.message
| filter level = "ERROR"
| sort @timestamp desc
| limit 100

-- Track FIR generation performance
fields @timestamp, extra.fir_number, extra.duration_ms
| filter message like /FIR generated/
| stats avg(extra.duration_ms) as avg_duration, 
        max(extra.duration_ms) as max_duration,
        count() as total_firs
        by bin(5m)

-- Monitor authentication failures
fields @timestamp, extra.ip_address, extra.endpoint
| filter extra.security_event = true and extra.event_type = "auth_failure"
| stats count() by extra.ip_address
| sort count desc

-- Track session lifecycle
fields @timestamp, message, extra.session_id
| filter extra.session_id = "abc-123"
| sort @timestamp asc
```

3. **Metric Filters**: Create CloudWatch metrics from logs
   - Error rate: Count of `level = "ERROR"`
   - Response time: Extract `extra.duration_ms`
   - Auth failures: Count of `extra.event_type = "auth_failure"`

## Testing

Run the test suite to validate JSON logging:

```bash
cd "AFIRGEN FINAL"
python test_json_logging.py
```

Tests validate:
- JSON format correctness
- Required fields presence
- Exception logging
- Extra context fields
- Log levels
- Convenience functions

## Migration Guide

### For Existing Code

Replace old logging patterns:

**Old:**
```python
log.info(f"Processing session {session_id}")
```

**New:**
```python
log_with_context(log, "info", "Processing session", session_id=session_id)
```

**Old:**
```python
log.error(f"Failed to process: {str(e)}")
```

**New:**
```python
log_error(log, "Failed to process", error=e, session_id=session_id)
```

### For New Code

Use convenience functions for common patterns:
- `log_request()` for HTTP requests
- `log_response()` for HTTP responses
- `log_performance()` for performance metrics
- `log_security_event()` for security events
- `log_error()` for errors with exceptions

## Best Practices

1. **Include Context**: Always add relevant context fields
   ```python
   log_with_context(log, "info", "Operation completed",
                    session_id=session_id,
                    operation="generate_fir",
                    duration_ms=duration)
   ```

2. **Use Appropriate Levels**:
   - `DEBUG`: Detailed diagnostic information
   - `INFO`: General informational messages
   - `WARNING`: Warning messages for potentially harmful situations
   - `ERROR`: Error messages for failures
   - `CRITICAL`: Critical messages for severe failures

3. **Log Structured Data**: Use extra fields instead of string formatting
   ```python
   # Good
   log_with_context(log, "info", "User action", user_id=user_id, action="login")
   
   # Avoid
   log.info(f"User {user_id} performed action: login")
   ```

4. **Security Sensitive Data**: Never log passwords, API keys, or PII
   ```python
   # Bad
   log_with_context(log, "info", "Auth attempt", password=password)
   
   # Good
   log_with_context(log, "info", "Auth attempt", user_id=user_id)
   ```

5. **Performance**: Log performance metrics for monitoring
   ```python
   start = time.time()
   result = expensive_operation()
   duration_ms = (time.time() - start) * 1000
   
   log_performance(log, "expensive_operation", duration_ms, success=True)
   ```

## Troubleshooting

### Logs Not Appearing

1. Check log level: `export LOG_LEVEL=DEBUG`
2. Verify log directory exists: `mkdir -p logs`
3. Check file permissions

### Invalid JSON in Logs

1. Ensure all extra fields are JSON-serializable
2. Use `default=str` for custom objects
3. Check for circular references

### Performance Impact

JSON logging has minimal overhead:
- ~0.1-0.5ms per log entry
- Use appropriate log levels to reduce volume
- Consider async logging for high-throughput scenarios

## Future Enhancements

Potential improvements:
1. Async logging for better performance
2. Log rotation and compression
3. Sampling for high-volume logs
4. Integration with distributed tracing (X-Ray)
5. Custom log processors for sensitive data masking

## Related Documentation

- [CloudWatch Logs Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/)
- [CloudWatch Insights Query Syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html)
- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
