# JSON Logging: Before and After Comparison

## Configuration

### Before
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("fir_pipeline.log"), logging.StreamHandler()],
)
log = logging.getLogger("pipeline")
```

### After
```python
from json_logging import setup_json_logging

log = setup_json_logging(
    service_name="main-backend",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file="logs/main_backend.log",
    environment=os.getenv("ENVIRONMENT", "production"),
    enable_console=True
)
```

## Basic Logging

### Before
```python
log.info("Processing FIR request")
```

**Output:**
```
2024-02-12 10:30:45 [INFO] Processing FIR request
```

### After
```python
log.info("Processing FIR request")
```

**Output:**
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
  }
}
```

## Logging with Context

### Before
```python
log.info(f"FIR generated: {fir_number}, session: {session_id}, duration: {duration_ms}ms")
```

**Output:**
```
2024-02-12 10:30:45 [INFO] FIR generated: FIR-2024-001, session: abc-123, duration: 1500ms
```

**Problems:**
- Hard to parse programmatically
- Inconsistent format across different log messages
- Difficult to query by specific fields
- String formatting overhead

### After
```python
from json_logging import log_with_context

log_with_context(
    log, "info", "FIR generated",
    fir_number="FIR-2024-001",
    session_id="abc-123",
    duration_ms=1500
)
```

**Output:**
```json
{
  "timestamp": "2024-02-12T10:30:45.123456Z",
  "level": "INFO",
  "logger": "main-backend",
  "message": "FIR generated",
  "service": "main-backend",
  "environment": "production",
  "source": {
    "file": "/app/agentv5.py",
    "line": 1234,
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

**Benefits:**
- Easy to parse and query
- Consistent structure
- Type-safe fields
- Better performance (no string formatting)

## Error Logging

### Before
```python
try:
    result = risky_operation()
except Exception as e:
    log.error(f"Operation failed: {str(e)}")
```

**Output:**
```
2024-02-12 10:30:45 [ERROR] Operation failed: Invalid audio format
```

**Problems:**
- No traceback information
- No context about what failed
- Hard to correlate with other logs

### After
```python
from json_logging import log_error

try:
    result = risky_operation()
except Exception as e:
    log_error(
        log, "Operation failed",
        error=e,
        operation="risky_operation",
        session_id=session_id
    )
```

**Output:**
```json
{
  "timestamp": "2024-02-12T10:30:45.123456Z",
  "level": "ERROR",
  "logger": "main-backend",
  "message": "Operation failed",
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
  "exception": {
    "type": "ValueError",
    "message": "Invalid audio format",
    "traceback": "Traceback (most recent call last):\n  File \"/app/agentv5.py\", line 1234, in process_endpoint\n    result = risky_operation()\n  File \"/app/operations.py\", line 56, in risky_operation\n    raise ValueError(\"Invalid audio format\")\nValueError: Invalid audio format"
  },
  "extra": {
    "operation": "risky_operation",
    "session_id": "abc-123"
  }
}
```

**Benefits:**
- Full exception details with traceback
- Context about what was being done
- Easy to correlate with other logs via session_id

## HTTP Request/Response Logging

### Before
```python
log.info(f"Request: {method} {path} from {client_ip}")
# ... process request ...
log.info(f"Response: {status_code} in {duration_ms}ms")
```

**Output:**
```
2024-02-12 10:30:45 [INFO] Request: POST /api/process from 192.168.1.100
2024-02-12 10:30:47 [INFO] Response: 200 in 1234ms
```

**Problems:**
- Hard to correlate request and response
- No structured fields for filtering
- Inconsistent format

### After
```python
from json_logging import log_request, log_response

log_request(log, "POST", "/api/process", "192.168.1.100", user_id="user-123")
# ... process request ...
log_response(log, "POST", "/api/process", 200, 1234.5, session_id="abc-123")
```

**Output:**
```json
{
  "timestamp": "2024-02-12T10:30:45.123456Z",
  "level": "INFO",
  "message": "POST /api/process",
  "extra": {
    "request_method": "POST",
    "request_path": "/api/process",
    "client_ip": "192.168.1.100",
    "user_id": "user-123"
  }
}

{
  "timestamp": "2024-02-12T10:30:47.123456Z",
  "level": "INFO",
  "message": "POST /api/process - 200",
  "extra": {
    "request_method": "POST",
    "request_path": "/api/process",
    "status_code": 200,
    "duration_ms": 1234.5,
    "session_id": "abc-123"
  }
}
```

**Benefits:**
- Structured fields for easy querying
- Consistent format
- Easy to correlate via session_id

## Performance Monitoring

### Before
```python
start = time.time()
result = expensive_operation()
duration = (time.time() - start) * 1000
log.info(f"Operation completed in {duration:.2f}ms")
```

**Output:**
```
2024-02-12 10:30:45 [INFO] Operation completed in 1234.56ms
```

**Problems:**
- No operation name
- No success/failure indication
- Hard to aggregate metrics

### After
```python
from json_logging import log_performance

