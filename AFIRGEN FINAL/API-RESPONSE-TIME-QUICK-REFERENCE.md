# API Response Time Optimization - Quick Reference

## Target
**<200ms response time** for all non-model-inference endpoints (P95)

## Optimized Endpoints

| Endpoint | Target | Optimization |
|----------|--------|--------------|
| GET /health | <50ms | 30s cache |
| GET /session/{id}/status | <100ms | 60s cache + async |
| GET /fir/{number} | <100ms | 30s cache + indexes |
| GET /fir/{number}/content | <150ms | 30s cache + indexes |
| GET /metrics | <50ms | 10s cache |
| GET /list_firs | <150ms | Async + indexes |

## Key Optimizations

### 1. Caching
```python
# Session cache: 60s TTL
_session_cache = {}

# FIR cache: 30s TTL
_fir_cache = {}

# Health check cache: 30s TTL
_health_check_cache = {}

# Metrics cache: 10s TTL
_metrics_cache = None
```

### 2. Database Indexes
```sql
INDEX idx_fir_number (fir_number)
INDEX idx_session_id (session_id)
INDEX idx_status (status)
INDEX idx_created_at (created_at)
```

### 3. Async Operations
```python
# All DB operations use async
session = await asyncio.to_thread(session_manager.get_session, session_id)
fir = await asyncio.to_thread(db.get_fir, fir_number)
```

### 4. Data Minimization
- Removed `validation_history` from session status
- Removed `content` from FIR status (use /fir/{number}/content)
- Limited list queries to 20 records

## Testing

```bash
# Run API response time test
python test_api_response_time.py
```

## Breaking Changes

### FIR Content Endpoint
**Before**:
```javascript
GET /fir/{number}  // Returns status + content
```

**After**:
```javascript
GET /fir/{number}          // Returns status only (fast)
GET /fir/{number}/content  // Returns status + content (slower)
```

### Session Status Endpoint
**Before**:
```javascript
GET /session/{id}/status  // Returns status + validation_history
```

**After**:
```javascript
GET /session/{id}/status  // Returns status only (no validation_history)
```

## Cache Invalidation

| Cache | Invalidated On |
|-------|----------------|
| Session | Update, status change, validation step |
| FIR | Save, finalization |
| Health | TTL expiration only |
| Metrics | TTL expiration only |

## Performance Monitoring

### Key Metrics
- Response time (P50, P95, P99)
- Cache hit rate
- Database query time
- Error rate

### Expected Performance
- **Cached requests**: 50-100ms
- **Uncached requests**: 100-200ms
- **Cache hit rate**: >80%

## Troubleshooting

### Response Time >200ms
1. Check cache hit rate
2. Verify database indexes exist
3. Check database connection pool
4. Monitor database query time
5. Consider increasing cache TTL

### High Memory Usage
1. Check cache sizes
2. Verify TTL expiration working
3. Monitor KB query cache (max 100 entries)

## Quick Wins

1. **Increase cache TTL** if response times still high
2. **Add more indexes** for slow queries
3. **Use Redis** for distributed caching
4. **Scale database** with read replicas
