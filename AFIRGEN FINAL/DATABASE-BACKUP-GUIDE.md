# AFIRGen Database Backup System

## Overview

The AFIRGen system includes an automated database backup solution that runs every 6 hours to ensure data protection and disaster recovery capabilities.

## Features

- **Automated Backups**: Runs every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)
- **Dual Database Support**: Backs up both MySQL (FIR records) and SQLite (sessions)
- **Compression**: All backups are gzip-compressed to save storage space
- **Retention Policy**: Automatically removes backups older than configured retention period (default: 7 days)
- **Logging**: Comprehensive logging of all backup operations
- **Docker Integration**: Runs as a separate service in docker-compose

## Architecture

### Components

1. **backup_database.py**: Python script that performs the actual backup operations
2. **backup_scheduler.sh**: Shell script that sets up cron jobs and manages scheduling
3. **Dockerfile.backup**: Docker image for the backup service
4. **docker-compose.yaml**: Service definition with proper dependencies and volumes

### Backup Schedule

The system uses cron to schedule backups every 6 hours:
```
0 */6 * * *  (At minute 0 past every 6th hour)
```

This translates to:
- 00:00 (midnight)
- 06:00 (6 AM)
- 12:00 (noon)
- 18:00 (6 PM)

## Configuration

### Environment Variables

Configure the backup service using these environment variables in your `.env` file:

```bash
# MySQL Configuration (inherited from main service)
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DB=fir_db

# Backup-Specific Configuration
BACKUP_RETENTION_DAYS=7  # Number of days to keep backups
```

### Docker Compose Configuration

The backup service is defined in `docker-compose.yaml`:

```yaml
backup:
  build:
    context: .
    dockerfile: Dockerfile.backup
  environment:
    - MYSQL_HOST=mysql
    - MYSQL_PASSWORD=${MYSQL_PASSWORD}
    - BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}
  volumes:
    - backup_data:/app/backups
    - sessions_data:/app:ro
  depends_on:
    mysql:
      condition: service_healthy
  restart: always
```

## Usage

### Starting the Backup Service

The backup service starts automatically with docker-compose:

```bash
docker-compose up -d backup
```

### Viewing Backup Logs

Monitor backup operations in real-time:

```bash
# View live logs
docker-compose logs -f backup

# View backup log file
docker exec afirgen-backup cat /app/backups/backup.log
```

### Manual Backup Trigger

To trigger a backup manually without waiting for the scheduled time:

```bash
docker exec afirgen-backup python3 /app/backup_database.py
```

### Listing Backups

View all available backups:

```bash
docker exec afirgen-backup ls -lh /app/backups/
```

### Accessing Backup Files

Backups are stored in a Docker volume. To copy backups to your host machine:

```bash
# Copy all backups to current directory
docker cp afirgen-backup:/app/backups ./backups

# Copy specific backup
docker cp afirgen-backup:/app/backups/mysql_backup_20240212_120000.sql.gz ./
```

## Backup File Format

### MySQL Backups

- **Filename**: `mysql_backup_YYYYMMDD_HHMMSS.sql.gz`
- **Format**: Compressed SQL dump
- **Contents**: Complete database schema and data
- **Typical Size**: 1-10 MB (compressed)

Example: `mysql_backup_20240212_120000.sql.gz`

### Sessions Backups

- **Filename**: `sessions_backup_YYYYMMDD_HHMMSS.db.gz`
- **Format**: Compressed SQLite database
- **Contents**: Session state and validation history
- **Typical Size**: 100-500 KB (compressed)

Example: `sessions_backup_20240212_120000.db.gz`

## Restoration Procedures

### Restoring MySQL Database

1. **Stop the application** (to prevent data conflicts):
   ```bash
   docker-compose stop fir_pipeline
   ```

2. **Copy backup to MySQL container**:
   ```bash
   # Decompress backup
   gunzip mysql_backup_20240212_120000.sql.gz
   
   # Copy to MySQL container
   docker cp mysql_backup_20240212_120000.sql afirgen-mysql:/tmp/restore.sql
   ```

3. **Restore the database**:
   ```bash
   docker exec afirgen-mysql mysql -u root -p${MYSQL_PASSWORD} ${MYSQL_DB} < /tmp/restore.sql
   ```

4. **Restart the application**:
   ```bash
   docker-compose start fir_pipeline
   ```

### Restoring Sessions Database

1. **Stop the application**:
   ```bash
   docker-compose stop fir_pipeline
   ```

2. **Replace sessions database**:
   ```bash
   # Decompress backup
   gunzip sessions_backup_20240212_120000.db.gz
   
   # Copy to container
   docker cp sessions_backup_20240212_120000.db afirgen-fir_pipeline:/app/sessions.db
   ```

3. **Restart the application**:
   ```bash
   docker-compose start fir_pipeline
   ```

## Monitoring and Alerts

### Health Checks

Monitor backup service health:

```bash
# Check if backup service is running
docker-compose ps backup

# Check recent backup activity
docker exec afirgen-backup tail -n 50 /app/backups/backup.log
```

### Backup Success Verification

Verify that backups are being created:

```bash
# List backups created in last 24 hours
docker exec afirgen-backup find /app/backups -name "*.gz" -mtime -1 -ls
```

### Setting Up Alerts

For production environments, consider:

1. **CloudWatch Logs**: Forward backup logs to CloudWatch
2. **SNS Notifications**: Send alerts on backup failures
3. **Monitoring Script**: Create a script to verify backup freshness

