# Performance Optimization Validation Checklist

Use this checklist to verify that all performance optimizations are working correctly.

## Pre-Validation Setup

- [ ] All services are running (`docker-compose up -d`)
- [ ] Models are loaded successfully (check logs)
- [ ] Database is accessible
- [ ] ChromaDB collections are loaded
- [ ] Python dependencies installed (`pip install httpx`)

## Code Changes Verification

### Main Backend (`agentv5.py`)

- [ ] **Parallel Violation Checking**
  - Check that `find_violations_with_validation` uses `asyncio.gather()`
  - Verify `top_hits = hits[:10]` limits to 10 hits
  - Confirm timeout is 8s per check

- [ ] **KB Query Caching**
  - Verify `KB` class has `_query_cache` attribute
  - Check `_cache_ttl = 300` (5 minutes)
  - Confirm cache key uses MD5 hash

- [ ] **Reduced Token Limits**
  - `two_line_summary`: max_tokens=100
  - `check_violation`: max_tokens=3
  - `fir_narrative`: max_tokens=150

- [ ] **Health Check Caching**
  - Verify `_health_check_cache` in `ModelPool`
  - Check `_health_check_ttl = 30` seconds

- [ ] **Metrics Endpoint**
  - Confirm `/metrics` endpoint exists
  - Verify it returns session and FIR statistics

### GGUF Model Server (`llm_server.py`)

- [ ] **Optimized Model Loading**
  - `n_batch=512` in CONFIG
  - `use_mlock=True` in CONFIG
  - `use_mmap=True` in CONFIG
  - These parameters passed to `Llama()` constructor

## Functional Testing

### 1. Health Checks

```bash
# Main backend
curl http://localhost:8000/health | jq '.'

# Expected: status "healthy" or "degraded"
# Check: kb_cache_size field exists
```

```bash
# Model server
curl http://localhost:8001/health | jq '.'

# Expected: all models loaded
```

```bash
# ASR/OCR server
curl http://localhost:8002/health | jq '.'

# Expected: at least whisper loaded
```

- [ ] All health checks return 200 OK
- [ ] Main backend shows `kb_cache_size` field
- [ ] Model servers show models loaded

### 2. Metrics Endpoint

```bash
curl http://localhost:8000/metrics | jq '.'
```

- [ ] Returns session statistics
- [ ] Returns FIR statistics
- [ ] Returns cache_size
- [ ] Returns rate_limiter info

### 3. Performance Test

```bash
python test_performance.py
```

- [ ] Test completes without errors
- [ ] Total time < 30 seconds
- [ ] All steps complete successfully
- [ ] FIR document generated
- [ ] Results saved to `performance_test_results.json`

### 4. Cache Verification

Run the performance test twice in succession:

```bash
# First run (cold cache)
python test_performance.py
# Note the violations_validation time

# Second run (warm cache)
python test_performance.py
# Note the violations_validation time - should be faster
```

- [ ] Second run is faster than first run
- [ ] Cache hit visible in metrics: `curl http://localhost:8000/metrics | jq '.sessions.cache_size'`

### 5. Parallel Processing Verification

Check logs during test execution:

```bash
docker-compose logs -f main_backend | grep "Violation check"
```

- [ ] Multiple "Violation check" messages appear simultaneously
- [ ] No sequential pattern in timestamps

## Performance Benchmarks

After running `test_performance.py`, verify these benchmarks:

### Individual Steps

- [ ] Process step: < 1s
- [ ] Transcript validation: < 0.5s
- [ ] Summary generation: < 5s
- [ ] Violations detection: < 8s
- [ ] Narrative generation: < 5s
- [ ] FIR generation: < 2s

### Overall Performance

- [ ] Total time: < 30s
- [ ] Average (multiple runs): 15-20s
- [ ] No timeouts or errors

## Load Testing (Optional)

Run concurrent test:

```bash
# In test_performance.py, answer 'y' when prompted
python test_performance.py
# When asked: Run concurrent load test? (y/n): y
```

- [ ] All 5 requests complete successfully
- [ ] Average time reasonable (< 5s per request)
- [ ] No errors or timeouts

## Monitoring Validation

### Check Logs

```bash
# Main backend logs
docker-compose logs main_backend | grep "cache hit"
docker-compose logs main_backend | grep "Violation check"

# Model server logs
docker-compose logs gguf_model_server | grep "loaded"
```

- [ ] Cache hits visible in logs
- [ ] Models loaded with optimized parameters
- [ ] No error messages

### Check Database

```bash
# Check FIR records
curl http://localhost:8000/list_firs | jq '.'
```

- [ ] FIR records created successfully
- [ ] Status shows "pending" or "finalized"

## Regression Testing

Test that existing functionality still works:

### Manual FIR Generation

1. Open frontend: `http://localhost:8000` (or frontend URL)
2. Submit a text complaint
3. Go through validation steps
4. Verify FIR is generated

- [ ] All validation steps work
- [ ] FIR document is correct
- [ ] No errors in console

### API Endpoints

```bash
# Test /process endpoint
curl -X POST http://localhost:8000/process \
  -F "text=Test complaint about theft"

# Test /validate endpoint (use session_id from above)
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{"session_id":"SESSION_ID","approved":true}'
```

- [ ] /process returns session_id
- [ ] /validate progresses through steps
- [ ] No 500 errors

## Documentation Verification

- [ ] `PERFORMANCE-OPTIMIZATIONS.md` exists and is complete
- [ ] `PERFORMANCE-TEST-GUIDE.md` exists and is complete
- [ ] `PERFORMANCE-SUMMARY.md` exists and is complete
- [ ] `PERFORMANCE-VALIDATION-CHECKLIST.md` (this file) exists

## Sign-Off

### Performance Requirements Met

- [x] FIR generation completes in < 30 seconds
- [ ] System handles 10 concurrent requests (partially tested)
- [ ] Model loading time < 2 minutes (verify on cold start)
- [ ] API response time < 200ms (excluding model inference)

### Code Quality

- [ ] No syntax errors (verified with getDiagnostics)
- [ ] No runtime errors during testing
- [ ] Logs show expected behavior
- [ ] All optimizations active

### Testing

- [ ] Automated test passes
- [ ] Manual testing successful
- [ ] Cache working correctly
- [ ] Parallel processing working

### Documentation

- [ ] All documentation complete
- [ ] Instructions clear and accurate
- [ ] Troubleshooting guide helpful

## Issues Found

Document any issues discovered during validation:

1. Issue: _______________
   - Severity: [ ] Critical [ ] Major [ ] Minor
   - Status: [ ] Open [ ] Resolved
   - Notes: _______________

2. Issue: _______________
   - Severity: [ ] Critical [ ] Major [ ] Minor
   - Status: [ ] Open [ ] Resolved
   - Notes: _______________

## Final Approval

- [ ] All critical checks passed
- [ ] Performance target met (< 30s)
- [ ] No blocking issues
- [ ] Ready for production deployment

**Validated by**: _______________
**Date**: _______________
**Signature**: _______________

## Next Steps

After validation:

1. [ ] Update requirements.md to mark task complete
2. [ ] Deploy to staging environment
3. [ ] Run load tests with realistic traffic
4. [ ] Set up production monitoring
5. [ ] Configure alerts
6. [ ] Document baseline performance metrics
