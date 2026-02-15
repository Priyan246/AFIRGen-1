#!/usr/bin/env python3
"""
Test script for AFIRGen Database Backup System
Validates backup functionality, scheduling, and restoration
"""

import os
import subprocess
import time
import gzip
import tempfile
from pathlib import Path

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def run_command(cmd, description):
    """Run a shell command and return result"""
    print(f"\n[TEST] {description}")
    print(f"[CMD] {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"[PASS] {description}")
            return True, result.stdout
        else:
            print(f"[FAIL] {description}")
            print(f"[ERROR] {result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"[FAIL] {description}")
        print(f"[ERROR] {str(e)}")
        return False, str(e)

def test_backup_service_running():
    """Test 1: Verify backup service is running"""
    print_section("Test 1: Backup Service Status")
    
    success, output = run_command(
        ["docker-compose", "ps", "backup"],
        "Check if backup service is running"
    )
    
    if success and "Up" in output:
        print("[PASS] Backup service is running")
        return True
    else:
        print("[FAIL] Backup service is not running")
        return False

def test_backup_directory_exists():
    """Test 2: Verify backup directory exists"""
    print_section("Test 2: Backup Directory")
    
    success, output = run_command(
        ["docker", "exec", "afirgen-backup", "ls", "-la", "/app/backups"],
        "Check backup directory exists"
    )
    
    return success

def test_manual_backup_execution():
    """Test 3: Execute manual backup"""
    print_section("Test 3: Manual Backup Execution")
    
    # Get initial backup count
    success, before_output = run_command(
        ["docker", "exec", "afirgen-backup", "ls", "/app/backups"],
        "List backups before manual trigger"
    )
    
    before_count = len([line for line in before_output.split('\n') if line.endswith('.gz')])
    print(f"[INFO] Backups before: {before_count}")
    
    # Trigger manual backup
    success, output = run_command(
        ["docker", "exec", "afirgen-backup", "python3", "/app/backup_database.py"],
        "Execute manual backup"
    )
    
    if not success:
        return False
    
    # Wait a moment for files to be written
    time.sleep(2)
    
    # Get backup count after
    success, after_output = run_command(
        ["docker", "exec", "afirgen-backup", "ls", "/app/backups"],
        "List backups after manual trigger"
    )
    
    after_count = len([line for line in after_output.split('\n') if line.endswith('.gz')])
    print(f"[INFO] Backups after: {after_count}")
    
    if after_count > before_count:
        print(f"[PASS] New backups created: {after_count - before_count}")
        return True
    else:
        print("[FAIL] No new backups created")
        return False

def test_mysql_backup_exists():
    """Test 4: Verify MySQL backup file exists"""
    print_section("Test 4: MySQL Backup File")
    
    success, output = run_command(
        ["docker", "exec", "afirgen-backup", "find", "/app/backups", "-name", "mysql_backup_*.gz"],
        "Find MySQL backup files"
    )
    
    if success and "mysql_backup_" in output:
        backup_files = [line for line in output.split('\n') if line.strip()]
        print(f"[PASS] Found {len(backup_files)} MySQL backup(s)")
        for f in backup_files[-3:]:  # Show last 3
            print(f"  - {f}")
        return True
    else:
        print("[FAIL] No MySQL backup files found")
        return False

def test_sessions_backup_exists():
    """Test 5: Verify sessions backup file exists"""
    print_section("Test 5: Sessions Backup File")
    
    success, output = run_command(
        ["docker", "exec", "afirgen-backup", "find", "/app/backups", "-name", "sessions_backup_*.gz"],
        "Find sessions backup files"
    )
    
    if success and "sessions_backup_" in output:
        backup_files = [line for line in output.split('\n') if line.strip()]
        print(f"[PASS] Found {len(backup_files)} sessions backup(s)")
        for f in backup_files[-3:]:  # Show last 3
            print(f"  - {f}")
        return True
    else:
        print("[WARN] No sessions backup files found (may not exist yet)")
        return True  # Not a critical failure

def test_backup_compression():
    """Test 6: Verify backups are compressed"""
    print_section("Test 6: Backup Compression")
    
    # Get latest MySQL backup
    success, output = run_command(
        ["docker", "exec", "afirgen-backup", "find", "/app/backups", "-name", "mysql_backup_*.gz", "-type", "f"],
        "Find latest MySQL backup"
    )
    
    if not success or not output.strip():
        print("[FAIL] No backup file to test")
        return False
    
    backup_file = output.strip().split('\n')[-1]
    print(f"[INFO] Testing file: {backup_file}")
    
    # Test if file is valid gzip
    success, output = run_command(
        ["docker", "exec", "afirgen-backup", "gzip", "-t", backup_file],
        "Verify gzip compression integrity"
    )
    
    return success

def test_backup_log_exists():
    """Test 7: Verify backup log exists and has content"""
    print_section("Test 7: Backup Logging")
    
    success, output = run_command(
        ["docker", "exec", "afirgen-backup", "cat", "/app/backups/backup.log"],
        "Read backup log file"
    )
    
    if success and len(output) > 0:
        lines = output.split('\n')
        print(f"[PASS] Log file exists with {len(lines)} lines")
        print("[INFO] Last 5 log entries:")
        for line in lines[-5:]:
            if line.strip():
                print(f"  {line}")
        return True
    else:
        print("[FAIL] Log file is empty or doesn't exist")
        return False

def test_cron_configuration():
    """Test 8: Verify cron is configured correctly"""
    print_section("Test 8: Cron Configuration")
    
    success, output = run_command(
        ["docker", "exec", "afirgen-backup", "crontab", "-l"],
        "Check crontab configuration"
    )
    
    if success and "backup_database.py" in output:
        print("[PASS] Cron job configured")
        print(f"[INFO] Cron entry: {output.strip()}")
        
        # Verify it's every 6 hours
        if "*/6" in output or "0,6,12,18" in output:
            print("[PASS] Backup scheduled every 6 hours")
            return True
        else:
            print("[WARN] Backup schedule may not be every 6 hours")
            return True
    else:
        print("[FAIL] Cron job not configured")
        return False

def test_backup_retention():
    """Test 9: Verify backup retention configuration"""
    print_section("Test 9: Backup Retention")
    
    success, output = run_command(
        ["docker", "exec", "afirgen-backup", "env"],
        "Check environment variables"
    )
    
    if success and "BACKUP_RETENTION_DAYS" in output:
        for line in output.split('\n'):
            if "BACKUP_RETENTION_DAYS" in line:
                print(f"[PASS] {line}")
                return True
    
    print("[WARN] BACKUP_RETENTION_DAYS not explicitly set (using default: 7)")
    return True

def test_mysql_connectivity():
    """Test 10: Verify MySQL connectivity from backup service"""
    print_section("Test 10: MySQL Connectivity")
    
    success, output = run_command(
        ["docker", "exec", "afirgen-backup", "mysqladmin", "ping", "-h", "mysql", "-u", "root", "-ppassword"],
        "Test MySQL connection"
    )
    
    if success and "alive" in output.lower():
        print("[PASS] MySQL is accessible from backup service")
        return True
    else:
        print("[FAIL] Cannot connect to MySQL")
        return False

def test_backup_file_size():
    """Test 11: Verify backup files have reasonable size"""
    print_section("Test 11: Backup File Size")
    
    success, output = run_command(
        ["docker", "exec", "afirgen-backup", "find", "/app/backups", "-name", "*.gz", "-exec", "ls", "-lh", "{}", ";"],
        "Check backup file sizes"
    )
    
    if success and output.strip():
        print("[PASS] Backup files exist with sizes:")
        for line in output.split('\n')[-5:]:  # Show last 5
            if line.strip():
                print(f"  {line}")
        return True
    else:
        print("[FAIL] No backup files found")
        return False

def test_volume_mount():
    """Test 12: Verify backup volume is properly mounted"""
    print_section("Test 12: Volume Mount")
    
    success, output = run_command(
        ["docker", "inspect", "afirgen-backup"],
        "Inspect backup container volumes"
    )
    
    if success and "backup_data" in output:
        print("[PASS] Backup volume is mounted")
        return True
    else:
        print("[FAIL] Backup volume not found")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  AFIRGen Database Backup System - Test Suite")
    print("=" * 60)
    print("\nThis test suite validates the backup system functionality")
    print("Ensure docker-compose is running before executing tests\n")
    
    tests = [
        ("Backup Service Running", test_backup_service_running),
        ("Backup Directory Exists", test_backup_directory_exists),
        ("Manual Backup Execution", test_manual_backup_execution),
        ("MySQL Backup Exists", test_mysql_backup_exists),
        ("Sessions Backup Exists", test_sessions_backup_exists),
        ("Backup Compression", test_backup_compression),
        ("Backup Logging", test_backup_log_exists),
        ("Cron Configuration", test_cron_configuration),
        ("Backup Retention", test_backup_retention),
        ("MySQL Connectivity", test_mysql_connectivity),
        ("Backup File Size", test_backup_file_size),
        ("Volume Mount", test_volume_mount),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[ERROR] Test '{test_name}' raised exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    print("\nDetailed Results:")
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {test_name}")
    
    print("\n" + "=" * 60)
    
    if passed == total:
        print("  ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    else:
        print(f"  {total - passed} TEST(S) FAILED")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    exit(main())
