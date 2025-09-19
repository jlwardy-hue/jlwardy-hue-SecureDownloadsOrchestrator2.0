# SecureDownloadsOrchestrator 2.0

SecureDownloadsOrchestrator 2.0 is a Python-based secure file organization system that monitors directories and automatically categorizes files based on type, with security scanning, OCR metadata extraction, and AI-ready architecture.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap, Build, and Test the Repository

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
   - Takes ~30 seconds. NEVER CANCEL. Set timeout to 180+ seconds.
   - Installs core dependencies (watchdog, PyYAML, python-magic, pytesseract, Pillow, pdf2image)
   - Installs dev dependencies (pytest, black, flake8, mypy, isort, bandit, safety, sphinx)

2. **Verify setup:**
   ```bash
   ./setup.sh verify
   # OR
   python scripts/setup.py --verify
   ```
   - Takes ~1 second. Validates Python version, dependencies, and configuration.

3. **Run tests:**
   ```bash
   # Basic import validation (takes ~0.4 seconds)
   pytest tests/test_import_orchestrator.py -v
   
   # Unit tests only (takes ~8.5 seconds) - NEVER CANCEL
   pytest tests/unit/ -v
   
   # Full test suite with coverage (takes ~36 seconds) - NEVER CANCEL 
   pytest --cov=orchestrator --cov-report=html
   ```
   - NEVER CANCEL test runs. Set timeout to 120+ seconds for full test suite.
   - Tests include unit, integration, and security tests (63 total tests)

### Code Quality and Linting

**ALWAYS run these commands before committing or the CI (.github/workflows/ci.yml) will fail:**

```bash
# Fix code formatting (takes ~0.6 seconds)
black orchestrator/ main.py

# Fix import sorting (takes ~0.2 seconds)
isort orchestrator/ main.py

# Check linting (takes ~0.4 seconds)
flake8 orchestrator/ main.py --statistics --count

# Check type hints (takes ~0.6 seconds)
mypy orchestrator/ main.py --show-error-codes --show-error-context
```

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
   
   # Verify directory structure is created
   ls -la /tmp/test_dest/
   # Should show: documents, code, images, audio, video, archives, executables, quarantine
   ```

4. **Always run all quality checks:**
   ```bash
   black orchestrator/ main.py
   isort orchestrator/ main.py
   flake8 orchestrator/ main.py
   mypy orchestrator/ main.py
   pytest
   ```

**Note**: File monitoring and organization works in real-time. The application creates category directories automatically and monitors for file system events.

### Security Testing
```bash
# Run security-specific tests (takes ~5 seconds)
pytest tests/security/ -v

# Run security scanning
bandit -r orchestrator/ -f txt
safety check
```

## Common Tasks

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
- **CI failures**: Always run `black`, `isort`, `flake8`, and `pytest` before committing

### Time Expectations
- **Setup verification**: ~1 second
- **Dependency installation**: ~30 seconds
- **Basic tests**: ~0.4 seconds (7 tests)
- **Unit tests**: ~8.5 seconds (33 tests)  
- **Full test suite**: ~36 seconds (63 tests)
- **Code formatting**: ~0.6 seconds
- **Linting checks**: ~0.4 seconds
- **Type checking**: ~0.6 seconds
- **Application startup**: ~0.2 seconds

NEVER CANCEL any build or test commands. All operations complete in under 1 minute.