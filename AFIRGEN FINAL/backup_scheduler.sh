#!/bin/bash
# Database Backup Scheduler for AFIRGen
# Runs backup every 6 hours using cron

set -e

echo "Starting AFIRGen Backup Scheduler"
echo "Backup interval: Every 6 hours"
echo "Backup retention: ${BACKUP_RETENTION_DAYS:-7} days"

# Create cron job for 6-hour backups (at 00:00, 06:00, 12:00, 18:00)
CRON_SCHEDULE="0 */6 * * *"

# Create crontab entry
echo "${CRON_SCHEDULE} /usr/bin/python3 /app/backup_database.py >> /app/backups/backup.log 2>&1" > /etc/cron.d/backup-cron

# Give execution rights on the cron job
chmod 0644 /etc/cron.d/backup-cron

# Apply cron job
crontab /etc/cron.d/backup-cron

# Create the log file to be able to run tail
touch /app/backups/backup.log

echo "Cron job installed: ${CRON_SCHEDULE}"
echo "Running initial backup..."

# Run initial backup
/usr/bin/python3 /app/backup_database.py

echo "Initial backup completed. Starting cron daemon..."

# Start cron in foreground
cron -f
