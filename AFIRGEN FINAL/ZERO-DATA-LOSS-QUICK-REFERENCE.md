# Zero Data Loss - Quick Reference

## Key Features

✅ **Transaction Management** - All database operations are atomic
✅ **Database Flush** - Data flushed to disk before shutdown
✅ **WAL Mode** - SQLite crash recovery enabled
✅ **MySQL Durability** - Configured for zero data loss
✅ **Graceful Shutdown** - 30s timeout for in-flight requests

## Testing

```bash
# Run zero data loss test suite
python3 test_zero_data_loss.py

# Expected: 6/6 tests passed
```

## Verification Commands

### Check MySQL Durability Settings

```bash
docker exec afirgen-mysql mysql -u root -ppassword -e "
  SELECT @@innodb_flush_log_at_trx_commit,
         @@sync_binlog,
         @@innodb_doublewrite;
"
```

Expected output:
```
+----------------------------------+---------------+---------------------+
| @@innodb_flush_log_at_trx_commit | @@sync_binlog | @@innodb_doublewrite|
+----------------------------------+---------------+---------------------+
|                                1 |             1 |                   1 |
+----------------------------------+---------------+---------------------+
```

### Check SQLite WAL Mode

```bash
docker exec afirgen-fir_pipeline sqlite3 /app/sessions.db "
  PRAGMA journal_mode;
  PRAGMA synchronous;
"
```

Expected output:
```
wal
2
```

### Check Transaction Mode

```bash
docker exec afirgen-mysql mysql -u root -ppassword -e "
  SELECT @@autocommit;
"
```

Expected output:
```
+--------------+
| @@autocommit |
+--------------+
|            0 |
+--------------+
```

## Monitoring Shutdown

### Watch Logs During Restart

```bash
# Terminal 1: Watch logs
docker-compose logs -f fir_pipeline

# Terminal 2: Restart service
docker-compose restart fir_pipeline
```

Look for these messages:
```
[INFO] Application shutdown initiated
[INFO] Graceful shutdown complete - all in-flight requests finished
[INFO] Flushing all pending data to disk...
[INFO] ✅ Session data flushed
[INFO] ✅ MySQL data flushed
[INFO] ✅ All data successfully persisted to disk
[INFO] 👋 Application shutdown complete - Zero data loss guaranteed
```

## Manual Testing

### Test Data Persistence

```bash
# 1. Create test data
curl -X POST http://localhost:8000/process \
  -F "text=Test complaint for persistence check"

# 2. Get session ID from response
# Response: {"success": true, "session_id": "abc123..."}

# 3. Restart service
docker-compose restart fir_pipeline

# 4. Wait for service
sleep 30

# 5. Verify data persists
curl http://localhost:8000/list_firs
```

### Test During Load

```bash
# 1. Start load (background)
for i in {1..5}; do
  curl -X POST http://localhost:8000/process \
    -F "text=Load test complaint $i" &
done

# 2. Restart immediately
docker-compose restart fir_pipeline

# 3. Verify all data persists
sleep 30
curl http://localhost:8000/list_firs
```

## Configuration

### MySQL Durability (docker-compose.yaml)

```yaml
mysql:
  command: >
    --innodb-flush-log-at-trx-commit=1
    --sync-binlog=1
    --innodb-doublewrite=1
```

### Graceful Shutdown Timeout

```yaml
fir_pipeline:
  stop_grace_period: 30s
```

### Transaction Mode (agentv5.py)

```python
"mysql": {
    "autocommit": False,  # Transactions enabled
    ...
}
```

## Troubleshooting

### Data Lost After Restart

```bash
# Check MySQL settings
docker exec afirgen-mysql mysql -u root -ppassword -e "
  SHOW VARIABLES LIKE 'innodb_flush%';
  SHOW VARIABLES LIKE 'sync_binlog';
"

# Check SQLite mode
docker exec afirgen-fir_pipeline sqlite3 /app/sessions.db "PRAGMA journal_mode"

# Check logs for errors
docker-compose logs fir_pipeline | grep -i "flush\|error"
```

### Slow Shutdown

```bash
# Check active requests
curl http://localhost:8000/reliability

# Check shutdown timeout
docker-compose config | grep stop_grace_period
```

### Flush Failures

```bash
# Check disk space
docker exec afirgen-fir_pipeline df -h

# Check database connectivity
docker exec afirgen-fir_pipeline python3 -c "
import mysql.connector
conn = mysql.connector.connect(
    host='mysql', user='root', password='password', database='fir_db'
)
print('MySQL OK')
"

# Check SQLite
docker exec afirgen-fir_pipeline sqlite3 /app/sessions.db "SELECT COUNT(*) FROM sessions"
```

## Performance Impact

| Component | Impact | Benefit |
|-----------|--------|---------|
| MySQL Durability | -20-40% write speed | Zero data loss |
| SQLite WAL | +2-3x write speed | Better concurrency |
| Transaction Mode | -5-10% throughput | Atomicity |
| Flush on Shutdown | +1-2s shutdown time | Data persistence |

## Health Checks

### Service Health

```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "database": "connected",
  "session_persistence": "sqlite"
}
```

### Reliability Status

```bash
curl http://localhost:8000/reliability
```

Expected:
```json
{
  "graceful_shutdown": {
    "is_shutting_down": false,
    "active_requests": 0,
    "shutdown_timeout": 30.0
  }
}
```

## Key Files

- `main backend/agentv5.py` - Transaction management, flush methods
- `docker-compose.yaml` - MySQL durability settings
- `test_zero_data_loss.py` - Test suite
- `ZERO-DATA-LOSS-IMPLEMENTATION.md` - Full documentation

## Acceptance Criteria

✅ **Zero data loss on service restart**
- Transactions ensure atomicity
- Flush operations ensure durability
- WAL mode provides crash recovery
- MySQL configured for maximum durability
- Graceful shutdown waits for in-flight requests
- Comprehensive test suite validates all mechanisms

## Quick Commands

```bash
# Run tests
python3 test_zero_data_loss.py

# Check MySQL settings
docker exec afirgen-mysql mysql -u root -ppassword -e "SHOW VARIABLES LIKE 'innodb%'"

# Check SQLite mode
docker exec afirgen-fir_pipeline sqlite3 /app/sessions.db "PRAGMA journal_mode; PRAGMA synchronous;"

# Monitor shutdown
docker-compose logs -f fir_pipeline

# Restart service
docker-compose restart fir_pipeline

# Verify data
curl http://localhost:8000/list_firs
```
