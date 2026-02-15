#!/usr/bin/env python3
"""
Database Backup Script for AFIRGen
Performs automated backups of MySQL database and SQLite sessions database
"""

import os
import subprocess
import datetime
import logging
import sys
from pathlib import Path
import gzip
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/backups/backup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
MYSQL_HOST = os.getenv('MYSQL_HOST', 'mysql')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'password')
MYSQL_DB = os.getenv('MYSQL_DB', 'fir_db')
BACKUP_DIR = os.getenv('BACKUP_DIR', '/app/backups')
BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '7'))
SESSION_DB_PATH = os.getenv('SESSION_DB_PATH', '/app/sessions.db')


def ensure_backup_directory():
    """Create backup directory if it doesn't exist"""
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    logger.info(f"Backup directory: {BACKUP_DIR}")


def backup_mysql():
    """Backup MySQL database using mysqldump"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"mysql_backup_{timestamp}.sql"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    compressed_path = f"{backup_path}.gz"
    
    try:
        logger.info(f"Starting MySQL backup: {backup_filename}")
        
        # Build mysqldump command
        cmd = [
            'mysqldump',
            f'--host={MYSQL_HOST}',
            f'--port={MYSQL_PORT}',
            f'--user={MYSQL_USER}',
            f'--password={MYSQL_PASSWORD}',
            '--single-transaction',
            '--quick',
            '--lock-tables=false',
            '--routines',
            '--triggers',
            '--events',
            MYSQL_DB
        ]
        
        # Execute mysqldump and save to file
        with open(backup_path, 'w') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300  # 5 minute timeout
            )
        
        if result.returncode != 0:
            logger.error(f"MySQL backup failed: {result.stderr}")
            return False
        
        # Compress the backup
        logger.info(f"Compressing backup: {compressed_path}")
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        os.remove(backup_path)
        
        # Get file size
        size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
        logger.info(f"MySQL backup completed: {compressed_path} ({size_mb:.2f} MB)")
        
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("MySQL backup timed out after 5 minutes")
        return False
    except Exception as e:
        logger.error(f"MySQL backup error: {str(e)}")
        return False


def backup_sessions_db():
    """Backup SQLite sessions database"""
    if not os.path.exists(SESSION_DB_PATH):
        logger.warning(f"Sessions database not found: {SESSION_DB_PATH}")
        return True  # Not a critical failure
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"sessions_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    compressed_path = f"{backup_path}.gz"
    
    try:
        logger.info(f"Starting sessions database backup: {backup_filename}")
        
        # Copy SQLite database
        shutil.copy2(SESSION_DB_PATH, backup_path)
        
        # Compress the backup
        logger.info(f"Compressing backup: {compressed_path}")
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        os.remove(backup_path)
        
        # Get file size
        size_kb = os.path.getsize(compressed_path) / 1024
        logger.info(f"Sessions backup completed: {compressed_path} ({size_kb:.2f} KB)")
        
        return True
        
    except Exception as e:
        logger.error(f"Sessions backup error: {str(e)}")
        return False


def cleanup_old_backups():
    """Remove backups older than retention period"""
    try:
        logger.info(f"Cleaning up backups older than {BACKUP_RETENTION_DAYS} days")
        
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=BACKUP_RETENTION_DAYS)
        deleted_count = 0
        
        for filename in os.listdir(BACKUP_DIR):
            if filename.endswith('.gz') and (filename.startswith('mysql_backup_') or filename.startswith('sessions_backup_')):
                filepath = os.path.join(BACKUP_DIR, filename)
                file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_mtime < cutoff_time:
                    os.remove(filepath)
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {filename}")
        
        logger.info(f"Cleanup completed: {deleted_count} old backups removed")
        return True
        
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        return False


def verify_backup_integrity(backup_path):
    """Verify that a compressed backup can be decompressed"""
    try:
        with gzip.open(backup_path, 'rb') as f:
            # Try to read first 1KB to verify it's valid
            f.read(1024)
        return True
    except Exception as e:
        logger.error(f"Backup integrity check failed for {backup_path}: {str(e)}")
        return False


def main():
    """Main backup execution"""
    logger.info("=" * 60)
    logger.info("Starting AFIRGen Database Backup")
    logger.info("=" * 60)
    
    # Ensure backup directory exists
    ensure_backup_directory()
    
    # Perform backups
    mysql_success = backup_mysql()
    sessions_success = backup_sessions_db()
    
    # Cleanup old backups
    cleanup_success = cleanup_old_backups()
    
    # Summary
    logger.info("=" * 60)
    logger.info("Backup Summary:")
    logger.info(f"  MySQL Backup: {'SUCCESS' if mysql_success else 'FAILED'}")
    logger.info(f"  Sessions Backup: {'SUCCESS' if sessions_success else 'FAILED'}")
    logger.info(f"  Cleanup: {'SUCCESS' if cleanup_success else 'FAILED'}")
    logger.info("=" * 60)
    
    # Exit with appropriate code
    if mysql_success and sessions_success:
        logger.info("All backups completed successfully")
        sys.exit(0)
    else:
        logger.error("Some backups failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
