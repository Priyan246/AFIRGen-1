# Zero Data Loss - Validation Checklist

## Pre-Deployment Validation

### 1. Code Changes Verification

- [ ] **Transaction Management Enabled**
  - File: `main backend/agentv5.py`
  - Check: `"autocommit": False` in MySQL config
  - Check: `_cursor()` method has `autocommit` parameter
  - Check: Explicit `commit()` and `rollback()` in context manager

- [ ] **Flush Methods Implemented**
  - File: `main backend/agentv5.py`
  - Check: `DB.flush_all()` method exists
  - Check: `PersistentSessionManager.flush_all()` method exists
  - Check: Both methods called in shutdown sequence

- [ ] **SQLite WAL Mode Enabled**
  - File: `main backend/agentv5.py`
  - Check: `PRAGMA journal_mode=WAL` in `_init_db()`
  - Check: `PRAGMA synchronous=FULL` in `_init_db()`

- [ ] **MySQL Durability Settings**
  - File: `docker-compose.yaml`
  - Check: `--innodb-flush-log-at-trx-commit=1` in mysql command
  - Check: `--sync-binlog=1` in mysql command
  - Check: `--innodb-doublewrite=1` in mysql command

- [ ] **Graceful Shutdown Enhanced**
  - File: `main backend/agentv5.py`
  - Check: Flush operations in shutdown sequence
  - Check: Proper error handling for flush failures
  - Check: Logging for flush operations

### 2. Docker Configuration

- [ ] **MySQL Service**
  - Durability command flags present
  - `stop_grace_period: 30s` configured
  - Volume mount for data persistence
  - Health check configured

- [ ] **Main Backend Service**
  - `stop_grace_period: 30s` configured
  - Session volume mount present
  - Depends on MySQL health check
  - Restart policy: `always`

- [ ] **Volume Configuration**
  - `mysql_data` volume defined
  - `sessions_data` volume defined
  - `chroma_data` volume defined
  - All volumes persistent (not tmpfs)

### 3. Documentation

- [ ] **Implementation Guide**
  - File: `ZERO-DATA-LOSS-IMPLEMENTATION.md` exists
  - Covers all components
  - Includes testing instructions
  - Explains data loss scenarios prevented

- [ ] **Quick Reference**
  - File: `ZERO-DATA-LOSS-QUICK-REFERENCE.md` exists
  - Verification commands included
  - Troubleshooting guide present
  - Performance impact documented

- [ ] **Test Suite**
  - File: `test_zero_data_loss.py` exists
  - All 6 tests implemented
  - Clear pass/fail criteria
  - Comprehensive coverage

## Deployment Validation

### 1. Service Startup

```bash
# Start services
docker-compose up -d

# Check all services running
docker-compose ps

# Expected: All services "Up" and "healthy"
```

- [ ] All services started successfully
- [ ] Health checks passing
- [ ] No error logs during startup

### 2. MySQL Configuration Check

```bash
# Check durability settings
docker exec afirgen-mysql mysql -u root -ppassword -e "
  SELECT @@innodb_flush_log_at_trx_commit AS flush_log,
         @@sync_binlog AS sync_binlog,
         @@innodb_doublewrite AS doublewrite;
"
```

Expected output:
```
+-----------+-------------+-------------+
| flush_log | sync_binlog | doublewrite |
+-----------+-------------+-------------+
|         1 |           1 |           1 |
+-----------+-------------+-------------+
```

- [ ] `innodb_flush_log_at_trx_commit = 1`
- [ ] `sync_binlog = 1`
- [ ] `innodb_doublewrite = 1`

### 3. SQLite Configuration Check

```bash
# Check WAL mode
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

- [ ] `journal_mode = wal`
- [ ] `synchronous = 2` (FULL)

### 4. Transaction Mode Check

```bash
# Check autocommit disabled
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

- [ ] `autocommit = 0` (disabled)

### 5. Health Check Validation

```bash
# Check service health
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "session_persistence": "sqlite"
}
```

- [ ] Status is "healthy"
- [ ] Database is "connected"
- [ ] Session persistence is "sqlite"

### 6. Reliability Status Check

```bash
# Check reliability components
curl http://localhost:8000/reliability
```

Expected response includes:
```json
{
  "graceful_shutdown": {
    "is_shutting_down": false,
    "active_requests": 0,
    "shutdown_timeout": 30.0
  }
}
```

- [ ] Graceful shutdown configured
- [ ] Shutdown timeout = 30s
- [ ] No active shutdown in progress

## Functional Testing

### Test 1: Data Persistence on Normal Restart

```bash
# 1. Create test data
curl -X POST http://localhost:8000/process \
  -F "text=Test complaint for persistence validation"

# 2. Note the session_id from response

# 3. Restart service
docker-compose restart fir_pipeline

# 4. Wait for service
sleep 30

# 5. Verify data persists
curl http://localhost:8000/list_firs
```

- [ ] Test data created successfully
- [ ] Service restarted without errors
- [ ] Data persists after restart
- [ ] Session data intact

### Test 2: Graceful Shutdown with In-Flight Requests

```bash
# 1. Start multiple requests (background)
for i in {1..5}; do
  curl -X POST http://localhost:8000/process \
    -F "text=Load test complaint $i" &
done

# 2. Immediately restart
docker-compose restart fir_pipeline

# 3. Wait for service
sleep 30

# 4. Verify all data persists
curl http://localhost:8000/list_firs
```

