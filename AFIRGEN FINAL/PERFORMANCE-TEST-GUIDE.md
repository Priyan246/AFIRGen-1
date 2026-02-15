# Performance Test Guide

## Quick Start

### Prerequisites

1. All services running (main backend, model server, ASR/OCR server)
2. Models loaded successfully
3. Database initialized
4. Python 3.8+ with httpx installed

### Install Dependencies

```bash
pip install httpx
```

### Run Performance Test

```bash
cd "AFIRGEN FINAL"
python test_performance.py
```

## What the Test Does

The performance test validates that FIR generation completes in under 30 seconds by:

1. **Health Check**: Verifies all services are running
2. **Process Text**: Submits a test complaint
3. **Validation Steps**: Automatically approves each validation step:
   - Transcript review
   - Summary review
   - Violations review
   - FIR narrative review
   - Final review
4. **Timing**: Measures total time and per-step duration
5. **Results**: Reports PASS/FAIL based on 30-second threshold

## Expected Output

```
============================================================
FIR Generation Performance Test
============================================================

1. Checking service health...
Health Status: healthy
  Model Server: healthy
  ASR/OCR Server: healthy

2. Starting FIR processing...
✅ Process step completed in 0.45s

3. Validating transcript...
✅ transcript_validation completed in 0.23s

4. Validating summary...
✅ summary_validation completed in 3.82s

5. Validating violations...
✅ violations_validation completed in 4.56s

6. Validating FIR narrative...
✅ narrative_validation completed in 3.21s

7. Final review...
✅ final_review completed in 1.34s

============================================================
Performance Test Results
============================================================
Total Time: 18.45s
Target: 30.00s
Status: ✅ PASS

Step Breakdown:
  process                  :   0.45s
  transcript_validation    :   0.23s
  summary_validation       :   3.82s
  violations_validation    :   4.56s
  narrative_validation     :   3.21s
  final_review             :   1.34s
============================================================

✅ FIR Generated: FIR-a1b2c3d4-20240212143022

✅ Performance test PASSED - FIR generation under 30 seconds

============================================================
Run concurrent load test? (y/n): 
```

## Interpreting Results

### PASS Criteria

- Total time < 30 seconds
- All steps complete successfully
- FIR document generated

### FAIL Scenarios

1. **Total time > 30s**: Performance optimization needed
2. **Service unhealthy**: Check logs and restart services
3. **Step timeout**: Check specific service (model server, ASR/OCR)
4. **Error in processing**: Check application logs

## Troubleshooting

### Test Fails with "Services not healthy"

```bash
# Check service status
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health

# Check logs
docker-compose logs main_backend
docker-compose logs gguf_model_server
docker-compose logs asr_ocr_model_server
```

### Test Fails with Timeout

1. Check CPU/memory usage:
   ```bash
   docker stats
   ```

2. Check if models are loaded:
   ```bash
   curl http://localhost:8001/health | jq '.models_loaded'
   curl http://localhost:8002/health | jq '.models'
   ```

3. Check database connectivity:
   ```bash
   docker-compose exec mysql mysql -u root -p -e "SELECT 1"
   ```

### Test Takes > 30 seconds

Check which step is slow:

1. **summary_validation > 5s**: Model server slow
   - Check model server logs
   - Verify model optimization settings
   - Consider using smaller/faster model

2. **violations_validation > 8s**: Too many violation checks
   - Check KB cache hit rate: `curl http://localhost:8000/metrics`
   - Verify parallel checking is working
   - Consider reducing top_hits limit

3. **narrative_validation > 5s**: Model server slow
   - Same as summary_validation

## Concurrent Load Test

After the main test passes, you can optionally run a concurrent load test:

```
Run concurrent load test? (y/n): y

============================================================
Concurrent Load Test (5 requests)
============================================================

Results:
  Total Time: 12.34s
  Successful: 5/5
  Avg Time: 2.47s
  Min Time: 2.12s
  Max Time: 2.89s
```

This tests the system's ability to handle multiple simultaneous requests.

## Performance Metrics

### Baseline Performance (After Optimizations)

- **Average**: 15-20 seconds
- **p95**: < 25 seconds
- **p99**: < 30 seconds

### Per-Step Targets

| Step | Target | Typical |
|------|--------|---------|
| Process | < 1s | 0.4-0.6s |
| Transcript validation | < 0.5s | 0.2-0.3s |
| Summary generation | < 5s | 3-4s |
| Violations detection | < 8s | 4-6s |
| Narrative generation | < 5s | 3-4s |
| FIR generation | < 2s | 1-2s |

## Continuous Monitoring

### Production Monitoring

Set up automated performance tests:

```bash
# Run every hour
0 * * * * cd /path/to/AFIRGEN && python test_performance.py >> performance.log 2>&1
```

### Alert on Failures

```bash
# Check exit code
python test_performance.py
if [ $? -ne 0 ]; then
    echo "Performance test failed!" | mail -s "ALERT: FIR Performance" admin@example.com
fi
```

## Results File

Test results are saved to `performance_test_results.json`:

```json
{
  "total_time": 18.45,
  "steps": {
    "process": 0.45,
    "transcript_validation": 0.23,
    "summary_validation": 3.82,
    "violations_validation": 4.56,
    "narrative_validation": 3.21,
    "final_review": 1.34
  },
  "success": true,
  "error": null
}
```

Use this for:
- Historical tracking
- Performance regression detection
- Capacity planning

## Advanced Testing

### Custom Test Data

Edit `test_performance.py` and modify `TEST_TEXT`:

```python
TEST_TEXT = """
Your custom complaint text here...
"""
```

### Different Scenarios

Test with:
- Short complaints (< 100 words)
- Long complaints (> 500 words)
- Multiple violations
- No violations
- Different languages (if supported)

### Load Testing

For production load testing, use tools like:
- Apache JMeter
- Locust
- k6
- Artillery

## Support

If performance tests consistently fail:

1. Review `PERFORMANCE-OPTIMIZATIONS.md` for tuning options
2. Check system resources (CPU, RAM, disk I/O)
3. Verify model files are correct and not corrupted
4. Check network latency between services
5. Review application logs for errors

## Next Steps

After confirming performance:

1. ✅ Mark task as complete in requirements.md
2. 📊 Set up production monitoring
3. 🚀 Deploy to staging environment
4. 🔍 Run load tests with realistic traffic
5. 📈 Establish performance baselines
