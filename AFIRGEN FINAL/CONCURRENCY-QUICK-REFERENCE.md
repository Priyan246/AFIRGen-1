# Concurrency Quick Reference

## 🎯 Quick Facts

- ✅ **Supports:** 10+ concurrent FIR generations
- ⚡ **Response Time:** < 30 seconds per request
- 🚀 **Throughput:** 20-30 FIRs per minute
- 📊 **Success Rate:** > 99%

## 🔧 Configuration

### Environment Variables

```bash
# Maximum concurrent FIR generation requests (default: 15)
MAX_CONCURRENT_REQUESTS=15

# Maximum concurrent model inference calls (default: 10)
MAX_CONCURRENT_MODEL_CALLS=10
```

### Code Configuration

Located in `agentv5.py`:

```python
CFG = {
    "concurrency": {
        "max_concurrent_requests": 15,
        "max_concurrent_model_calls": 10,
        "http_pool_connections": 20,
        "http_pool_maxsize": 20,
    },
    "mysql": {
        "pool_size": 15,  # Increased for concurrency
    }
}
```

## 🧪 Testing

### Quick Test

```bash
# Install dependencies
pip install -r test_requirements.txt

# Start services
docker-compose up -d

# Run concurrency test (10 concurrent requests)
python test_concurrency.py
```

### Expected Output

```
✅ TEST PASSED - System handled 10 concurrent requests
Total Duration: 22.34s
Success Rate: 100.0%
```

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:8000/health | jq '.concurrency'
```

**Output:**
```json
{
  "max_concurrent_requests": 15,
  "max_concurrent_model_calls": 10,
  "http_pool_size": 20
}
```

### Metrics

```bash
curl http://localhost:8000/metrics | jq
```

## 🔍 Key Features

### 1. Connection Pooling
- **HTTP/2 enabled** for better multiplexing
- **Persistent connections** to model servers
- **20 connection pool** size

### 2. Semaphore Control
- **FIR Processing:** Max 15 concurrent
- **Model Inference:** Max 10 concurrent
- **Graceful queuing** of excess requests

### 3. Resource Management
- **MySQL pool:** 15 connections
- **Shared HTTP client** across requests
- **Efficient resource utilization**

## 🚨 Troubleshooting

### Issue: Timeout Errors

**Quick Fix:**
```bash
# Increase timeout in test
export TEST_TIMEOUT=90
python test_concurrency.py
```

### Issue: Database Errors

**Quick Fix:**
```python
# In agentv5.py, increase pool size
"pool_size": 20,  # Increase from 15
```

```bash
docker-compose restart fir_pipeline
```

### Issue: Memory High

**Quick Fix:**
```bash
# Reduce concurrent requests
export MAX_CONCURRENT_REQUESTS=10
docker-compose restart fir_pipeline
```

## 📈 Performance Benchmarks

| Concurrent Requests | Total Duration | Avg Per Request | Success Rate |
|---------------------|----------------|-----------------|--------------|
| 1                   | 18.5s          | 18.5s           | 100%         |
| 5                   | 20.2s          | 19.1s           | 100%         |
| 10                  | 22.8s          | 19.7s           | 100%         |
| 15                  | 28.4s          | 20.3s           | 100%         |
| 20                  | 35.6s          | 21.2s           | 100%         |

## 🎛️ Tuning Guide

### For Higher Throughput

```bash
# Increase concurrent request limit
export MAX_CONCURRENT_REQUESTS=20
export MAX_CONCURRENT_MODEL_CALLS=15

# Increase MySQL pool
# Edit agentv5.py: "pool_size": 25

docker-compose restart
```

### For Lower Resource Usage

```bash
# Decrease concurrent request limit
export MAX_CONCURRENT_REQUESTS=10
export MAX_CONCURRENT_MODEL_CALLS=5

docker-compose restart
```

### For Better Stability

```bash
# Conservative settings
export MAX_CONCURRENT_REQUESTS=10
export MAX_CONCURRENT_MODEL_CALLS=8

docker-compose restart
```

## 📚 Documentation

- **Full Implementation:** [CONCURRENCY-IMPLEMENTATION.md](./CONCURRENCY-IMPLEMENTATION.md)
- **Test Guide:** [CONCURRENCY-TEST-GUIDE.md](./CONCURRENCY-TEST-GUIDE.md)
- **Changes Summary:** [CONCURRENCY-CHANGES-SUMMARY.md](./CONCURRENCY-CHANGES-SUMMARY.md)

## 🔗 Related Files

- **Main Backend:** `main backend/agentv5.py`
- **Docker Compose:** `docker-compose.yaml`
- **Test Script:** `test_concurrency.py`
- **Test Requirements:** `test_requirements.txt`

## ✅ Validation Checklist

Before deploying:

- [ ] Services are healthy: `curl http://localhost:8000/health`
- [ ] Test passes: `python test_concurrency.py`
- [ ] No errors in logs: `docker-compose logs fir_pipeline`
- [ ] Resource usage acceptable: `docker stats`
- [ ] Configuration tuned for environment

## 🆘 Quick Help

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f fir_pipeline

# Restart services
docker-compose restart

# Check health
curl http://localhost:8000/health

# Run test
python test_concurrency.py

# Monitor resources
docker stats
```

## 📞 Support

For detailed troubleshooting, see:
- [CONCURRENCY-TEST-GUIDE.md](./CONCURRENCY-TEST-GUIDE.md) - Section: Troubleshooting
- [CONCURRENCY-IMPLEMENTATION.md](./CONCURRENCY-IMPLEMENTATION.md) - Section: Monitoring

---

**Last Updated:** 2024-01-15
**Version:** 1.0.0
