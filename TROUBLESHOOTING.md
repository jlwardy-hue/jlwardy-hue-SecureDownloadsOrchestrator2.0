# Troubleshooting Guide

## SecureDownloadsOrchestrator 2.0 Troubleshooting

This guide helps diagnose and resolve common issues with SecureDownloadsOrchestrator 2.0.

### Quick Diagnostic Commands

```bash
# Check service status
sudo systemctl status secure-orchestrator

# View recent logs
sudo journalctl -u secure-orchestrator -n 50

# Check application logs
tail -f /var/log/secure-orchestrator/application.log

# Verify configuration
python scripts/setup.py --verify

# Check directory permissions
ls -la /data/incoming /data/organized

# Test ClamAV
clamscan --version && echo "ClamAV is working"
```

---

## Common Issues and Solutions

### 1. Service Won't Start

#### Symptoms
- `systemctl start secure-orchestrator` fails
- Service shows "failed" status
- Application doesn't respond

#### Diagnosis
```bash
# Check detailed service status
sudo systemctl status secure-orchestrator -l

# View service logs
sudo journalctl -u secure-orchestrator -f

# Check configuration syntax
python -m orchestrator.config_loader --validate config.yaml

# Verify Python environment
sudo -u secure-orchestrator /opt/secure-orchestrator/venv/bin/python --version

# Check dependencies
sudo -u secure-orchestrator /opt/secure-orchestrator/venv/bin/python -c "import orchestrator; print('OK')"
```

#### Common Causes and Solutions

**1. Configuration Errors**
```bash
# Error: Invalid YAML syntax
# Solution: Validate YAML format
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Error: Missing required configuration sections
# Solution: Check required sections exist
grep -E "directories|categories|logging|application" config.yaml
```

**2. Permission Issues**
```bash
# Error: Permission denied accessing directories
# Solution: Fix ownership and permissions
sudo chown -R secure-orchestrator:secure-orchestrator /opt/secure-orchestrator
sudo chmod -R 755 /data/incoming /data/organized
sudo chmod -R 755 /var/log/secure-orchestrator
```

**3. Missing Dependencies**
```bash
# Error: ModuleNotFoundError
# Solution: Reinstall dependencies
sudo -u secure-orchestrator /opt/secure-orchestrator/venv/bin/pip install -r requirements.txt

# Error: System dependencies missing
# Solution: Install system packages
sudo apt install python3-dev python3-pip
```

**4. Port/Resource Conflicts**
```bash
# Error: Address already in use
# Solution: Check for running processes
ps aux | grep orchestrator
sudo netstat -tulpn | grep :8080  # If using web interface
```

### 2. Files Not Being Processed

#### Symptoms
- Files remain in source directory
- No movement to destination categories
- No quarantine events

#### Diagnosis
```bash
# Check file permissions in source directory
ls -la /data/incoming/

# Verify file watcher is active
sudo journalctl -u secure-orchestrator | grep "watching directory"

# Check for file lock issues
lsof /data/incoming/*

# Monitor file system events
sudo inotifywait -m /data/incoming/
```

#### Common Causes and Solutions

**1. File Permission Issues**
```bash
# Files not readable by service user
sudo chown secure-orchestrator:secure-orchestrator /data/incoming/*
sudo chmod 644 /data/incoming/*
```

**2. File System Events Not Triggering**
```bash
# Check inotify limits
cat /proc/sys/fs/inotify/max_user_watches
cat /proc/sys/fs/inotify/max_user_instances

# Increase limits if needed
echo 'fs.inotify.max_user_watches=524288' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

**3. File Stability Check Failing**
```bash
# Files still being written during processing
# Solution: Adjust stability check duration
# In config.yaml:
atomic_move:
  enabled: true
  duration_seconds: 5  # Increase from default 2
  check_interval: 0.5
