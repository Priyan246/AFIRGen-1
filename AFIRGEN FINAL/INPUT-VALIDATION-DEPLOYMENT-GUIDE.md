# Input Validation Deployment Guide

## Pre-Deployment Checklist

### 1. Code Review
- [ ] Review all changes in `agentv5.py`
- [ ] Review `input_validation.py` module
- [ ] Verify no hardcoded secrets
- [ ] Check all imports are correct

### 2. Testing
- [ ] Run full test suite: `python test_input_validation.py`
- [ ] Verify all tests pass
- [ ] Test with real data
- [ ] Test edge cases manually

### 3. Configuration
- [ ] Set appropriate validation limits for production
- [ ] Configure API keys
- [ ] Set up monitoring for validation failures

## Deployment Steps

### Step 1: Backup Current System

```bash
# Backup current code
cp -r "AFIRGEN FINAL/main backend" "AFIRGEN FINAL/main backend.backup"

# Backup database
python backup_database.py
```

### Step 2: Deploy New Code

```bash
# Copy new files to production
cp "AFIRGEN FINAL/main backend/input_validation.py" /path/to/production/
cp "AFIRGEN FINAL/main backend/agentv5.py" /path/to/production/

# Install dependencies (if any new ones)
pip install -r requirements.txt
```

### Step 3: Update Environment Variables

```bash
# Add any new environment variables
export API_KEY="your-secure-api-key"
export RATE_LIMIT_REQUESTS=100
export RATE_LIMIT_WINDOW=60
```

### Step 4: Restart Services

```bash
# Stop current services
pkill -f agentv5.py

# Start with new code
python agentv5.py &

# Verify service is running
curl http://localhost:8000/health
```

### Step 5: Smoke Testing

```bash
# Test basic functionality
curl -X POST http://localhost:8000/process \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test complaint for validation"}'

# Test validation works
curl -X POST http://localhost:8000/process \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"text": "short"}'  # Should return 400
```

### Step 6: Monitor Logs

```bash
# Watch for validation errors
tail -f fir_pipeline.log | grep -i "validation\|error"

# Check for false positives
tail -f fir_pipeline.log | grep -i "dangerous pattern"
```

## Post-Deployment Verification

### 1. Functional Testing

Test each endpoint:

```bash
# Process endpoint
curl -X POST http://localhost:8000/process \
  -H "X-API-Key: $API_KEY" \
  -d '{"text": "Valid complaint text..."}'

# Validate endpoint
curl -X POST http://localhost:8000/validate \
  -H "X-API-Key: $API_KEY" \
  -d '{"session_id": "valid-uuid", "approved": true}'

# List FIRs
curl -X GET "http://localhost:8000/list_firs?limit=10" \
  -H "X-API-Key: $API_KEY"
```

### 2. Security Testing

```bash
# Test XSS prevention
curl -X POST http://localhost:8000/process \
  -H "X-API-Key: $API_KEY" \
  -d '{"text": "<script>alert(1)</script>"}' \
  # Should return 400

# Test SQL injection prevention
curl -X GET "http://localhost:8000/fir/FIR-12345678'; DROP TABLE fir_records;--" \
  -H "X-API-Key: $API_KEY" \
  # Should return 400

# Test authentication
curl -X GET http://localhost:8000/list_firs
# Should return 401
```

### 3. Performance Testing

```bash
# Run load test
ab -n 1000 -c 10 \
  -H "X-API-Key: $API_KEY" \
  http://localhost:8000/health

# Check response times
curl -w "@curl-format.txt" -o /dev/null -s \
  -H "X-API-Key: $API_KEY" \
  http://localhost:8000/list_firs
```

## Monitoring

### 1. Set Up Alerts

Monitor for:
- High rate of validation failures (possible attack)
- Unusual patterns in rejected inputs
- Performance degradation
- Error rate increase

### 2. Log Analysis

```bash
# Count validation failures by type
grep "validation" fir_pipeline.log | \
  awk '{print $NF}' | sort | uniq -c

# Find most common rejected patterns
grep "dangerous pattern" fir_pipeline.log | \
  awk -F': ' '{print $2}' | sort | uniq -c | sort -rn
```

### 3. Metrics to Track

- Validation failure rate
- Most common validation errors
- Response time impact
- False positive rate

## Rollback Procedure

If issues are detected:

### Step 1: Stop Current Service

```bash
pkill -f agentv5.py
```

### Step 2: Restore Backup

```bash
cp -r "AFIRGEN FINAL/main backend.backup/"* "AFIRGEN FINAL/main backend/"
```

### Step 3: Restart Service

```bash
python agentv5.py &
```

### Step 4: Verify Rollback

```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Issue: High False Positive Rate

**Symptoms**: Valid inputs being rejected

**Solution**:
1. Review validation logs
2. Identify common patterns being rejected
3. Adjust validation rules in `ValidationConstants`
4. Redeploy with updated rules

### Issue: Performance Degradation

**Symptoms**: Slower response times

**Solution**:
1. Check if validation is the bottleneck
2. Review complex regex patterns
3. Consider caching validation results
4. Optimize sanitization functions

### Issue: Validation Bypass

**Symptoms**: Invalid inputs getting through

**Solution**:
1. Review validation logic
2. Add missing validators
3. Tighten validation rules
4. Add more test cases

## Configuration Tuning

### Adjusting Limits

Edit `input_validation.py`:

```python
class ValidationConstants:
    # Increase for longer complaints
    MAX_TEXT_LENGTH = 100_000  # Was 50,000
    
    # Decrease for stricter validation
    MIN_TEXT_LENGTH = 20  # Was 10
    
    # Adjust file size limit
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB instead of 25MB
```

### Adding Custom Patterns

```python
# Add to DANGEROUS_PATTERNS
DANGEROUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    # Add custom pattern
    r'your-custom-pattern',
]
```

## Best Practices

1. **Test Thoroughly**: Always test in staging before production
2. **Monitor Closely**: Watch logs for first 24 hours after deployment
3. **Document Changes**: Keep track of validation rule changes
4. **Gradual Rollout**: Consider deploying to subset of users first
5. **Have Rollback Plan**: Always be ready to rollback if needed

## Support Contacts

- **Security Issues**: security@example.com
- **Technical Issues**: tech-support@example.com
- **Emergency Rollback**: on-call-engineer@example.com

## Appendix: Validation Rules Reference

### Text Input
- Min: 10 characters
- Max: 50,000 characters
- Sanitization: HTML escaping, dangerous pattern removal

### File Upload
- Max size: 25 MB
- Allowed types: JPEG, PNG, WAV, MP3
- Validation: Extension, MIME type, size

### Session ID
- Format: UUID v4
- Validation: Regex pattern match

### FIR Number
- Format: FIR-[hex8]-[timestamp14]
- Validation: Regex pattern match

### Pagination
- Limit: 1-100 (default 20)
- Offset: >= 0 (default 0)

## Conclusion

Follow this guide carefully to ensure a smooth deployment of input validation. Monitor closely after deployment and be prepared to rollback if necessary.
