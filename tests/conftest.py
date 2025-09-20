# Test configuration for SecureDownloadsOrchestrator 2.0

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_directories():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        source_dir = Path(temp_dir) / "source"
        dest_dir = Path(temp_dir) / "destination"
        source_dir.mkdir()
        dest_dir.mkdir()

        yield {
            "temp_dir": temp_dir,
            "source": str(source_dir),
            "destination": str(dest_dir),
        }


@pytest.fixture
def test_config(temp_directories):
    """Create a test configuration."""
    return {
        "directories": {
            "source": temp_directories["source"],
            "destination": temp_directories["destination"],
        },
        "categories": {
            "documents": {"extensions": [".pdf", ".txt"], "destination": "documents"},
            "images": {"extensions": [".jpg", ".png"], "destination": "images"},
        },
        "logging": {
            "console": {"enabled": True, "level": "INFO"},
            "file": {"enabled": False},
        },
        "application": {
            "name": "SecureDownloadsOrchestrator",
            "version": "2.0",
            "startup": {"validate_config": True, "create_missing_dirs": True},
        },
        "processing": {
            "enable_ai_classification": False,
            "enable_security_scan": False,
        },
    }


@pytest.fixture
def sample_files(temp_directories):
    """Create sample files for testing."""
    source_dir = Path(temp_directories["source"])

    # Create test files
    test_files = {
        "document.pdf": b"fake pdf content",
        "image.jpg": b"fake jpg content",
        "script.py": b"print('hello world')",
        "unknown.xyz": b"unknown file type",
    }

    created_files = {}
    for filename, content in test_files.items():
        file_path = source_dir / filename
        file_path.write_bytes(content)
        created_files[filename] = str(file_path)

    return created_files