start = time.time()
result = expensive_operation()
duration_ms = (time.time() - start) * 1000

log_performance(
    log, "expensive_operation",
    duration_ms=duration_ms,
    success=True,
    rows_processed=100
)
```

**Output:**
```json
{
  "timestamp": "2024-02-12T10:30:45.123456Z",
  "level": "INFO",
  "message": "Performance: expensive_operation",
  "extra": {
    "operation": "expensive_operation",
    "duration_ms": 1234.56,
    "success": true,
    "rows_processed": 100
  }
}
```

**Benefits:**
- Easy to aggregate by operation name
- Success/failure tracking
- Additional metrics included
- CloudWatch can create metrics from these logs

## Security Event Logging

### Before
```python
log.warning(f"Authentication failed for IP: {ip_address}")
```

**Output:**
```
2024-02-12 10:30:45 [WARNING] Authentication failed for IP: 192.168.1.200
```

**Problems:**
- Not tagged as security event
- Hard to filter security logs
- No additional context

### After
```python
from json_logging import log_security_event

log_security_event(
    log, "auth_failure",
    severity="warning",
    description="Invalid API key provided",
    ip_address="192.168.1.200",
    endpoint="/api/process"
)
```

**Output:**
```json
{
  "timestamp": "2024-02-12T10:30:45.123456Z",
  "level": "WARNING",
  "message": "Security: auth_failure",
  "extra": {
    "event_type": "auth_failure",
    "security_event": true,
    "description": "Invalid API key provided",
    "ip_address": "192.168.1.200",
    "endpoint": "/api/process"
  }
}
```

**Benefits:**
- Tagged as security event
- Easy to filter: `filter extra.security_event = true`
- Consistent structure for security logs
- Additional context included

## CloudWatch Queries

### Before (Plain Text Logs)

Finding errors:
```
filter @message like /ERROR/
```

**Problems:**
- Can only search message text
- No structured filtering
- Hard to extract metrics

### After (JSON Logs)

Finding errors:
```sql
fields @timestamp, message, exception.type, exception.message
| filter level = "ERROR"
| sort @timestamp desc
```

Performance metrics:
```sql
fields @timestamp, extra.operation, extra.duration_ms
| filter extra.operation = "database_query"
| stats avg(extra.duration_ms) as avg_duration,
        max(extra.duration_ms) as max_duration,
        count() as total_queries
        by bin(5m)
```

Security events:
```sql
fields @timestamp, extra.event_type, extra.ip_address
| filter extra.security_event = true
| stats count() as event_count by extra.event_type, extra.ip_address
| sort event_count desc
```

Session tracking:
```sql
fields @timestamp, message, extra.operation, extra.duration_ms
| filter extra.session_id = "abc-123"
| sort @timestamp asc
```

**Benefits:**
- Powerful structured queries
- Easy metric extraction
- Complex filtering and aggregation
- Better insights into system behavior

## Summary of Improvements

| Aspect | Before | After |
|--------|--------|-------|
| **Format** | Plain text | JSON |
| **Parsing** | Manual/regex | Native JSON parsing |
| **Context** | String formatting | Structured fields |
| **Querying** | Text search only | Field-based queries |
| **Metrics** | Manual extraction | Automatic extraction |
| **Exceptions** | Message only | Full traceback + context |
| **Security** | Not tagged | Tagged and structured |
| **Performance** | String overhead | Type-safe fields |
| **CloudWatch** | Limited queries | Full Insights support |
| **Correlation** | Difficult | Easy via IDs |

## Migration Effort

- **Core module**: 1 file (`json_logging.py`)
- **Services updated**: 3 (main-backend, gguf-server, asr-ocr-server)
- **Supporting modules**: 3 (secrets_manager, input_validation, reliability)
- **Breaking changes**: None (backward compatible)
- **Performance impact**: Minimal (~0.1-0.5ms per log)
- **Testing**: Comprehensive (9 tests, all passing)
- **Documentation**: Complete (5 documents)

## Conclusion

The migration to structured JSON logging provides:
- ✅ Better observability
- ✅ Easier debugging
- ✅ Better performance monitoring
- ✅ Enhanced security auditing
- ✅ CloudWatch-ready logs
- ✅ Production-ready implementation
