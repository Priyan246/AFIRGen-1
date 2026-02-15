# Auto-Recovery Quick Reference

## Quick Start

### Check System Status
```bash
# Check overall health
curl http://localhost:8000/health

# Check reliability components
curl http://localhost:8000/reliability
```

### Manual Recovery
```bash
# Trigger recovery for model server
curl -X POST http://localhost:8000/reliability/auto-recovery/model_server/trigger

# Trigger recovery for ASR/OCR server
curl -X POST http://localhost:8000/reliability/auto-recovery/asr_ocr_server/trigger

# Trigger recovery for database
curl -X POST http://localhost:8000/reliability/auto-recovery/database/trigger
```

### Reset Circuit Breakers
```bash
# Reset model server circuit breaker
curl -X POST http://localhost:8000/reliability/circuit-breaker/model_server/reset

# Reset ASR/OCR server circuit breaker
curl -X POST http://localhost:8000/reliability/circuit-breaker/asr_ocr_server/reset
```

## Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| AutoRecovery | Automatic recovery handler | `reliability.py` |
| DependencyHealthCheck | Startup dependency checker | `reliability.py` |
| CircuitBreaker | Failure detection | `reliability.py` |
| HealthMonitor | Continuous monitoring | `reliability.py` |
| GracefulShutdown | Clean shutdown | `reliability.py` |

## Recovery Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Recovery Interval | 60s | Cooldown between recovery cycles |
| Max Attempts | 3 | Max recovery attempts before manual intervention |
| Recovery Backoff | 2.0x | Exponential backoff multiplier |
| Startup Timeout | 300s | Max time to wait for dependencies |
| Health Check Interval | 30s | Time between health checks |

## Circuit Breaker States

| State | Meaning | Action |
|-------|---------|--------|
| CLOSED | Normal operation | Requests pass through |
| OPEN | Too many failures | Requests rejected, auto-recovery triggered |
| HALF_OPEN | Testing recovery | Limited requests allowed |

## Monitored Services

1. **Model Server** (Port 8001)
   - GGUF model inference
   - Circuit breaker protected
   - Auto-recovery enabled

2. **ASR/OCR Server** (Port 8002)
   - Whisper ASR
   - dots_ocr OCR
   - Circuit breaker protected
   - Auto-recovery enabled

3. **MySQL Database** (Port 3306)
   - FIR records storage
   - Connection pool managed
   - Auto-recovery enabled

## Common Issues

### Issue: Circuit breaker stuck open
**Solution**: Reset circuit breaker
```bash
curl -X POST http://localhost:8000/reliability/circuit-breaker/model_server/reset
```

### Issue: Service won't start
**Cause**: Dependencies not healthy
**Solution**: Check dependency status
```bash
docker ps
docker logs gguf_model_server
docker logs asr_ocr_model_server
docker logs mysql
```

### Issue: Recovery attempts exhausted
**Cause**: Service genuinely unavailable
**Solution**: 
1. Check service logs
2. Restart failed service
3. Reset recovery state

### Issue: High failure rate
**Cause**: Resource exhaustion or network issues
**Solution**:
1. Check resource usage: `docker stats`
2. Check network connectivity
3. Review service logs

## Testing

### Run Auto-Recovery Tests
```bash
cd "AFIRGEN FINAL"
python test_auto_recovery.py
```

### Simulate Failures
```bash
# Stop model server
docker stop gguf_model_server

# Watch recovery attempts
docker logs -f fir_pipeline

# Restart model server
docker start gguf_model_server
```

## Monitoring

### Key Metrics

1. **Circuit Breaker State**: Should be "closed" during normal operation
2. **Failure Count**: Should be 0 or low
3. **Recovery Attempts**: Should be 0 during normal operation
4. **Uptime Percentage**: Should be >99.9%
5. **Active Requests**: Should be >0 during load

### Log Messages

**Successful Recovery**:
```
[INFO] Circuit breaker 'model_server' opened, triggering auto-recovery
[INFO] Model server connection recovered
[INFO] Recovery successful for: model_server
```

**Failed Recovery**:
```
[ERROR] Model server recovery failed: Connection refused
[ERROR] Max recovery attempts (3) reached for: model_server
```

**Startup**:
```
[INFO] Checking dependencies health...
[INFO] All dependencies are healthy
[INFO] Auto-recovery handlers registered
```

## API Endpoints

### GET /health
Returns service health status

**Response**:
```json
{
  "status": "healthy",
  "model_server": {...},
  "asr_ocr_server": {...},
  "database": "connected",
  "reliability": {
    "circuit_breakers": {...},
    "graceful_shutdown": {...}
  }
}
```

### GET /reliability
Returns detailed reliability status

**Response**:
```json
{
  "circuit_breakers": {
    "model_server": {
      "state": "closed",
      "failure_count": 0
    }
  },
  "auto_recovery": {
    "handlers": {
      "model_server": {
        "attempts": 0,
        "in_progress": false
      }
    }
  }
}
```

### POST /reliability/auto-recovery/{name}/trigger
Manually trigger recovery

**Parameters**:
- `name`: "model_server", "asr_ocr_server", or "database"

**Response**:
```json
{
  "success": true,
  "message": "Recovery succeeded for 'model_server'",
  "status": {...}
}
```

### POST /reliability/circuit-breaker/{name}/reset
Reset circuit breaker

**Parameters**:
- `name`: "model_server" or "asr_ocr_server"

**Response**:
```json
{
  "success": true,
  "message": "Circuit breaker 'model_server' has been reset",
  "status": {...}
}
```

## Best Practices

1. **Monitor Regularly**: Check `/reliability` endpoint every 5 minutes
2. **Alert on Failures**: Set up alerts when circuit breakers open
3. **Review Logs**: Check logs daily for recovery attempts
4. **Test Recovery**: Simulate failures monthly to verify recovery works
5. **Update Thresholds**: Adjust recovery settings based on observed patterns

## Troubleshooting Commands

```bash
# Check all container status
docker ps -a

# Check main backend logs
docker logs fir_pipeline --tail 100

# Check model server logs
docker logs gguf_model_server --tail 100

# Check ASR/OCR server logs
docker logs asr_ocr_model_server --tail 100

# Check database logs
docker logs mysql --tail 100

# Restart all services
docker-compose restart

# Check resource usage
docker stats --no-stream

# Check network connectivity
docker exec fir_pipeline curl -f http://gguf_model_server:8001/health
docker exec fir_pipeline curl -f http://asr_ocr_model_server:8002/health
```

## Support

For issues or questions:
1. Check logs: `docker logs fir_pipeline`
2. Review health status: `curl http://localhost:8000/health`
3. Check reliability: `curl http://localhost:8000/reliability`
4. Run tests: `python test_auto_recovery.py`
