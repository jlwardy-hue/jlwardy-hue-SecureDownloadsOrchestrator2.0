# SecureDownloadsOrchestrator 2.0

[![CI/CD Pipeline](https://github.com/jlwardy-hue/jlwardy-hue-SecureDownloadsOrchestrator2.0/actions/workflows/ci.yml/badge.svg)](https://github.com/jlwardy-hue/jlwardy-hue-SecureDownloadsOrchestrator2.0/actions/workflows/ci.yml)
[![CodeQL Security Scan](https://github.com/jlwardy-hue/jlwardy-hue-SecureDownloadsOrchestrator2.0/actions/workflows/codeql.yml/badge.svg)](https://github.com/jlwardy-hue/jlwardy-hue-SecureDownloadsOrchestrator2.0/actions/workflows/codeql.yml)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An advanced, secure, and intelligent file organization system that monitors directories and automatically categorizes files based on type, with extensible architecture for AI-powered classification and security scanning.

## 🚀 Features

### Core Functionality
- **Real-time File Monitoring**: Watches source directories for new and modified files using `watchdog`
- **Intelligent File Classification**: Multi-layer classification using file extensions and magic number detection
- **Configurable Categories**: Fully customizable file categorization rules via YAML configuration
- **Secure File Handling**: Enterprise-grade security with comprehensive threat protection
- **Robust Logging**: Comprehensive logging to console and files with automatic rotation

### Security Features
- **Antivirus Integration**: ClamAV integration with EICAR test validation and fail-closed behavior
- **Archive Bomb Protection**: Comprehensive protection against zip/tar bombs with configurable limits
- **Path Traversal Protection**: Advanced path validation preventing directory traversal attacks
- **Atomic Move Detection**: File stability checking to prevent processing incomplete files
- **Quarantine System**: Automatic isolation of suspicious files with detailed logging
- **Log Rotation**: Automatic log rotation to prevent disk space exhaustion

### Advanced Features
- **AI-Ready Architecture**: Extensible design for future AI-powered file classification
- **Security Scanning Framework**: Modular security scanning system with configurable policies
- **Metadata Extraction**: Automatic file metadata collection (size, creation/modification dates, MIME types)
- **Error Recovery**: Graceful error handling and recovery mechanisms
- **Configuration Validation**: Comprehensive configuration validation with helpful error messages

### Automation & CI/CD
- **GitHub Actions Workflows**: Complete CI/CD pipeline with security validation and EICAR testing
- **Automated Dependency Updates**: Dependabot integration for security updates
- **Code Quality Enforcement**: Automated linting, type checking, and security scanning
- **Self-Hosted Runner Support**: Optimized for self-hosted GitHub Actions runners

## 📁 Repository Structure

```
SecureDownloadsOrchestrator2.0/
├── orchestrator/                 # Main application package
│   ├── main.py                  # Application entry point and orchestration
│   ├── config_loader.py         # Configuration management and validation
│   ├── logger.py                # Logging setup and utilities
│   ├── file_watcher.py          # File system monitoring
│   ├── classifier.py            # File classification engine
│   └── file_type_detector.py    # Magic number-based file type detection
├── .github/                     # GitHub automation and templates
│   ├── workflows/               # CI/CD workflows
│   │   ├── ci.yml              # Main CI/CD pipeline
│   │   ├── codeql.yml          # Security scanning
│   │   ├── deploy.yml          # Deployment workflow
│   │   └── self-hosted-test.yml # Self-hosted runner verification
│   ├── ISSUE_TEMPLATE/          # Issue templates
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── PULL_REQUEST_TEMPLATE.md # Pull request template
│   └── dependabot.yml          # Automated dependency updates
├── main.py                      # Compatibility entry point
├── config.yaml                  # Main configuration file
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── README.md                    # This file
├── ARCHITECTURE.md              # Detailed architecture documentation
└── .gitignore                   # Git ignore rules
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git (for cloning the repository)

### 🚀 Automated Setup (Recommended)

For the smoothest setup experience, use our automated setup script which requires **zero manual steps** - all directories are created automatically:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jlwardy-hue/jlwardy-hue-SecureDownloadsOrchestrator2.0.git
   cd jlwardy-hue-SecureDownloadsOrchestrator2.0
   ```

2. **Run automated setup:**
   ```bash
   # Quick setup (one command - creates all directories automatically)
   ./setup.sh
   
   # Or using Python directly
   python scripts/setup.py
   
   # Setup with virtual environment (recommended for development)
   ./setup.sh venv
   
   # Just verify current setup
   ./setup.sh verify
   ```

3. **Start the application:**
   ```bash
   python -m orchestrator.main
   ```

**✨ What the automated setup does:**
- ✅ Validates Python version and dependencies
- ✅ Installs required packages automatically
- ✅ **Creates source and destination directories from config.yaml**
- ✅ **Creates all category subdirectories (documents, images, etc.)**
- ✅ Sets up logging directories
- ✅ Validates configuration
- ✅ **No manual directory creation required!**

### 📋 Manual Setup

If you prefer manual setup or need to troubleshoot:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jlwardy-hue/jlwardy-hue-SecureDownloadsOrchestrator2.0.git
   cd jlwardy-hue-SecureDownloadsOrchestrator2.0
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   # Production dependencies
   pip install -r requirements.txt
   
   # Development dependencies (optional)
   pip install -r requirements-dev.txt
   ```

4. **Configure the application:**
   ```bash
   # Edit config.yaml to set your source and destination directories
   nano config.yaml
   ```

5. **Run the application:**
   ```bash
   # Recommended: Using the module directly (no PYTHONPATH needed)
   python -m orchestrator.main
   
   # Alternative: Using the compatibility entry point
   python main.py
   ```

### 🔧 Optional System Dependencies

For enhanced functionality, install these optional system packages:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install tesseract-ocr poppler-utils

# macOS
brew install tesseract poppler

# Windows (via Chocolatey)
choco install tesseract poppler
```

**What these enable:**
- **tesseract-ocr**: OCR text extraction for document metadata
- **poppler-utils**: PDF to image conversion for OCR processing

### ✅ Verification

Verify your installation is working correctly:

```bash
# Quick verification (bash script)
./setup.sh verify

# Or using Python directly
python scripts/setup.py --verify

# Or run basic tests
python -m pytest tests/test_import_orchestrator.py -v
```

### 🔄 Cleanup and Reset

To reset to a fresh state:

```bash
# Clean build artifacts and reset (bash script)
./setup.sh clean

# Or using Python directly
python scripts/setup.py --clean

# Or manual cleanup
rm -rf __pycache__ .pytest_cache logs/*.log
```

### 🆘 Troubleshooting

#### Common Issues

**❌ "No module named 'orchestrator'"**
- Ensure you're running from the repository root directory
- Verify Python path: `python -c "import sys; print('\n'.join(sys.path))"`
- Try: `python -m pip install -e .` (development install)

**❌ "Permission denied" on directories**
- Check that source/destination directories have correct permissions
- On Unix systems: `chmod 755 /path/to/directories`

**❌ "Missing dependencies" after pip install**
- Update pip: `python -m pip install --upgrade pip`
- Try installing individually: `pip install watchdog PyYAML python-magic`
- On Ubuntu: `sudo apt install python3-dev libmagic1`

**❌ "Configuration validation failed"**
- Verify `config.yaml` syntax with: `python -c "import yaml; yaml.safe_load(open('config.yaml'))"`
- Check file permissions on `config.yaml`
- Ensure source/destination paths exist or can be created

**⚠️ OCR features disabled**
- Install tesseract: See "Optional System Dependencies" above
- Verify installation: `tesseract --version`

**⚠️ PDF processing disabled**
- Install poppler: See "Optional System Dependencies" above
- Verify installation: `pdftoppm -h`

#### Getting Help

1. **Run diagnostics:** `python scripts/setup.py --verify`
2. **Check comprehensive troubleshooting guide:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. **Review deployment documentation:** [DEPLOYMENT.md](DEPLOYMENT.md)
2. **Check logs:** Look in `logs/app.log` for detailed error messages
3. **Test imports:** `python -c "from orchestrator.main import main; print('✓ OK')"`
4. **Validate config:** `python -c "from orchestrator.config_loader import load_config; print('✓ Config OK')"`

For additional help, please open an issue with:
- Output of `python scripts/setup.py --verify`
- Your operating system and Python version
- Complete error messages from logs

## 🚀 Production Deployment

For production environments, additional considerations apply beyond basic setup:

### 📋 Production Requirements

- **ClamAV Integration**: Install ClamAV for security scanning
  ```bash
  # Ubuntu/Debian
  sudo apt install clamav clamav-daemon clamav-freshclam
  sudo systemctl enable clamav-daemon clamav-freshclam
  sudo freshclam  # Update virus definitions
  ```

- **System Service**: Set up as systemd service for auto-start and monitoring
- **Security Hardening**: Configure fail-closed security, proper permissions
- **Monitoring**: Log rotation, disk space monitoring, performance metrics
- **Backup Strategy**: Regular backup of configuration and organized files

### 🔗 Production Documentation

📖 **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete production deployment guide covering:
- System requirements and dependencies
- Security configuration and hardening  
- Service setup with systemd
- Monitoring and maintenance procedures
- Scaling and performance optimization
- Backup and recovery procedures

🔧 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Comprehensive troubleshooting guide with:
- Common error scenarios and solutions
- Performance troubleshooting steps
- Log analysis and debugging techniques
- Emergency recovery procedures

### Configuration

The application is configured via `config.yaml`. Key configuration sections:

```yaml
directories:
  source: "/path/to/monitor"        # Directory to monitor for new files
  destination: "/path/to/organize"  # Base directory for organized files

categories:
  documents:
    extensions: [".pdf", ".doc", ".docx", ".txt"]
    destination: "documents"        # Subdirectory under destination
  images:
    extensions: [".jpg", ".jpeg", ".png", ".gif"]
    destination: "images"
  # ... additional categories

logging:
  console:
    enabled: true
    level: "INFO"
  file:
    enabled: true
    path: "./logs/app.log"
    level: "DEBUG"
    rotation:
      enabled: true
      max_bytes: 10485760  # 10MB
      backup_count: 5

security:
  fail_closed: true                    # Fail-closed security behavior
  archive_limits:
    max_files: 1000                    # Max files per archive
    max_total_size: 104857600          # 100MB max extracted size
    max_depth: 10                      # Max directory nesting
    max_file_size: 52428800            # 50MB max individual file

processing:
  enable_ai_classification: false      # Future AI features
  enable_security_scan: true           # Enable antivirus scanning
  enable_archive_extraction: true      # Enable archive processing

atomic_move:
  enabled: true                        # Enable file stability checking
  duration_seconds: 2                  # Check duration
  check_interval: 0.5                  # Check frequency
```

### Security Configuration

The application includes comprehensive security features that can be configured:

#### Antivirus Scanning
- **ClamAV Integration**: Automatic virus scanning with EICAR test validation
- **Fail-Closed Behavior**: Files are quarantined when scanning fails (configurable)
- **Quarantine System**: Automatic isolation of threats with detailed logging

#### Archive Protection
- **Bomb Protection**: Prevents resource exhaustion from malicious archives
- **Size Limits**: Configurable limits for files, total size, and nesting depth
- **Path Validation**: Prevents directory traversal attacks in archive contents

#### File Security
- **Path Traversal Protection**: Comprehensive validation of all file paths
- **Atomic Move Detection**: Ensures files are completely written before processing
- **Quarantine Logging**: Detailed logs for all security events
```

## 🏗️ Development

### Development Environment Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install development dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Run code quality checks:**
   ```bash
   # Code formatting
   black orchestrator/ main.py
   
   # Import sorting
   isort orchestrator/ main.py
   
   # Linting
   flake8 orchestrator/ main.py
   
   # Type checking
   mypy orchestrator/ main.py
   
   # Security scanning
   bandit -r orchestrator/
   ```

### Testing

```bash
# Run all tests (no manual PYTHONPATH needed)
pytest

# Run tests with coverage
pytest --cov=orchestrator --cov-report=html

# Run specific test categories
pytest -m unit      # Unit tests only
pytest -m integration  # Integration tests only

# Run basic import tests to verify package setup
pytest tests/test_import_orchestrator.py
```

**Note**: Tests work out of the box thanks to `pytest.ini` configuration that automatically sets the Python path. No manual `PYTHONPATH` configuration is required.

### Project Structure Guidelines

- **orchestrator/**: Main application package
  - Keep modules focused and single-responsibility
  - Use type hints throughout
  - Include comprehensive docstrings
- **tests/**: Test modules (mirror orchestrator/ structure)
- **docs/**: Documentation files
- **.github/**: GitHub-specific automation and templates

## 🔄 Workflows & Automation

### GitHub Actions Workflows

#### CI/CD Pipeline (`.github/workflows/ci.yml`)
- **Triggered on**: Push to any branch, Pull Requests
- **Runs on**: Self-hosted runner (Linux x64)
- **Steps**:
  - Code checkout
  - Python environment setup
  - Dependency installation
  - Code quality checks (linting, formatting, type checking)
  - Security scanning
  - Unit and integration tests
  - Build artifact creation
  - Test coverage reporting

#### CodeQL Security Scanning (`.github/workflows/codeql.yml`)
- **Triggered on**: Push to main, Pull Requests, Weekly schedule
- **Purpose**: Automated security vulnerability detection
- **Languages**: Python
- **Integration**: Results appear in GitHub Security tab

#### Deployment (`.github/workflows/deploy.yml`)
- **Triggered on**: Manual dispatch, Push to main branch
- **Purpose**: Production deployment automation
- **Features**: Environment-specific deployments, rollback capabilities

#### Self-Hosted Runner Test (`.github/workflows/self-hosted-test.yml`)
- **Triggered on**: Push to main, Manual dispatch
- **Purpose**: Verify self-hosted runner functionality
- **Outputs**: System information, runner capabilities

### Dependabot Configuration

Automated dependency updates for:
- Python packages (pip)
- GitHub Actions
- Security-focused updates with priority
- Weekly update schedule

## 🤖 AI & Copilot Integration

### GitHub Copilot Usage

This project is optimized for GitHub Copilot assistance:

- **Code Completion**: Well-structured modules with clear patterns for Copilot suggestions
- **Documentation**: Comprehensive docstrings help Copilot understand context
- **Testing**: Consistent test patterns for Copilot-assisted test generation
- **Configuration**: Clear configuration schemas for AI-assisted setup

### AI-Ready Architecture

The system is designed for future AI integrations:

```python
# Example: AI classification hook
def handle_new_file(filepath, logger):
    # Current: Rule-based classification
    file_category = classify_file(filepath, logger)
    
    # Future: AI-enhanced classification
    if config.get('processing', {}).get('enable_ai_classification'):
        ai_category = ai_classify_file(filepath)
        file_category = merge_classifications(file_category, ai_category)
```

### Copilot Best Practices for Contributors

1. **Write descriptive function names**: Helps Copilot understand intent
2. **Use type hints**: Improves Copilot's suggestion accuracy
3. **Include docstrings**: Provides context for better code generation
4. **Follow consistent patterns**: Enables Copilot to learn project conventions
5. **Comment complex logic**: Helps Copilot generate appropriate tests

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

### Getting Started

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run the full test suite**: `pytest`
5. **Run code quality checks**: `black`, `flake8`, `mypy`
6. **Commit your changes**: `git commit -m 'Add amazing feature'`
7. **Push to your branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Code Standards

- **Python Style**: Follow PEP 8, enforced by `black` and `flake8`
- **Type Hints**: Required for all public functions and methods
- **Documentation**: Docstrings required for all modules, classes, and public functions
- **Testing**: Minimum 80% test coverage for new code
- **Security**: All changes must pass security scanning

### Pull Request Process

1. **Use the PR template**: Fill out all sections completely
2. **Link related issues**: Reference any related GitHub issues
3. **Update documentation**: Update README.md and ARCHITECTURE.md if needed
4. **Add tests**: Include tests for new functionality
5. **CI must pass**: All workflow checks must be green
6. **Code review**: At least one approving review required

### Issue Reporting

- **Use issue templates**: Bug reports and feature requests have specific templates
- **Provide context**: Include system information, configuration, and steps to reproduce
- **Search existing issues**: Avoid duplicates by searching first

## 📚 Additional Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Detailed system architecture and design decisions
- **[API Documentation](docs/api.md)**: Detailed API reference (coming soon)
- **[Configuration Guide](docs/configuration.md)**: Advanced configuration options (coming soon)
- **[Troubleshooting Guide](docs/troubleshooting.md)**: Common issues and solutions (coming soon)

## 🔒 Security

### Security Features

- **Input Validation**: All file paths and configuration inputs are validated
- **Safe File Operations**: Secure file handling with proper error checking
- **Configurable Security Scanning**: Framework for extensible security checks
- **No Arbitrary Code Execution**: Static configuration-based operation

### Reporting Security Issues

Please report security vulnerabilities to the repository maintainers privately. Do not create public issues for security vulnerabilities.

### Security Scanning

- **CodeQL**: Automated vulnerability scanning via GitHub Actions
- **Bandit**: Python security linting
- **Dependabot**: Automated dependency vulnerability updates
- **Safety**: Python package vulnerability checking

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **watchdog**: File system monitoring
- **python-magic**: File type detection
- **PyYAML**: Configuration management
- **GitHub Actions**: CI/CD automation
- **GitHub Copilot**: AI-assisted development

## 📞 Support

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for questions and community chat
- **Wiki**: Check the project Wiki for additional documentation and examples

---

**SecureDownloadsOrchestrator 2.0** - Intelligent file organization with enterprise-grade automation and security.