- [ ] Multiple requests submitted
- [ ] Service restarted during load
- [ ] All data persists
- [ ] No partial writes

### Test 3: Shutdown Log Verification

```bash
# Monitor logs during restart
docker-compose logs fir_pipeline | tail -50
```

Look for these messages:
```
[INFO] Application shutdown initiated
[INFO] Graceful shutdown complete - all in-flight requests finished
[INFO] Flushing all pending data to disk...
[INFO] Session database flushed to disk
[INFO] ✅ Session data flushed
[INFO] Database tables flushed to disk
[INFO] ✅ MySQL data flushed
[INFO] ✅ All data successfully persisted to disk
```

- [ ] Shutdown initiated message present
- [ ] Graceful shutdown completed
- [ ] Session flush successful
- [ ] MySQL flush successful
- [ ] Zero data loss message present

### Test 4: Crash Recovery (Forced Stop)

```bash
# 1. Create test data
curl -X POST http://localhost:8000/process \
  -F "text=Test complaint before crash"

# 2. Force stop (simulates crash)
docker-compose kill fir_pipeline

# 3. Start service
docker-compose start fir_pipeline

# 4. Wait for service
sleep 30

# 5. Verify data persists
curl http://localhost:8000/list_firs
```

- [ ] Test data created
- [ ] Service force-stopped
- [ ] Service restarted successfully
- [ ] Data persists despite crash
- [ ] No database corruption

### Test 5: Automated Test Suite

```bash
# Install dependencies
pip install requests mysql-connector-python

# Run test suite
python3 test_zero_data_loss.py
```

Expected output:
```
Results: 6/6 tests passed
✓ All tests passed! Zero data loss is guaranteed.
```

- [ ] All 6 tests passed
- [ ] Transaction atomicity verified
- [ ] MySQL durability verified
- [ ] SQLite WAL verified
- [ ] Graceful shutdown verified
- [ ] Data persistence verified

## Performance Validation

### 1. Write Performance

```bash
# Measure write performance
time for i in {1..10}; do
  curl -X POST http://localhost:8000/process \
    -F "text=Performance test $i" > /dev/null 2>&1
done
```

- [ ] Write operations complete successfully
- [ ] Performance acceptable (20-40% slower than autocommit)
- [ ] No timeouts or errors

### 2. Shutdown Time

```bash
# Measure shutdown time
time docker-compose restart fir_pipeline
```

- [ ] Shutdown completes within 35s (30s grace + 5s overhead)
- [ ] No forced termination
- [ ] All data flushed successfully

### 3. Startup Time

```bash
# Measure startup time
time docker-compose up -d fir_pipeline
```

- [ ] Startup completes within 2 minutes
- [ ] Health checks pass
- [ ] Service ready to accept requests

## Production Readiness

### 1. Monitoring Setup

- [ ] CloudWatch logs configured (if AWS)
- [ ] Shutdown logs monitored
- [ ] Flush operation metrics tracked
- [ ] Alert on flush failures

### 2. Backup Verification

- [ ] Database backups running every 6 hours
- [ ] Backup includes both MySQL and SQLite
- [ ] Backup restoration tested
- [ ] Backup retention policy configured

### 3. Disaster Recovery

- [ ] Recovery procedure documented
- [ ] RTO (Recovery Time Objective) defined
- [ ] RPO (Recovery Point Objective) = 0 (zero data loss)
- [ ] Failover tested

### 4. Documentation

- [ ] Implementation guide reviewed
- [ ] Quick reference accessible
- [ ] Troubleshooting guide complete
- [ ] Runbook updated

## Sign-Off

### Development Team

- [ ] Code changes reviewed
- [ ] Tests passing
- [ ] Documentation complete
- [ ] Ready for deployment

**Signed**: _________________ **Date**: _________

### QA Team

- [ ] All tests executed
- [ ] Performance acceptable
- [ ] No data loss observed
- [ ] Ready for production

**Signed**: _________________ **Date**: _________

### Operations Team

- [ ] Deployment procedure reviewed
- [ ] Monitoring configured
- [ ] Backup verified
- [ ] Ready to deploy

**Signed**: _________________ **Date**: _________

## Post-Deployment Validation

### Day 1

- [ ] Monitor shutdown logs
- [ ] Verify no data loss incidents
- [ ] Check performance metrics
- [ ] Review error logs

### Week 1

- [ ] Analyze restart patterns
- [ ] Verify backup integrity
- [ ] Review flush operation metrics
- [ ] Collect performance data

### Month 1

- [ ] Calculate actual uptime
- [ ] Verify zero data loss maintained
- [ ] Review and optimize if needed
- [ ] Update documentation

## Acceptance Criteria Met

✅ **Zero data loss on service restart**

Evidence:
- [ ] Transaction management implemented
- [ ] Database flush on shutdown
- [ ] WAL mode enabled
- [ ] MySQL durability configured
- [ ] Graceful shutdown with timeout
- [ ] Comprehensive testing completed
- [ ] Documentation provided

**Status**: ☐ Not Started | ☐ In Progress | ☐ Complete | ☐ Verified

**Notes**:
_____________________________________________
_____________________________________________
_____________________________________________
