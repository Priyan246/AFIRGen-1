# Database Backup System - Validation Checklist

## Pre-Deployment Validation

Use this checklist to verify the database backup system is properly configured and operational.

## Prerequisites

- [ ] Docker and Docker Compose installed
- [ ] AFIRGen system running (`docker-compose up -d`)
- [ ] MySQL service healthy and accessible
- [ ] `.env` file configured with database credentials

## Installation Verification

### 1. Files Created

Verify all backup system files exist:

- [ ] `backup_database.py` - Main backup script
- [ ] `backup_scheduler.sh` - Cron scheduler script
- [ ] `Dockerfile.backup` - Backup service Docker image
- [ ] `test_backup.py` - Test suite
- [ ] `DATABASE-BACKUP-GUIDE.md` - Complete documentation
- [ ] `DATABASE-BACKUP-QUICK-REFERENCE.md` - Quick reference
- [ ] `DATABASE-BACKUP-IMPLEMENTATION-SUMMARY.md` - Implementation summary
- [ ] `DATABASE-BACKUP-VALIDATION-CHECKLIST.md` - This file

### 2. Configuration Files Updated

- [ ] `docker-compose.yaml` includes `backup` service
- [ ] `docker-compose.yaml` includes `backup_data` volume
- [ ] `.env.example` includes `BACKUP_RETENTION_DAYS`
- [ ] `DATABASE.md` updated with backup information

## Service Deployment

### 3. Build and Start Backup Service

```bash
# Build the backup service
docker-compose build backup

# Start the backup service
docker-compose up -d backup

# Verify service is running
docker-compose ps backup
```

Expected output: Service status should be "Up"

- [ ] Backup service builds successfully
- [ ] Backup service starts without errors
- [ ] Service status shows "Up"

### 4. Check Service Logs

```bash
docker-compose logs backup
```

Expected: Should see initialization messages and initial backup execution

- [ ] No error messages in logs
- [ ] Initial backup executed successfully
- [ ] Cron daemon started

## Functional Testing

### 5. Run Test Suite

```bash
python3 test_backup.py
```

Expected: All 12 tests should pass

- [ ] Test 1: Backup Service Running - PASS
- [ ] Test 2: Backup Directory Exists - PASS
- [ ] Test 3: Manual Backup Execution - PASS
- [ ] Test 4: MySQL Backup Exists - PASS
- [ ] Test 5: Sessions Backup Exists - PASS
- [ ] Test 6: Backup Compression - PASS
- [ ] Test 7: Backup Logging - PASS
- [ ] Test 8: Cron Configuration - PASS
- [ ] Test 9: Backup Retention - PASS
- [ ] Test 10: MySQL Connectivity - PASS
- [ ] Test 11: Backup File Size - PASS
- [ ] Test 12: Volume Mount - PASS

### 6. Manual Backup Test

```bash
# Trigger manual backup
docker exec afirgen-backup python3 /app/backup_database.py

# Check exit code (should be 0)
echo $?
```

- [ ] Manual backup completes successfully
- [ ] Exit code is 0
- [ ] No error messages

### 7. Verify Backup Files Created

```bash
# List backup files
docker exec afirgen-backup ls -lh /app/backups/

# Should see:
# - mysql_backup_YYYYMMDD_HHMMSS.sql.gz
# - sessions_backup_YYYYMMDD_HHMMSS.db.gz (if sessions.db exists)
# - backup.log
```

- [ ] MySQL backup file exists
- [ ] Sessions backup file exists (or warning logged if no sessions.db)
- [ ] Backup log file exists
- [ ] Files have reasonable sizes (>0 bytes)

### 8. Verify Backup Compression

```bash
# Test backup integrity
docker exec afirgen-backup find /app/backups -name "*.gz" -exec gzip -t {} \;
```

Expected: No errors, all files are valid gzip archives

- [ ] All .gz files pass integrity check
- [ ] No corruption errors

### 9. Check Backup Log

```bash
# View backup log
docker exec afirgen-backup cat /app/backups/backup.log
```

Expected: Should see successful backup entries with timestamps

- [ ] Log contains backup start messages
- [ ] Log shows successful MySQL backup
- [ ] Log shows successful sessions backup (or warning)
- [ ] Log shows cleanup operations
- [ ] Timestamps are correct

### 10. Verify Cron Configuration

```bash
# Check crontab
docker exec afirgen-backup crontab -l
```

Expected: Should see entry like `0 */6 * * * /usr/bin/python3 /app/backup_database.py`

- [ ] Cron job is configured
- [ ] Schedule is every 6 hours (`*/6`)
- [ ] Command path is correct

### 11. Test MySQL Connectivity

```bash
# Test MySQL connection from backup container
docker exec afirgen-backup mysqladmin ping -h mysql -u root -p${MYSQL_PASSWORD}
```

Expected: `mysqld is alive`

- [ ] MySQL is accessible from backup container
- [ ] Credentials are correct

### 12. Verify Volume Mount

```bash
# Inspect backup container
docker inspect afirgen-backup | grep -A 10 "Mounts"
```

Expected: Should see mounts for `backup_data` and `sessions_data`

- [ ] `backup_data` volume is mounted to `/app/backups`
- [ ] `sessions_data` volume is mounted to `/app` (read-only)

## Backup Schedule Verification

### 13. Wait for Scheduled Backup

Wait 6 hours and verify automatic backup runs:

```bash
# Check for new backup files
docker exec afirgen-backup find /app/backups -name "*.gz" -mtime -0.3 -ls
```

