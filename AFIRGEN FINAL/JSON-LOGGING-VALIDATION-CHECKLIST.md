# JSON Logging Validation Checklist

## Pre-Deployment Validation

### 1. Module Installation
- [ ] `json_logging.py` exists in `main backend/` directory
- [ ] Module can be imported without errors
- [ ] All dependencies are available (no external packages required)

### 2. Service Integration

#### Main Backend
- [ ] `agentv5.py` imports `json_logging` module
- [ ] Logger configured with `setup_json_logging()`
- [ ] Service name set to `main-backend`
- [ ] Log file path: `logs/main_backend.log`
- [ ] No syntax errors in updated code

#### GGUF Model Server
- [ ] `llm_server.py` imports `json_logging` module
- [ ] Logger configured with `setup_json_logging()`
- [ ] Service name set to `gguf-server`
- [ ] Log file path: `logs/gguf_server.log`
- [ ] No syntax errors in updated code

#### ASR/OCR Server
- [ ] `asr_ocr.py` imports `json_logging` module
- [ ] Logger configured with `setup_json_logging()`
- [ ] Service name set to `asr-ocr-server`
- [ ] Log file path: `logs/asr_ocr_server.log`
- [ ] No syntax errors in updated code

### 3. Test Suite
- [ ] `test_json_logging.py` exists
- [ ] All 6 tests pass successfully
- [ ] No test failures or errors
- [ ] JSON format validation passes
- [ ] Exception logging test passes
- [ ] Extra fields test passes

### 4. Documentation
- [ ] `JSON-LOGGING-IMPLEMENTATION.md` created
- [ ] `JSON-LOGGING-QUICK-REFERENCE.md` created
- [ ] `JSON-LOGGING-SUMMARY.md` created
- [ ] `JSON-LOGGING-VALIDATION-CHECKLIST.md` created (this file)

## Runtime Validation

### 5. Log Output Format

Start each service and verify log output:

#### Main Backend
```bash
cd "AFIRGEN FINAL/main backend"
python agentv5.py
```

Verify:
- [ ] Logs are output to console
- [ ] Each log line is valid JSON
- [ ] `service` field = `main-backend`
- [ ] `timestamp` field is ISO 8601 format
- [ ] `level` field is present
- [ ] `message` field is present
- [ ] `source` object is present
- [ ] `process` object is present

#### GGUF Server
```bash
cd "AFIRGEN FINAL/gguf model server"
python llm_server.py
```

Verify:
- [ ] Logs are output to console
- [ ] Each log line is valid JSON
- [ ] `service` field = `gguf-server`
- [ ] All required fields present

#### ASR/OCR Server
```bash
cd "AFIRGEN FINAL/asr ocr model server"
python asr_ocr.py
```

Verify:
- [ ] Logs are output to console
- [ ] Each log line is valid JSON
- [ ] `service` field = `asr-ocr-server`
- [ ] All required fields present

### 6. Log Files

After running services:

- [ ] `logs/` directory created
- [ ] `logs/main_backend.log` exists and contains JSON logs
- [ ] `logs/gguf_server.log` exists and contains JSON logs
- [ ] `logs/asr_ocr_server.log` exists and contains JSON logs
- [ ] Log files are readable
- [ ] Each line in log files is valid JSON

### 7. Context Fields

Test logging with context:

```python
from json_logging import log_with_context

log_with_context(
    log, "info", "Test message",
    test_field="test_value",
    numeric_field=123
)
```

Verify:
- [ ] `extra` object present in log
- [ ] `extra.test_field` = `"test_value"`
- [ ] `extra.numeric_field` = `123`
- [ ] Extra fields are properly typed

### 8. Exception Logging

Trigger an error and verify:

```python
try:
    raise ValueError("Test error")
except Exception as e:
    log.error("Error occurred", exc_info=e)
```

Verify:
- [ ] `exception` object present in log
- [ ] `exception.type` = `"ValueError"`
- [ ] `exception.message` contains error message
- [ ] `exception.traceback` contains full traceback

### 9. Convenience Functions

Test each convenience function:

```python
from json_logging import (
    log_request,
    log_response,
    log_performance,
    log_security_event,
    log_error
)

log_request(log, "GET", "/test", "127.0.0.1")
log_response(log, "GET", "/test", 200, 100.5)
log_performance(log, "test_op", 50.0, success=True)
log_security_event(log, "test_event", "info", "Test", ip="127.0.0.1")
```