Example monitoring script:

```bash
#!/bin/bash
# Check if backup was created in last 7 hours
LATEST_BACKUP=$(docker exec afirgen-backup find /app/backups -name "mysql_backup_*.gz" -mtime -0.3 | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "ERROR: No recent backup found!"
    # Send alert (email, Slack, PagerDuty, etc.)
    exit 1
else
    echo "OK: Recent backup found: $LATEST_BACKUP"
    exit 0
fi
```

## Storage Management

### Backup Volume Size

Monitor backup volume usage:

```bash
docker exec afirgen-backup du -sh /app/backups
```

### Adjusting Retention Period

To change how long backups are kept, update the environment variable:

```bash
# In .env file
BACKUP_RETENTION_DAYS=14  # Keep backups for 14 days
```

Then restart the backup service:

```bash
docker-compose restart backup
```

### Manual Cleanup

To manually remove old backups:

```bash
# Remove backups older than 30 days
docker exec afirgen-backup find /app/backups -name "*.gz" -mtime +30 -delete
```

## AWS Deployment Considerations

### S3 Integration

For AWS deployments, consider syncing backups to S3:

1. **Install AWS CLI in backup container**:
   ```dockerfile
   RUN apt-get install -y awscli
   ```

2. **Add S3 sync to backup script**:
   ```python
   # After successful backup
   subprocess.run([
       'aws', 's3', 'sync',
       '/app/backups',
       's3://your-bucket/afirgen-backups/',
       '--exclude', '*.log'
   ])
   ```

3. **Configure IAM role** with S3 write permissions

### RDS Automated Backups

If using AWS RDS instead of containerized MySQL:

- RDS provides automated backups (point-in-time recovery)
- Backup window can be configured in RDS settings
- Retention period: 1-35 days
- Manual snapshots can be created for long-term retention

In this case, you only need to backup the sessions database.

## Troubleshooting

### Backup Service Won't Start

**Check logs**:
```bash
docker-compose logs backup
```

**Common issues**:
- MySQL not ready: Ensure MySQL health check is passing
- Permission issues: Check volume mount permissions
- Missing environment variables: Verify .env file

### Backups Not Being Created

**Verify cron is running**:
```bash
docker exec afirgen-backup ps aux | grep cron
```

**Check crontab**:
```bash
docker exec afirgen-backup crontab -l
```

**Test manual backup**:
```bash
docker exec afirgen-backup python3 /app/backup_database.py
```

### Backup Files Too Large

**Solutions**:
1. Increase retention period to reduce frequency
2. Implement incremental backups
3. Use S3 with lifecycle policies (move to Glacier)
4. Clean up old FIR records from database

### Restoration Fails

**Check backup integrity**:
```bash
# Test decompression
gunzip -t mysql_backup_20240212_120000.sql.gz

# If successful, try restoration again
```

**Verify MySQL credentials**:
```bash
docker exec afirgen-mysql mysql -u root -p${MYSQL_PASSWORD} -e "SHOW DATABASES;"
```

## Best Practices

1. **Test Restorations Regularly**: Verify backups can be restored successfully
2. **Monitor Backup Size**: Track growth trends to plan storage capacity
3. **Secure Backup Storage**: Encrypt backups if storing sensitive data
4. **Off-Site Backups**: Copy backups to S3 or another location for disaster recovery
5. **Document Procedures**: Keep restoration procedures up-to-date
6. **Automate Verification**: Create scripts to verify backup integrity
7. **Alert on Failures**: Set up notifications for backup failures

## Security Considerations

1. **Backup Encryption**: Consider encrypting backups at rest
2. **Access Control**: Limit who can access backup files
3. **Secure Transfer**: Use encrypted channels (S3 with SSL) for backup transfers
4. **Credential Management**: Use AWS Secrets Manager for database credentials
5. **Audit Logging**: Log all backup and restoration activities

## Performance Impact

The backup process is designed to minimize impact on the running system:

- **Single Transaction**: Uses `--single-transaction` for consistent snapshots
- **No Table Locks**: Uses `--lock-tables=false` to avoid blocking writes
- **Resource Limits**: Backup container has CPU and memory limits
- **Off-Peak Scheduling**: Default schedule includes off-peak hours (00:00, 06:00)

Typical backup duration:
- MySQL backup: 10-60 seconds (depending on database size)
- Sessions backup: 1-5 seconds
- Total impact: Minimal, <1% CPU usage during backup

## Compliance and Audit

For compliance requirements:

1. **Backup Logs**: All operations logged with timestamps
2. **Retention Policy**: Configurable retention meets regulatory requirements
3. **Immutability**: Consider S3 Object Lock for immutable backups
4. **Audit Trail**: Backup logs can be forwarded to SIEM systems

## Support and Maintenance

### Regular Maintenance Tasks

- **Weekly**: Verify recent backups exist
- **Monthly**: Test restoration procedure
- **Quarterly**: Review retention policy and storage usage
- **Annually**: Update backup procedures documentation

### Getting Help

If you encounter issues:

1. Check this documentation
2. Review backup logs: `/app/backups/backup.log`
3. Check Docker logs: `docker-compose logs backup`
4. Verify MySQL connectivity: `docker exec afirgen-backup mysqladmin ping -h mysql`

## Changelog

- **2024-02-12**: Initial backup system implementation
  - 6-hour backup schedule
  - MySQL and SQLite backup support
  - Compression and retention policies
  - Docker integration

