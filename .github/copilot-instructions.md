# SecureDownloadsOrchestrator 2.0

SecureDownloadsOrchestrator 2.0 is a Python-based secure file organization system that monitors directories and automatically categorizes files based on type, with security scanning, OCR metadata extraction, and AI-ready architecture.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## ⚠️ CRITICAL NETWORK REQUIREMENTS

**This repository requires reliable internet connectivity for full development functionality:**

- **Dev dependencies installation**: Requires PyPI access for pytest, black, flake8, mypy, isort, bandit, safety
- **Security scanning**: `safety check` requires network access to vulnerability databases
- **CI/CD compatibility**: GitHub Actions workflows expect these tools to be available

**In restricted network environments (air-gapped, firewalled, etc.):**
- Core application functionality works offline (file monitoring, organization, basic security)
- Development tools (linting, testing, CI) may not be installable
- See "Restricted Network Environments" section below for workarounds

## Working Effectively

### Bootstrap, Build, and Test the Repository

1. **Install dependencies:**
   ```bash
   # Core dependencies (ALWAYS WORKS - no network issues observed)
   pip install -r requirements.txt
   # Takes ~10 seconds. NEVER CANCEL. Set timeout to 60+ seconds.
   
   # Dev dependencies (REQUIRES STABLE NETWORK CONNECTION)
   pip install -r requirements-dev.txt
   # Takes ~25 seconds if network is stable. OFTEN FAILS with PyPI timeouts.
   # If this fails, see "Restricted Network Environments" section below.
   ```
   - **Core dependencies**: watchdog, PyYAML, python-magic, pytesseract, Pillow, pdf2image
   - **Dev dependencies**: pytest, black, flake8, mypy, isort, bandit, safety, sphinx
   - **CRITICAL**: Dev dependency installation frequently fails due to PyPI connection timeouts

2. **Verify setup:**
   ```bash
   ./setup.sh verify
   # OR
   python scripts/setup.py --verify
   ```
   - Takes ~0.2 seconds. Validates Python version, dependencies, and configuration.

3. **Run tests:**
   ```bash
   # FIRST: Check if pytest is available
   python -c "import pytest; print('pytest available')" || echo "pytest not installed - see network requirements"
   
   # Basic import validation (takes ~0.4 seconds)
   pytest tests/test_import_orchestrator.py -v
   
   # Unit tests only (takes ~8.5 seconds) - NEVER CANCEL
   pytest tests/unit/ -v
   
   # Full test suite with coverage (takes ~36 seconds) - NEVER CANCEL 
   pytest --cov=orchestrator --cov-report=html
   ```
   - **CRITICAL**: pytest may not be available due to network installation issues
   - NEVER CANCEL test runs. Set timeout to 120+ seconds for full test suite.
   - Tests include unit, integration, and security tests (63 total tests)
   - **If pytest unavailable**: Use `python -c "import orchestrator; print('Basic imports work')"` for basic validation

### Code Quality and Linting

**CRITICAL**: These tools require network installation and may not be available in restricted environments.

**ALWAYS verify tools are available before attempting to use:**

```bash
# Verify linting tools are installed
python -c "import black; print('black available')" || echo "❌ black not available"
python -c "import isort; print('isort available')" || echo "❌ isort not available" 
python -c "import flake8; print('flake8 available')" || echo "❌ flake8 not available"
python -c "import mypy; print('mypy available')" || echo "❌ mypy not available"
```

**If tools are available, run these commands before committing or the CI (.github/workflows/ci.yml) will fail:**

```bash
# Fix code formatting (takes ~0.6 seconds)
black orchestrator/ main.py

# Fix import sorting (takes ~0.2 seconds)
isort orchestrator/ main.py

# Check linting (takes ~0.45 seconds)
flake8 orchestrator/ main.py --statistics --count

# Check type hints (takes ~2.6 seconds) - NEVER CANCEL, much slower than other tools
mypy orchestrator/ main.py --show-error-codes --show-error-context
```

**CRITICAL**: Set timeout to 30+ seconds for MyPy. It takes 4x longer than documented and may appear to hang.

**Known linting issues that are acceptable:**
- Flake8: Some complexity warnings (C901) for existing complex functions
- Mypy: Missing type stubs for pytesseract (install `types-PyYAML` if needed)
- Mypy: Some Optional type issues in pipeline.py (existing technical debt)

### Run the Application

1. **Configure the application:**
   ```bash
   # Edit config.yaml to set your source and destination directories
   nano config.yaml
   ```
   - Default config monitors `/tmp/test_watch` and organizes to `/tmp/test_dest`
   - Update `directories.source` and `directories.destination` for your use case

