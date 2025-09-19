# Deployment Guide

## Production Deployment of SecureDownloadsOrchestrator 2.0

This guide covers production deployment, configuration, monitoring, and maintenance of SecureDownloadsOrchestrator 2.0.

### Prerequisites

#### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows
- **Python**: 3.8 or higher
- **Memory**: Minimum 512MB, Recommended 2GB+
- **Storage**: Minimum 1GB free space for quarantine and logs
- **Network**: Internet access for dependency updates (optional)

#### Security Requirements
- **ClamAV**: For antivirus scanning (recommended for production)
- **Tesseract OCR**: For document metadata extraction (optional)
- **Poppler Utils**: For PDF processing (optional)

### Installation

#### 1. System Dependencies (Ubuntu/Debian)
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install ClamAV for security scanning
sudo apt install clamav clamav-daemon clamav-freshclam -y

# Install OCR dependencies (optional)
sudo apt install tesseract-ocr poppler-utils -y

# Start and enable ClamAV services
sudo systemctl start clamav-daemon
sudo systemctl enable clamav-daemon
sudo systemctl start clamav-freshclam
sudo systemctl enable clamav-freshclam

# Update virus definitions
sudo freshclam
```

#### 2. Application Installation
```bash
# Clone the repository
git clone https://github.com/jlwardy-hue/jlwardy-hue-SecureDownloadsOrchestrator2.0.git
cd jlwardy-hue-SecureDownloadsOrchestrator2.0

# Create production user (recommended)
sudo useradd -r -s /bin/false -d /opt/secure-orchestrator secure-orchestrator

# Install to production directory
sudo mkdir -p /opt/secure-orchestrator
sudo cp -r . /opt/secure-orchestrator/
sudo chown -R secure-orchestrator:secure-orchestrator /opt/secure-orchestrator

# Install Python dependencies
cd /opt/secure-orchestrator
sudo -u secure-orchestrator python3 -m venv venv
sudo -u secure-orchestrator venv/bin/pip install -r requirements.txt
```

### Configuration

#### 1. Production Configuration
Create `/opt/secure-orchestrator/config-production.yaml`:

```yaml
# Production Configuration
directories:
  source: "/data/incoming"
  destination: "/data/organized"