- [ ] New backup files created after 6 hours
- [ ] Backup log shows scheduled execution
- [ ] No errors in logs

### 14. Verify Retention Policy

After 7+ days (or configured retention period):

```bash
# Check that old backups are removed
docker exec afirgen-backup find /app/backups -name "*.gz" -mtime +7
```

Expected: No files older than retention period

- [ ] Old backups are automatically removed
- [ ] Retention policy is working correctly

## Restoration Testing

### 15. Test MySQL Restoration

```bash
# 1. Create test FIR record (via API or directly in DB)
# 2. Take backup
docker exec afirgen-backup python3 /app/backup_database.py

# 3. Delete test record
# 4. Restore from backup (see DATABASE-BACKUP-GUIDE.md)
# 5. Verify test record is restored
```

- [ ] Backup contains test data
- [ ] Restoration completes without errors
- [ ] Data is correctly restored

### 16. Test Sessions Restoration

```bash
# 1. Create test session
# 2. Take backup
# 3. Delete sessions.db
# 4. Restore from backup
# 5. Verify session exists
```

- [ ] Sessions backup works
- [ ] Restoration completes without errors
- [ ] Session data is correctly restored

## Performance Validation

### 17. Measure Backup Duration

```bash
# Time a manual backup
time docker exec afirgen-backup python3 /app/backup_database.py
```

Expected: <60 seconds for typical database sizes

- [ ] MySQL backup completes in <60 seconds
- [ ] Sessions backup completes in <5 seconds
- [ ] Total time is acceptable

### 18. Check Resource Usage

```bash
# Monitor during backup
docker stats afirgen-backup --no-stream
```

Expected: CPU <50%, Memory <512MB

- [ ] CPU usage is reasonable
- [ ] Memory usage is within limits
- [ ] No resource exhaustion

### 19. Verify No Impact on Application

During backup execution:

```bash
# Test API endpoint
curl http://localhost:8000/health
```

Expected: Application remains responsive

- [ ] Application responds normally during backup
- [ ] No performance degradation
- [ ] No connection errors

## Monitoring and Alerting

### 20. Set Up Monitoring

- [ ] Backup logs are being collected
- [ ] Disk space monitoring configured
- [ ] Alert on backup failures (optional)
- [ ] Alert on old backups (optional)

### 21. Create Monitoring Script

```bash
#!/bin/bash
# Check for recent backups
LATEST=$(docker exec afirgen-backup find /app/backups -name "mysql_backup_*.gz" -mtime -0.3 | head -1)
if [ -z "$LATEST" ]; then
    echo "ERROR: No recent backup!"
    exit 1
fi
echo "OK: Recent backup found"
```

- [ ] Monitoring script created
- [ ] Script runs successfully
- [ ] Alerts configured (if applicable)

## Documentation Review

### 22. Documentation Completeness

- [ ] `DATABASE-BACKUP-GUIDE.md` reviewed and accurate
- [ ] `DATABASE-BACKUP-QUICK-REFERENCE.md` reviewed
- [ ] `DATABASE.md` updated with backup information
- [ ] Restoration procedures documented
- [ ] Troubleshooting guide available

### 23. Team Training

- [ ] Team knows how to view backup logs
- [ ] Team knows how to trigger manual backups
- [ ] Team knows restoration procedures
- [ ] Team knows troubleshooting steps

## Production Readiness

### 24. Security Review

- [ ] Database credentials secured (not hardcoded)
- [ ] Backup files have appropriate permissions
- [ ] Backup volume is persistent
- [ ] No sensitive data in logs

### 25. Disaster Recovery Plan

- [ ] Backup restoration procedure documented
- [ ] Recovery Time Objective (RTO) defined
- [ ] Recovery Point Objective (RPO) defined (6 hours)
- [ ] DR plan tested

### 26. AWS Deployment Preparation (if applicable)

- [ ] S3 bucket created for backup storage
- [ ] IAM roles configured
- [ ] S3 sync script prepared (optional)
- [ ] RDS automated backups configured (if using RDS)

## Final Validation

### 27. End-to-End Test

Complete workflow test:

1. [ ] Start fresh AFIRGen system
2. [ ] Create test FIR records
3. [ ] Wait for automatic backup (or trigger manually)
4. [ ] Verify backup files created
5. [ ] Simulate disaster (delete database)
6. [ ] Restore from backup
7. [ ] Verify all data restored correctly
8. [ ] Verify application works normally

### 28. Sign-Off

- [ ] All tests passed
- [ ] Documentation complete
- [ ] Team trained
- [ ] Production ready

## Acceptance Criteria

✅ **Database backups every 6 hours**

- [ ] Backups run automatically every 6 hours
- [ ] Both MySQL and SQLite databases backed up
- [ ] Backups are compressed
- [ ] Old backups are automatically cleaned up
- [ ] Restoration procedures work correctly
- [ ] Documentation is complete
- [ ] System is production-ready

## Notes

Record any issues, deviations, or special configurations:

```
Date: _______________
Tester: _______________

Issues Found:
1. 
2. 
3. 

Resolutions:
1. 
2. 
3. 

Additional Notes:


```

## Support

For issues or questions:
- Review `DATABASE-BACKUP-GUIDE.md`
- Check `DATABASE-BACKUP-QUICK-REFERENCE.md`
- Run `python3 test_backup.py` for diagnostics
- Check logs: `docker-compose logs backup`

---

**Validation Status**: ⬜ Not Started | 🟡 In Progress | ✅ Complete

**Date Completed**: _______________

**Validated By**: _______________

**Approved By**: _______________
