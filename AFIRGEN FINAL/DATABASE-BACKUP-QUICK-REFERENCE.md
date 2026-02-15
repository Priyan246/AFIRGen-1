# Database Backup - Quick Reference

## Quick Commands

### Start Backup Service
```bash
docker-compose up -d backup
```

### View Backup Logs
```bash
docker-compose logs -f backup
```

### Manual Backup
```bash
docker exec afirgen-backup python3 /app/backup_database.py
```

### List Backups
```bash
docker exec afirgen-backup ls -lh /app/backups/
```

### Copy Backups to Host
```bash
docker cp afirgen-backup:/app/backups ./backups
```

### Test Backup System
```bash
python3 test_backup.py
```

## Backup Schedule

- **Frequency**: Every 6 hours
- **Times**: 00:00, 06:00, 12:00, 18:00 UTC
- **Retention**: 7 days (configurable)

## Backup Files

- **MySQL**: `mysql_backup_YYYYMMDD_HHMMSS.sql.gz`
- **Sessions**: `sessions_backup_YYYYMMDD_HHMMSS.db.gz`

## Restore MySQL

```bash
# 1. Stop application
docker-compose stop fir_pipeline

# 2. Decompress backup
gunzip mysql_backup_20240212_120000.sql.gz

# 3. Copy to MySQL container
docker cp mysql_backup_20240212_120000.sql afirgen-mysql:/tmp/restore.sql

# 4. Restore
docker exec afirgen-mysql mysql -u root -p${MYSQL_PASSWORD} ${MYSQL_DB} < /tmp/restore.sql

# 5. Restart
docker-compose start fir_pipeline
```

## Restore Sessions

```bash
# 1. Stop application
docker-compose stop fir_pipeline

# 2. Decompress and copy
gunzip sessions_backup_20240212_120000.db.gz
docker cp sessions_backup_20240212_120000.db afirgen-fir_pipeline:/app/sessions.db

# 3. Restart
docker-compose start fir_pipeline
```

## Configuration

Edit `.env` file:
```bash
BACKUP_RETENTION_DAYS=7  # Days to keep backups
```

## Troubleshooting

### Service won't start
```bash
docker-compose logs backup
docker-compose restart backup
```

### No backups created
```bash
# Check cron
docker exec afirgen-backup crontab -l

# Test manual backup
docker exec afirgen-backup python3 /app/backup_database.py
```

### MySQL connection failed
```bash
docker exec afirgen-backup mysqladmin ping -h mysql -u root -ppassword
```

## Monitoring

### Check recent backups
```bash
docker exec afirgen-backup find /app/backups -name "*.gz" -mtime -1 -ls
```

### Check backup size
```bash
docker exec afirgen-backup du -sh /app/backups
```

### Verify backup integrity
```bash
docker exec afirgen-backup gzip -t /app/backups/mysql_backup_*.gz
```

## AWS S3 Sync (Optional)

```bash
# Add to backup script
aws s3 sync /app/backups s3://your-bucket/afirgen-backups/
```

## Support

See full documentation: `DATABASE-BACKUP-GUIDE.md`