```

**4. Network File System Issues**
```bash
# NFS/CIFS mounted directories may have issues
# Solution: Use local directories or configure proper mounting
mount | grep /data/incoming
# Remount with appropriate options for file watching
```

### 3. All Files Being Quarantined

#### Symptoms
- Every file goes to quarantine directory
- Security scan results show "AVUnavailable"
- No files reach category directories

#### Diagnosis
```bash
# Check ClamAV status
sudo systemctl status clamav-daemon
sudo systemctl status clamav-freshclam

# Test ClamAV manually
clamscan --version
clamscan /opt/secure-orchestrator/README.md

# Check ClamAV socket
sudo ls -la /var/run/clamav/

# View quarantine logs
cat /data/organized/quarantine/*.log | head -20
```

#### Solutions

**1. ClamAV Not Running**
```bash
# Start ClamAV services
sudo systemctl start clamav-daemon
sudo systemctl start clamav-freshclam
sudo systemctl enable clamav-daemon
sudo systemctl enable clamav-freshclam

# Update virus definitions
sudo freshclam
```

**2. ClamAV Configuration Issues**
```bash
# Check ClamAV configuration
sudo clamd --config-file=/etc/clamav/clamd.conf --test-config

# Fix common configuration issues
sudo sed -i 's/^Example/#Example/' /etc/clamav/clamd.conf
sudo sed -i 's/^Example/#Example/' /etc/clamav/freshclam.conf
```

**3. Socket Permission Issues**
```bash
# Add secure-orchestrator user to clamav group
sudo usermod -a -G clamav secure-orchestrator

# Restart services
sudo systemctl restart secure-orchestrator
```

**4. Disable Security Scanning (Temporary)**
```yaml
# In config.yaml (for testing only):
processing:
  enable_security_scan: false
```

### 4. High CPU/Memory Usage

#### Symptoms
- High system load
- Application becomes unresponsive
- Out of memory errors

#### Diagnosis
```bash
# Monitor resource usage
top -p $(pgrep -f orchestrator)
htop -p $(pgrep -f orchestrator)

# Check memory usage
ps aux | grep orchestrator | awk '{print $6}'

# Monitor file processing rate
watch "ls /data/incoming | wc -l; ls /data/organized/quarantine | wc -l"

# Check for memory leaks
valgrind --tool=massif python -m orchestrator.main & VAL_PID=$!
echo "Valgrind started in background with PID $VAL_PID"
# When finished, stop valgrind with:
kill $VAL_PID
```

#### Solutions

**1. Large File Processing**
```yaml
# Adjust processing limits in config.yaml
security:
  archive_limits:
    max_file_size: 10485760  # Reduce from 50MB to 10MB
    max_total_size: 52428800  # Reduce total size limit

processing:
  batch_size: 5  # Process fewer files simultaneously
```

**2. OCR Memory Usage**
```yaml
# Disable OCR for large files
processing:
  enable_ocr: false  # Temporarily disable
  
# Or limit OCR to smaller files
ocr:
  max_file_size: 5242880  # 5MB limit for OCR
```

**3. Archive Processing Issues**
```yaml
# Reduce archive extraction limits
security:
  archive_limits:
    max_files: 100     # Reduce from 1000
    max_total_size: 10485760  # 10MB total
```

**4. Service Resource Limits**
```ini
# In /etc/systemd/system/secure-orchestrator.service
[Service]
MemoryMax=1G           # Limit memory usage
CPUQuota=50%          # Limit CPU usage
```

### 5. Configuration Issues

#### Symptoms
- Application fails to start with config errors
- Unexpected behavior with file categorization
- Missing directories not created

#### Diagnosis
```bash
# Validate configuration syntax
python -c "import yaml; print(yaml.safe_load(open('config.yaml')))"

# Check configuration loading
python -c "from orchestrator.config_loader import load_config; print(load_config('config.yaml'))"

# Verify directory configuration
python scripts/setup.py --verify

# Test configuration with dry run
python -m orchestrator.main --config config.yaml --dry-run
```

#### Common Configuration Errors

**1. YAML Syntax Errors**
```yaml
# Wrong (causes parser error):
categories:
  documents:
    extensions [".pdf", ".doc"]  # Missing colon

# Correct:
categories:
  documents:
    extensions: [".pdf", ".doc"]
```

**2. Path Configuration Issues**
```yaml
# Wrong (relative paths may cause issues):
directories:
  source: "./incoming"
  destination: "./organized"

# Correct (use absolute paths):
directories:
  source: "/data/incoming"
  destination: "/data/organized"
```

**3. Missing Required Sections**
```yaml
# Ensure all required sections exist:
directories: {}
categories: {}
logging: {}
application: {}
```

### 6. Logging and Debugging Issues

#### Symptoms
- No log output or insufficient logging
- Log files not rotating
- Cannot trace file processing issues

#### Diagnosis
```bash
# Check log file permissions
ls -la /var/log/secure-orchestrator/

# Verify log rotation
sudo logrotate -d /etc/logrotate.d/secure-orchestrator

# Test logging configuration
python -c "
from orchestrator.logger import setup_logger
import logging
logger = setup_logger('config.yaml')
logger.info('Test message')
"

# Check systemd journal
sudo journalctl -u secure-orchestrator --since "1 hour ago"
```

#### Solutions

**1. Log Directory Permissions**
```bash
# Fix log directory permissions
sudo mkdir -p /var/log/secure-orchestrator
sudo chown -R secure-orchestrator:secure-orchestrator /var/log/secure-orchestrator
sudo chmod 755 /var/log/secure-orchestrator
```

**2. Increase Logging Verbosity**
```yaml
# In config.yaml:
logging:
  console:
    enabled: true
    level: "DEBUG"  # Increase from INFO
  file:
    enabled: true
    level: "DEBUG"
    file: "/var/log/secure-orchestrator/application.log"
```

**3. Configure Log Rotation**
```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/secure-orchestrator << EOF
/var/log/secure-orchestrator/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 secure-orchestrator secure-orchestrator
    postrotate
        systemctl reload secure-orchestrator
    endscript
}
EOF
```

### 7. Network and Connectivity Issues

#### Symptoms
- Cannot update virus definitions
- Dependency installation fails
- External integrations not working

#### Diagnosis
```bash
# Check network connectivity
ping -c 3 google.com
curl -I https://pypi.org

# Check DNS resolution
nslookup pypi.org
nslookup database.clamav.net

# Check firewall rules
sudo iptables -L
sudo ufw status

# Test proxy settings
echo $http_proxy $https_proxy
```

#### Solutions

**1. Firewall Configuration**
```bash
# Allow outbound connections for updates
sudo ufw allow out 80
sudo ufw allow out 443
sudo ufw allow out 53
```

**2. Proxy Configuration**
```bash
# Configure proxy for pip
pip config set global.proxy http://proxy.example.com:8080

# Configure proxy for freshclam
sudo tee -a /etc/clamav/freshclam.conf << EOF
HTTPProxyServer proxy.example.com
HTTPProxyPort 8080
EOF
```

### 8. Performance Issues

#### Symptoms
- Slow file processing
- Delays in file movement
- Timeouts during scanning

#### Diagnosis
```bash
# Monitor file processing times
time clamscan /path/to/test/file
time python -c "from orchestrator.classifier import classify_file; print(classify_file('/path/to/test/file'))"

# Check I/O performance
sudo iotop -p $(pgrep -f orchestrator)
iostat -x 1

# Monitor file system performance
df -h
sudo tune2fs -l /dev/sda1 | grep -i "mount count"
```

#### Solutions

**1. Optimize ClamAV Performance**
```bash
# In /etc/clamav/clamd.conf:
# MaxThreads 4          # Increase thread count
# MaxFileSize 50M       # Limit file size scans
# MaxScanSize 100M      # Limit total scan size
```

**2. Optimize File System**
```bash
# Use faster file systems (ext4, xfs)
# Mount with performance options
# /dev/sda1 /data ext4 defaults,noatime,commit=60 0 2
```

**3. Adjust Processing Timeouts**
```yaml
# In config.yaml:
security:
  clamav:
    timeout: 30  # Reduce from 60 seconds

atomic_move:
  duration_seconds: 1  # Reduce stability check time
```

---

## Advanced Troubleshooting

### Debug Mode

Enable comprehensive debugging:

```bash
# Set debug environment variables
export ORCHESTRATOR_DEBUG=1
export ORCHESTRATOR_LOG_LEVEL=DEBUG

# Run with debug logging
python -m orchestrator.main --config config.yaml --debug
```

### Memory Profiling

For memory leak investigation:

```bash
# Install memory profiler
pip install memory-profiler

# Profile memory usage
python -m memory_profiler -m orchestrator.main
```

### Performance Profiling

For performance analysis:

```bash
# Install profiling tools
pip install py-spy

# Profile running application
sudo py-spy record -o profile.svg --pid $(pgrep -f orchestrator)
```

### Log Analysis

For detailed log analysis:

```bash
# Extract processing times
grep "Pipeline processing complete" /var/log/secure-orchestrator/application.log | \
awk '{print $1, $2, $NF}' | \
sort

# Count quarantine events by hour
grep "quarantined" /var/log/secure-orchestrator/application.log | \
cut -d' ' -f1-2 | \
cut -d':' -f1 | \
uniq -c

# Find longest processing times
grep "Starting pipeline\|Pipeline processing complete" /var/log/secure-orchestrator/application.log | \
grep -B1 "complete" | \
# Process timing analysis
```

---

## Emergency Procedures

### Service Recovery

```bash
# Emergency service restart
sudo systemctl stop secure-orchestrator
sudo systemctl start secure-orchestrator

# Reset to known good state
sudo systemctl stop secure-orchestrator
sudo cp /backup/config-working.yaml /opt/secure-orchestrator/config.yaml
sudo systemctl start secure-orchestrator
```

### Data Recovery

```bash
# Recover from backup
sudo systemctl stop secure-orchestrator
sudo rsync -av /backup/data/ /data/organized/
sudo chown -R secure-orchestrator:secure-orchestrator /data
sudo systemctl start secure-orchestrator
```

### Log Collection for Support

```bash
# Collect diagnostic information
mkdir -p /tmp/orchestrator-debug
sudo journalctl -u secure-orchestrator > /tmp/orchestrator-debug/systemd.log
cp /var/log/secure-orchestrator/*.log /tmp/orchestrator-debug/
cp /opt/secure-orchestrator/config.yaml /tmp/orchestrator-debug/
ps aux | grep orchestrator > /tmp/orchestrator-debug/processes.txt
sudo systemctl status secure-orchestrator > /tmp/orchestrator-debug/status.txt
tar -czf orchestrator-debug-$(date +%Y%m%d-%H%M).tar.gz -C /tmp orchestrator-debug
```

---

## Getting Help

### Before Contacting Support

1. ✅ Check this troubleshooting guide
2. ✅ Review application logs
3. ✅ Verify configuration
4. ✅ Test with minimal configuration
5. ✅ Collect diagnostic information

### Contact Information

- **GitHub Issues**: [Repository Issues](https://github.com/jlwardy-hue/jlwardy-hue-SecureDownloadsOrchestrator2.0/issues)
- **Documentation**: Check README.md and ARCHITECTURE.md
- **Community**: Discussion forums and chat channels

### Issue Reporting Template

```markdown
## Issue Description
Brief description of the problem

## Environment
- OS: Ubuntu 20.04
- Python: 3.8.10
- Application Version: 2.0
- ClamAV Version: 0.103.x

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Logs
```
[Paste relevant log entries]
```

## Configuration
```yaml
[Paste relevant configuration sections]
```

## Additional Context
Any other relevant information
```

This troubleshooting guide covers the most common issues and their solutions. Keep it updated as new issues are discovered and resolved.