2. **Run the application:**
   ```bash
   # Recommended: Using the module directly (no PYTHONPATH needed)
   python -m orchestrator.main
   
   # Alternative: Using the compatibility entry point
   python main.py
   ```
   - Takes ~0.2 seconds to start. Application runs continuously monitoring directories.
   - Use Ctrl+C to stop gracefully.
   - **Note**: Application does not support --help flag. It requires a valid config.yaml file.

3. **Quick setup with virtual environment:**
   ```bash
   ./setup.sh venv
   source venv/bin/activate
   ```

## Validation

### End-to-End Testing
After making changes, ALWAYS test the complete workflow:

1. **Configure test directories:**
   ```bash
   # Edit config.yaml to set test directories, or use defaults:
   # source: "/tmp/test_watch"
   # destination: "/tmp/test_dest"
   mkdir -p /tmp/test_watch /tmp/test_dest
   ```

2. **Start the application** in one terminal:
   ```bash
   python -m orchestrator.main
   ```
   - Application starts in ~0.2 seconds
   - Look for "File monitoring service started successfully" message
   - Directory structure will be created automatically

3. **Test file organization** in another terminal:
   ```bash
   # Create test files in the source directory
   echo "test content" > /tmp/test_watch/test.txt
   echo "print('hello')" > /tmp/test_watch/script.py
   
   # Wait for processing (files may be quarantined if ClamAV unavailable)
   sleep 3
   
   # Verify directory structure is created
   ls -la /tmp/test_dest/
   # Should show: documents, code, images, audio, video, archives, executables, quarantine
   
   # Check quarantine directory (files go here when security scanning fails-closed)
   ls -la /tmp/test_dest/quarantine/
   # May contain quarantined files if ClamAV is not available
   ```

4. **Always run all quality checks (if tools are available):**
   ```bash
   # Verify tools first
   python -c "import black, isort, flake8, mypy, pytest" || echo "Some tools missing - see network requirements"
   
   # Run checks if available
   black orchestrator/ main.py
   isort orchestrator/ main.py
   flake8 orchestrator/ main.py
   mypy orchestrator/ main.py
   pytest
   ```

5. **Validate application functionality:**
   ```bash
   # Check quarantine logs to understand file processing
   cat /tmp/test_dest/quarantine/*.log
   
   # Verify directory structure was created correctly
   ls -la /tmp/test_dest/
   # Expected: archives, audio, code, documents, executables, images, quarantine, video
   
   # Application working correctly if:
   # - All category directories are created
   # - Files are moved to quarantine with explanatory logs
   # - Logs show "File monitoring service started successfully"
   ```

**Note**: File monitoring and organization works in real-time. The application creates category directories automatically and monitors for file system events. 

**IMPORTANT SECURITY BEHAVIOR**: Files may be quarantined in `/tmp/test_dest/quarantine/` if security scanning is enabled but ClamAV is not available (fail-closed behavior). This is expected and secure. Each quarantined file will have a corresponding `.log` file explaining why it was quarantined.

To test normal file organization, either:
1. Install ClamAV: `sudo apt install clamav` 
2. Or check that quarantine logs indicate files are being processed correctly

### Security Testing
```bash
# FIRST: Verify security tools are available
python -c "import bandit; print('bandit available')" || echo "❌ bandit not available"

# Run security-specific tests (takes ~18 seconds) - NEVER CANCEL
pytest tests/security/ -v

# Run security scanning (takes ~0.3 seconds)
bandit -r orchestrator/ -f txt

# Run dependency scanning - REQUIRES NETWORK ACCESS
safety check
# Note: safety check REQUIRES network access and WILL FAIL in restricted environments
```

## Common Tasks

### Restricted Network Environments

**If dev dependencies fail to install due to network timeouts:**

```bash
# 1. Verify core functionality works
python -c "import orchestrator; print('✅ Core application ready')"
python scripts/setup.py --verify

# 2. Test basic application functionality
mkdir -p /tmp/test_watch /tmp/test_dest
python -m orchestrator.main &
APP_PID=$!
echo "test" > /tmp/test_watch/test.txt
sleep 3
kill $APP_PID
ls -la /tmp/test_dest/  # Should show directory structure

# 3. Manual code quality checks (without automated tools)
python -m py_compile orchestrator/*.py  # Basic syntax check
python -c "
import ast
import os
for root, dirs, files in os.walk('orchestrator'):
    for file in files:
        if file.endswith('.py'):
            with open(os.path.join(root, file)) as f:
                try:
                    ast.parse(f.read())
                    print(f'✅ {file}')
                except SyntaxError as e:
                    print(f'❌ {file}: {e}')
"

# 4. Alternative approaches
# - Use local/offline package mirrors if available
# - Pre-install tools in base environment
# - Use containerized development environments
# - Skip linting temporarily (document as technical debt)
```

### Development Setup
```bash
# Full automated setup
./setup.sh

# Clean setup (removes old files)
./setup.sh clean

# Setup with virtual environment
./setup.sh venv
```