categories:
  documents:
    extensions: [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"]
    destination: "documents"
  images:
    extensions: [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg", ".webp"]
    destination: "images"
  audio:
    extensions: [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"]
    destination: "audio"
  video:
    extensions: [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".webm"]
    destination: "video"
  archives:
    extensions: [".zip", ".rar", ".7z", ".tar", ".gz", ".tar.gz"]
    destination: "archives"
  code:
    extensions: [".py", ".js", ".html", ".css", ".java", ".cpp", ".json", ".xml"]
    destination: "code"
  executables:
    extensions: [".exe", ".msi", ".dmg", ".deb", ".rpm"]
    destination: "executables"

# Enhanced logging for production
logging:
  console:
    enabled: true
    level: "INFO"
  file:
    enabled: true
    level: "DEBUG"
    file: "/var/log/secure-orchestrator/application.log"
    max_bytes: 10485760  # 10MB
    backup_count: 10
    rotation: true

# Security configuration
security:
  fail_closed: true
  clamav:
    enabled: true
    timeout: 60
  archive_limits:
    max_files: 1000
    max_total_size: 104857600  # 100MB
    max_file_size: 52428800   # 50MB

# Atomic move detection
atomic_move:
  enabled: true
  duration_seconds: 3
  check_interval: 0.5

# Processing configuration
processing:
  enable_ai_classification: false
  enable_security_scan: true
  enable_ocr: true
  enable_archive_extraction: true
  enable_unified_pipeline: true

application:
  name: "SecureDownloadsOrchestrator"
  version: "2.0"
  startup:
    validate_config: true
    create_missing_dirs: true
```

#### 2. Directory Setup
```bash
# Create data directories
sudo mkdir -p /data/incoming /data/organized
sudo chown -R secure-orchestrator:secure-orchestrator /data

# Create log directory
sudo mkdir -p /var/log/secure-orchestrator
sudo chown -R secure-orchestrator:secure-orchestrator /var/log/secure-orchestrator

# Set appropriate permissions
sudo chmod 755 /data/incoming /data/organized
sudo chmod 755 /var/log/secure-orchestrator
```

#### 3. Systemd Service Setup
Create `/etc/systemd/system/secure-orchestrator.service`:

```ini
[Unit]
Description=SecureDownloadsOrchestrator 2.0
After=network.target clamav-daemon.service
Wants=clamav-daemon.service
StartLimitBurst=5
StartLimitIntervalSec=10

[Service]
Type=exec
User=secure-orchestrator
Group=secure-orchestrator
WorkingDirectory=/opt/secure-orchestrator
ExecStart=/opt/secure-orchestrator/venv/bin/python -m orchestrator.main --config config-production.yaml
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=secure-orchestrator

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/data /var/log/secure-orchestrator

# Resource limits
LimitNOFILE=65536
MemoryMax=2G

[Install]
WantedBy=multi-user.target
```

#### 4. Enable and Start Service
```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable service for auto-start
sudo systemctl enable secure-orchestrator

# Start the service
sudo systemctl start secure-orchestrator

# Check service status
sudo systemctl status secure-orchestrator
```

### Monitoring and Maintenance

#### 1. Log Management
```bash
# View real-time logs
sudo journalctl -u secure-orchestrator -f

# View application logs
sudo tail -f /var/log/secure-orchestrator/application.log

# Check quarantine events
sudo find /data/organized/quarantine -name "*.log" -mtime -1 | xargs cat
```

#### 2. Health Checks
```bash
# Check service status
sudo systemctl is-active secure-orchestrator

# Check ClamAV status
sudo systemctl is-active clamav-daemon

# Check disk usage
df -h /data /var/log/secure-orchestrator

# Check memory usage
ps aux | grep python | grep orchestrator
```

#### 3. Maintenance Tasks

**Daily Tasks:**
```bash
#!/bin/bash
# daily-maintenance.sh

# Update virus definitions
sudo freshclam

# Check disk usage
df -h /data | awk 'NR==2{print $5}' | sed 's/%//g' | \
while read usage; do
  if [ $usage -gt 80 ]; then
    echo "WARNING: Disk usage is ${usage}%" | logger -t secure-orchestrator
  fi
done

# Check quarantine files older than 30 days
# Move old quarantine files to backup and log the action
mkdir -p /data/organized/quarantine_backup
find /data/organized/quarantine -type f -mtime +30 | while read file; do
  mv "$file" /data/organized/quarantine_backup/ && \
  echo "Moved $file to quarantine_backup" | logger -t secure-orchestrator
done

# Rotate logs if needed
sudo logrotate /etc/logrotate.d/secure-orchestrator
```

**Weekly Tasks:**
```bash
#!/bin/bash
# weekly-maintenance.sh

# Check for application updates
cd /opt/secure-orchestrator
git fetch origin

# Archive old logs
find /var/log/secure-orchestrator -name "*.log.*" -mtime +7 -exec gzip {} \;

# Performance report
echo "Weekly Performance Report - $(date)" >> /var/log/secure-orchestrator/weekly-report.log
ps aux | grep orchestrator >> /var/log/secure-orchestrator/weekly-report.log
df -h /data >> /var/log/secure-orchestrator/weekly-report.log
```

### Security Hardening

#### 1. Network Security
```bash
# Allow only necessary traffic (example with ufw)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw enable
```

#### 2. File System Security
```bash
# Set immutable bit on configuration files
sudo chattr +i /opt/secure-orchestrator/config-production.yaml

# Regular permission audit
find /opt/secure-orchestrator -type f -perm -002 -exec ls -la {} \;
```

#### 3. Monitoring and Alerting
Create `/opt/secure-orchestrator/monitoring.sh`:

```bash
#!/bin/bash
# monitoring.sh - Send alerts for critical events

# Check for high quarantine activity
quarantine_count=$(find /data/organized/quarantine -name "*.log" -mtime -1 | wc -l)
if [ $quarantine_count -gt 10 ]; then
    echo "ALERT: High quarantine activity - $quarantine_count files quarantined in 24h" | \
    mail -s "SecureOrchestrator Alert" admin@example.com
fi

# Check service health
if ! systemctl is-active --quiet secure-orchestrator; then
    echo "CRITICAL: SecureOrchestrator service is down" | \
    mail -s "SecureOrchestrator CRITICAL" admin@example.com
fi

# Check disk space
usage=$(df /data | awk 'NR==2{print $5}' | sed 's/%//g')
if [ $usage -gt 90 ]; then
    echo "CRITICAL: Disk usage is ${usage}%" | \
    mail -s "SecureOrchestrator Disk Alert" admin@example.com
fi
```

### Scaling and Performance

#### 1. Horizontal Scaling
For high-volume environments, consider:

- **Multiple Instances**: Deploy separate instances for different file types
- **Load Balancing**: Use HAProxy or nginx for request distribution
- **Shared Storage**: Use NFS or distributed file systems
- **Message Queues**: Implement Redis or RabbitMQ for task distribution

#### 2. Performance Tuning
```yaml
# High-performance configuration additions
processing:
  parallel_processing: true
  max_workers: 4
  batch_size: 10

security:
  clamav:
    timeout: 30  # Reduce for faster processing
    
atomic_move:
  duration_seconds: 1  # Reduce for faster detection
  check_interval: 0.2
```

### Backup and Recovery

#### 1. Backup Strategy
```bash
#!/bin/bash
# backup.sh

# Configuration backup
cp /opt/secure-orchestrator/config-production.yaml /backup/config-$(date +%Y%m%d).yaml

# Data backup (use rsync for incremental)
rsync -av --delete /data/organized/ /backup/data/

# Log backup
tar -czf /backup/logs-$(date +%Y%m%d).tar.gz /var/log/secure-orchestrator/
```

#### 2. Recovery Procedures
```bash
# Service recovery
sudo systemctl stop secure-orchestrator
sudo systemctl start secure-orchestrator

# Configuration recovery
sudo cp /backup/config-YYYYMMDD.yaml /opt/secure-orchestrator/config-production.yaml
sudo systemctl restart secure-orchestrator

# Data recovery
rsync -av /backup/data/ /data/organized/
```

### Troubleshooting

#### Common Issues

1. **Service Won't Start**
   ```bash
   # Check logs
   sudo journalctl -u secure-orchestrator -n 50
   
   # Check configuration
   sudo -u secure-orchestrator /opt/secure-orchestrator/venv/bin/python -m orchestrator.main --config config-production.yaml --verify
   ```

2. **High CPU Usage**
   ```bash
   # Check for stuck processes
   ps aux | grep orchestrator
   
   # Monitor file processing
   watch "ls -la /data/incoming | wc -l"
   ```

3. **Files Not Processing**
   ```bash
   # Check permissions
   ls -la /data/incoming
   
   # Check ClamAV
   sudo systemctl status clamav-daemon
   
   # Check quarantine logs
   tail -f /data/organized/quarantine/*.log
   ```

### Support and Updates

#### 1. Update Procedure
```bash
# Stop service
sudo systemctl stop secure-orchestrator

# Backup current installation
sudo cp -r /opt/secure-orchestrator /backup/secure-orchestrator-$(date +%Y%m%d)

# Update application
cd /opt/secure-orchestrator
sudo -u secure-orchestrator git pull origin main
sudo -u secure-orchestrator venv/bin/pip install -r requirements.txt

# Test configuration
sudo -u secure-orchestrator venv/bin/python scripts/setup.py --verify

# Start service
sudo systemctl start secure-orchestrator
```

#### 2. Emergency Contacts
- **Application Issues**: Create GitHub issue
- **Security Incidents**: Follow incident response plan
- **Critical Failures**: Contact system administrator

This deployment guide provides a comprehensive foundation for production deployment while maintaining security best practices and operational excellence.