Verify:
- [ ] `log_request()` produces valid JSON with request fields
- [ ] `log_response()` produces valid JSON with response fields
- [ ] `log_performance()` produces valid JSON with performance fields
- [ ] `log_security_event()` produces valid JSON with security fields
- [ ] All convenience functions work without errors

### 10. Environment Variables

Test environment variable configuration:

```bash
export LOG_LEVEL=DEBUG
export ENVIRONMENT=staging
python agentv5.py
```

Verify:
- [ ] Log level changes to DEBUG
- [ ] More verbose logs appear
- [ ] `environment` field = `"staging"`

## Docker Validation

### 11. Docker Build

Build Docker images:

```bash
docker-compose build
```

Verify:
- [ ] All services build successfully
- [ ] No errors related to json_logging module
- [ ] `logs/` directory created in containers

### 12. Docker Run

Start services:

```bash
docker-compose up
```

Verify:
- [ ] All services start successfully
- [ ] JSON logs appear in docker-compose output
- [ ] Each service outputs valid JSON
- [ ] Service names are correct in logs

### 13. Docker Logs

Check individual service logs:

```bash
docker-compose logs main-backend
docker-compose logs gguf-server
docker-compose logs asr-ocr-server
```

Verify:
- [ ] Logs are in JSON format
- [ ] All required fields present
- [ ] Timestamps are correct
- [ ] No plain-text log lines

## CloudWatch Validation (AWS Deployment)

### 14. Log Groups

After AWS deployment:

- [ ] Log group `/aws/ecs/afirgen/main-backend` exists
- [ ] Log group `/aws/ecs/afirgen/gguf-server` exists
- [ ] Log group `/aws/ecs/afirgen/asr-ocr-server` exists
- [ ] Log streams are being created

### 15. CloudWatch Logs Insights

Test queries:

```sql
fields @timestamp, message, level
| sort @timestamp desc
| limit 20
```

Verify:
- [ ] Query returns results
- [ ] JSON fields are parsed correctly
- [ ] Can query by `level` field
- [ ] Can query by `service` field
- [ ] Can query by `extra.*` fields

### 16. Metric Filters

Create test metric filter:

- Filter pattern: `{ $.level = "ERROR" }`
- Metric name: `ErrorCount`

Verify:
- [ ] Metric filter created successfully
- [ ] Errors are counted correctly
- [ ] Metric appears in CloudWatch Metrics

## Performance Validation

### 17. Performance Impact

Run performance tests:

```bash
python test_performance.py
```

Verify:
- [ ] No significant performance degradation
- [ ] Response times within acceptable range
- [ ] Memory usage stable
- [ ] CPU usage normal

### 18. High Volume Logging

Generate high volume of logs:

```python
for i in range(1000):
    log.info(f"Test message {i}", extra={"iteration": i})
```

Verify:
- [ ] All logs written successfully
- [ ] No log loss
- [ ] No memory leaks
- [ ] File handles closed properly

## Security Validation

### 19. Sensitive Data

Verify no sensitive data in logs:

- [ ] No passwords logged
- [ ] No API keys logged
- [ ] No PII logged (unless required)
- [ ] Sensitive fields are masked/redacted

### 20. Log Access

Verify log file permissions:

```bash
ls -la logs/
```

- [ ] Log files have appropriate permissions
- [ ] Only authorized users can read logs
- [ ] Log directory is not world-readable

## Final Checklist

### 21. Acceptance Criteria

From requirements document:

- [x] Structured JSON logging implemented
- [x] All services output JSON format
- [x] CloudWatch-compatible format
- [x] Required fields present
- [x] Exception tracking included
- [x] Context fields supported
- [x] Performance acceptable
- [x] Documentation complete
- [x] Tests passing

### 22. Sign-Off

- [ ] Development team reviewed
- [ ] QA team validated
- [ ] DevOps team approved
- [ ] Security team reviewed
- [ ] Ready for production deployment

## Troubleshooting

### Common Issues

**Issue**: Logs not in JSON format
- **Solution**: Verify `setup_json_logging()` is called before any logging

**Issue**: Missing fields in logs
- **Solution**: Check JSONFormatter configuration, ensure all required fields are included

**Issue**: Log files not created
- **Solution**: Verify `logs/` directory exists and has write permissions

**Issue**: Import errors
- **Solution**: Verify `json_logging.py` is in correct location and Python path is set

**Issue**: Performance degradation
- **Solution**: Reduce log level, use async logging, or implement log sampling

## Notes

- All validation steps should be completed before production deployment
- Document any deviations or issues found during validation
- Retest after any code changes
- Keep this checklist updated as requirements change