### Optional System Dependencies
For enhanced functionality (OCR and PDF processing):
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install tesseract-ocr poppler-utils

# macOS
brew install tesseract poppler

# Windows (via Chocolatey)
choco install tesseract poppler
```

**What these enable:**
- **tesseract-ocr**: OCR text extraction for document metadata
- **poppler-utils**: PDF to image conversion for OCR processing

### Project Structure
```
SecureDownloadsOrchestrator2.0/
├── orchestrator/              # Main application package
│   ├── main.py               # Application entry point and orchestration
│   ├── config_loader.py      # Configuration management and validation
│   ├── logger.py             # Logging setup and utilities
│   ├── file_watcher.py       # File system monitoring
│   ├── classifier.py         # File classification engine
│   ├── file_type_detector.py # Magic number-based file type detection
│   └── pipeline.py           # Unified file processing pipeline
├── tests/                    # Test modules
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── security/             # Security-specific tests
├── scripts/                  # Setup and utility scripts
├── .github/workflows/        # CI/CD pipeline definitions
└── config.yaml              # Main configuration file
```

### Key Application Features
- **Real-time file monitoring** using watchdog
- **Intelligent file classification** by extension and magic numbers
- **Security scanning** with ClamAV integration (optional)
- **Archive bomb protection** with configurable limits
- **OCR metadata extraction** from images and PDFs
- **Path traversal protection** and atomic move detection

### Configuration Categories
The application organizes files into these default categories:
- **documents**: .pdf, .doc, .docx, .txt, .rtf, .odt
- **images**: .jpg, .jpeg, .png, .gif, .bmp, .tiff, .svg, .webp
- **audio**: .mp3, .wav, .flac, .aac, .ogg, .m4a
- **video**: .mp4, .avi, .mkv, .mov, .wmv, .webm
- **archives**: .zip, .rar, .7z, .tar, .gz, .tar.gz
- **code**: .py, .js, .html, .css, .java, .cpp, .json, .xml
- **executables**: .exe, .msi, .dmg, .deb, .rpm

### CI/CD Pipeline
The project uses GitHub Actions with comprehensive quality gates:
- **Code formatting** (black, isort)
- **Linting** (flake8) 
- **Type checking** (mypy)
- **Security scanning** (bandit, safety)
- **Testing** across Python 3.8-3.11
- **EICAR antivirus validation**

### Troubleshooting
- **Import errors**: Run `python scripts/setup.py --verify` to check dependencies
- **Permission errors**: Ensure write access to destination directories
- **OCR not working**: Install tesseract-ocr and poppler-utils
- **CI failures**: Always run `black`, `isort`, `flake8`, and `pytest` before committing (if available)
- **Dev dependency installation failures**: See "Restricted Network Environments" section above
- **PyPI timeouts**: Common in sandboxed, air-gapped, or firewalled environments
- **Security scanning network errors**: `safety check` requires internet access and will fail in restricted environments
- **Files quarantined unexpectedly**: Check if ClamAV is installed; without it, security scanning fails closed and quarantines all files
- **Slow MyPy execution**: Type checking takes ~2.6 seconds, significantly longer than other linting tools

### Time Expectations
- **Setup verification**: ~0.8 seconds
- **Core dependency installation**: ~10 seconds (requires network)
- **Dev dependency installation**: ~25 seconds (requires stable network, often fails)
- **Basic tests**: ~0.6 seconds
- **Unit tests**: ~8.3 seconds (33 tests) - NEVER CANCEL
- **Full test suite**: ~36 seconds (63 tests) - NEVER CANCEL
- **Security tests**: ~18 seconds (20 tests) - NEVER CANCEL
- **Code formatting**: ~0.6 seconds
- **Import sorting**: ~0.2 seconds  
- **Linting checks**: ~0.45 seconds
- **Type checking**: ~2.6 seconds (much longer than other tools)
- **Security scanning**: ~0.3 seconds (bandit)
- **Application startup**: ~0.2 seconds

NEVER CANCEL any build or test commands. Most operations complete in under 1 minute, but security tests may take up to 20 seconds.

## Critical Timeout Warnings

**NEVER CANCEL these commands** - they may appear to hang but are working:

- **MyPy type checking**: Takes ~2.6 seconds (4x longer than other linting tools) - set timeout to 30+ seconds
- **Security tests**: Take ~18 seconds (not 5 as initially expected) - set timeout to 60+ seconds  
- **Full test suite**: Takes ~36 seconds - set timeout to 120+ seconds
- **Core dependency installation**: Takes ~10 seconds - set timeout to 60+ seconds
- **Dev dependency installation**: Takes ~25 seconds IF network is stable - set timeout to 180+ seconds

**CRITICAL NETWORK ISSUES**: Dev dependency installation frequently fails due to PyPI timeouts. This is normal in restricted network environments.

If a command appears stuck, wait at least the expected time + 50% buffer before investigating.