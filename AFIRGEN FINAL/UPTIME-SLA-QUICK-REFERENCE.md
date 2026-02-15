# 99.9% Uptime SLA - Quick Reference

## What is 99.9% Uptime?

- **Maximum downtime per year:** 8.76 hours
- **Maximum downtime per month:** 43.8 minutes
- **Maximum downtime per week:** 10.1 minutes
- **Maximum downtime per day:** 1.44 minutes

## Key Features Implemented

### 1. Circuit Breakers ⚡
Prevent cascading failures by stopping requests to failing services.

**Check Status:**
```bash
curl http://localhost:8000/reliability | jq '.circuit_breakers'
```

**Reset Circuit Breaker:**
```bash
curl -X POST http://localhost:8000/reliability/circuit-breaker/model_server/reset
curl -X POST http://localhost:8000/reliability/circuit-breaker/asr_ocr_server/reset
```

### 2. Retry Policies 🔄
Automatically retry failed requests with exponential backoff.

- Max retries: 2 (3 total attempts)
- Handles transient network issues
- Prevents thundering herd with jitter

### 3. Graceful Shutdown 👋
Ensures in-flight requests complete before shutdown.

- Timeout: 30 seconds
- Returns 503 for new requests during shutdown
- Clean resource cleanup

### 4. Health Monitoring 🏥
Continuous monitoring of critical dependencies.

**Check Health:**
```bash
curl http://localhost:8000/health | jq '.reliability.health_monitor'
```

### 5. Enhanced Docker Configuration 🐳
- Restart policy: `always`
- Resource limits configured
- Health checks on all services
- Graceful stop period: 30s

## Quick Commands

### Check System Health
```bash
curl http://localhost:8000/health
```

### Check Reliability Status
```bash
curl http://localhost:8000/reliability
```

### View Circuit Breaker States
```bash
curl http://localhost:8000/reliability | jq '.circuit_breakers'
```

### View Health Monitor Uptime
```bash
curl http://localhost:8000/reliability | jq '.health_monitor.checks'
```

### Check Active Requests
```bash
curl http://localhost:8000/reliability | jq '.graceful_shutdown.active_requests'
```

### Run Reliability Tests
```bash
python test_reliability.py
```

## Monitoring Checklist

Daily:
- [ ] Check circuit breaker states (should be CLOSED)
- [ ] Verify health monitor shows > 99% uptime
- [ ] Review error logs for patterns

Weekly:
- [ ] Calculate actual uptime percentage
- [ ] Review circuit breaker trip history
- [ ] Test graceful shutdown
- [ ] Run reliability test suite

Monthly:
- [ ] Verify 99.9% uptime SLA met
- [ ] Review and optimize resource limits
- [ ] Update monitoring thresholds
- [ ] Conduct chaos engineering tests

## Troubleshooting

### Circuit Breaker Stuck Open
```bash
# Check if service is healthy
curl http://localhost:8001/health  # Model server
curl http://localhost:8002/health  # ASR/OCR server

# Reset if healthy
curl -X POST http://localhost:8000/reliability/circuit-breaker/model_server/reset
```

### High Failure Rate
```bash
# Check resource usage
docker stats

# Check logs
docker-compose logs --tail=100 fir_pipeline

# Check circuit breaker states
curl http://localhost:8000/reliability
```

### Graceful Shutdown Issues
```bash
# Check active requests
curl http://localhost:8000/reliability | jq '.graceful_shutdown'

# Review shutdown logs
docker-compose logs fir_pipeline | grep "shutdown"
```

## Alerts to Configure

1. **Uptime < 99.9%** (over 30-day window)
   - Severity: Critical
   - Action: Immediate investigation

2. **Circuit Breaker OPEN > 5 minutes**
   - Severity: High
   - Action: Check service health, consider manual reset

3. **Health Check Failure Rate > 5%**
   - Severity: Medium
   - Action: Investigate dependency issues

4. **Graceful Shutdown Timeout**
   - Severity: Medium
   - Action: Review long-running requests

5. **Request Failure Rate > 1%**
   - Severity: High
   - Action: Check logs and circuit breakers

## Performance Impact

All reliability features have minimal overhead:
- Circuit breakers: < 1ms per request
- Retry policies: Only on failures
- Request tracking: < 0.1ms per request
- Health monitoring: Background task (no impact)

## Testing

### Quick Test
```bash
python test_reliability.py
```

### Load Test (30 seconds)
```bash
python test_reliability.py --url http://localhost:8000
```

### Expected Results
- All tests should pass
- Uptime should be ≥ 99.9%
- Circuit breakers should be CLOSED
- Health checks should be passing

## Deployment

Before deploying:
1. Run reliability tests: `python test_reliability.py`
2. Verify all services healthy: `docker-compose ps`
3. Check resource limits: `docker-compose config`
4. Review logs: `docker-compose logs`
5. Test graceful shutdown: `docker-compose restart fir_pipeline`

After deploying:
1. Monitor health endpoint for 1 hour
2. Verify circuit breakers remain CLOSED
3. Check health monitor uptime percentages
4. Review application logs for errors

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review health status: `curl http://localhost:8000/health`
3. Check reliability metrics: `curl http://localhost:8000/reliability`
4. Run test suite: `python test_reliability.py`
5. Consult full documentation: `UPTIME-SLA-IMPLEMENTATION.md`
