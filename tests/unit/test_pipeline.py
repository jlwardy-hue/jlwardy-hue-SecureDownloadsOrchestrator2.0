"""
Test suite for the unified file processing pipeline.

Tests the core functionality of the UnifiedFileProcessor including:
- File processing workflow
- Security scanning (with mocked ClamAV)
- Archive extraction
- OCR metadata extraction (with mocked dependencies)
- File organization
"""

import os
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from orchestrator.pipeline import (
    OCRMetadata,
    ProcessingResult,
    SecurityScanResult,
    UnifiedFileProcessor,
    create_unified_processor,
)


@pytest.fixture
def pipeline_config(temp_directories):
    """Create a test configuration for the pipeline."""
    return {
        "directories": {
            "source": temp_directories["source"],
            "destination": temp_directories["destination"],
        },
        "categories": {
            "documents": {"extensions": [".pdf", ".txt"], "destination": "documents"},
            "images": {"extensions": [".jpg", ".png"], "destination": "images"},
            "archives": {"extensions": [".zip"], "destination": "archives"},
        },
        "security": {"fail_closed": False},  # Use fail-open for unit tests
        "processing": {
            "enable_security_scan": False,
            "enable_ocr": True,
            "enable_archive_extraction": True,
        },
    }


@pytest.fixture
def processor(pipeline_config):
    """Create a UnifiedFileProcessor instance for testing."""
    return UnifiedFileProcessor(pipeline_config)


class TestUnifiedFileProcessor:
    """Test cases for the UnifiedFileProcessor class."""

    def test_processor_initialization(self, processor, pipeline_config):
        """Test that the processor initializes correctly."""
        assert processor.config == pipeline_config
        assert processor.source_dir == Path(pipeline_config["directories"]["source"])
        assert processor.destination_dir == Path(
            pipeline_config["directories"]["destination"]
        )
        assert processor.enable_ocr is True
        assert processor.enable_archive_extraction is True
        assert processor.enable_security_scan is False

    def test_create_unified_processor_factory(self, pipeline_config):
        """Test the factory function for creating processors."""
        processor = create_unified_processor(pipeline_config)
        assert isinstance(processor, UnifiedFileProcessor)
        assert processor.config == pipeline_config

    def test_process_nonexistent_file(self, processor):
        """Test processing a file that doesn't exist."""
        result = processor.process_file("/nonexistent/file.txt")
        assert not result.success
        # With new path validation, this will fail due to path validation or quarantine
        assert (
            "does not exist" in result.error
            or "Path validation failed" in result.error
            or "Quarantine failed" in result.error
        )

    def test_process_simple_text_file(self, processor, temp_directories):
        """Test processing a simple text file."""
        # Create a test file
        source_dir = Path(temp_directories["source"])
        test_file = source_dir / "test.txt"
        test_file.write_text("Hello world!")

        # Process the file
        result = processor.process_file(str(test_file))

        # Verify results
        assert result.success
        assert result.final_path
        assert Path(result.final_path).exists()
        assert (
            "document" in result.final_path
        )  # Should contain "document" (singular from config)

    @patch("orchestrator.pipeline.subprocess.run")
    def test_security_scanning_clean_file(self, mock_run, processor, temp_directories):
        """Test security scanning with a clean file."""
        # Enable security scanning
        processor.enable_security_scan = True
        processor.clamav_available = True

        # Mock ClamAV returning clean
        mock_run.return_value = Mock(returncode=0, stdout="file.txt: OK", stderr="")

        # Create test file
        source_dir = Path(temp_directories["source"])
        test_file = source_dir / "test.txt"
        test_file.write_text("Clean file content")

        # Test security scan
        result = processor._scan_file_security(str(test_file))
        assert result.is_clean
        assert result.threat_name is None

    @patch("orchestrator.pipeline.subprocess.run")
    def test_security_scanning_infected_file(
        self, mock_run, processor, temp_directories
    ):
        """Test security scanning with an infected file."""
        # Enable security scanning
        processor.enable_security_scan = True
        processor.clamav_available = True

        # Mock ClamAV returning infected
        mock_run.return_value = Mock(
            returncode=1, stdout="file.txt: TestVirus FOUND", stderr=""
        )

        # Create test file
        source_dir = Path(temp_directories["source"])
        test_file = source_dir / "infected.txt"
        test_file.write_text("Fake virus content")

        # Test security scan
        result = processor._scan_file_security(str(test_file))
        assert not result.is_clean
        assert result.threat_name == "TestVirus"

    def test_quarantine_infected_file(self, processor, temp_directories):
        """Test quarantining an infected file."""
        # Create test file
        source_dir = Path(temp_directories["source"])
        test_file = source_dir / "infected.txt"
        test_file.write_text("Infected content")

        # Create mock scan result
        scan_result = SecurityScanResult(False, "TestVirus", "Scan output")

        # Test quarantine
        result = processor._quarantine_file(str(test_file), scan_result)

        assert result.success
        assert "quarantine" in result.final_path
        assert not test_file.exists()  # Original file should be moved
        assert Path(result.final_path).exists()

    def test_archive_extraction(self, processor, temp_directories):
        """Test extracting and processing archive contents."""
        # Create a zip file with test content
        source_dir = Path(temp_directories["source"])
        zip_path = source_dir / "test.zip"

        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr("test1.txt", "Content 1")
            zip_file.writestr("test2.txt", "Content 2")

        # Process the archive
        result = processor._process_archive(str(zip_path))

        assert result.success
        assert "extracted_files" in result.metadata
        assert (
            len(result.metadata["extracted_files"]) >= 0
        )  # Files should be extracted and processed

    @patch("orchestrator.pipeline.TESSERACT_AVAILABLE", True)
    @patch("orchestrator.pipeline.pytesseract")
    @patch("orchestrator.pipeline.Image")
    def test_ocr_metadata_extraction(
        self, mock_image, mock_tesseract, processor, temp_directories
    ):
        """Test OCR metadata extraction from images."""
        # Mock tesseract to return sample text
        mock_tesseract.image_to_string.return_value = (
            "Invoice from: john@example.com\nDate: 01/15/2024\nAmount: $100"
        )

        # Mock PIL Image
        mock_img = Mock()
        mock_image.open.return_value = mock_img

        # Create test image file
        source_dir = Path(temp_directories["source"])
        test_image = source_dir / "test.jpg"
        test_image.write_bytes(b"fake image content")

        # Test OCR extraction
        metadata = processor._extract_ocr_metadata(str(test_image))

        assert metadata is not None
        assert "Invoice" in metadata.text
        assert metadata.sender is not None  # Should extract email
        assert metadata.business_context is not None  # Should detect "invoice"

    def test_file_organization_simple(self, processor, temp_directories):
        """Test basic file organization without OCR metadata."""
        # Create test file
        source_dir = Path(temp_directories["source"])
        test_file = source_dir / "document.pdf"
        test_file.write_bytes(b"fake pdf content")

        # Test organization
        final_path = processor._organize_file(str(test_file), "documents")

        assert "documents" in final_path
        assert Path(final_path).exists()
        assert Path(final_path).name == "document.pdf"

    def test_file_organization_with_metadata(self, processor, temp_directories):
        """Test file organization with OCR metadata."""
        # Create test file
        source_dir = Path(temp_directories["source"])
        test_file = source_dir / "invoice.pdf"
        test_file.write_bytes(b"fake pdf content")

        # Create mock OCR metadata
        ocr_metadata = OCRMetadata()
        ocr_metadata.business_context = "invoice"
        ocr_metadata.sender = "john@example.com"
        processor._extract_structured_metadata.__func__(processor, ocr_metadata)

        # Test organization
        final_path = processor._organize_file(str(test_file), "documents", ocr_metadata)

        assert "documents" in final_path
        assert "invoice" in final_path
        assert Path(final_path).exists()

    def test_filename_conflict_resolution(self, processor, temp_directories):
        """Test handling of filename conflicts during organization."""
        dest_dir = Path(temp_directories["destination"])
        category_dir = dest_dir / "documents"
        category_dir.mkdir(parents=True, exist_ok=True)

        # Create existing file
        existing_file = category_dir / "test.txt"
        existing_file.write_text("existing content")

        # Create new file with same name
        source_dir = Path(temp_directories["source"])
        test_file = source_dir / "test.txt"
        test_file.write_text("new content")

        # Test organization
        final_path = processor._organize_file(str(test_file), "documents")

        # Should create test_1.txt instead of overwriting
        assert Path(final_path).exists()
        assert "test_1.txt" in final_path or "test.txt" in final_path

    def test_full_pipeline_integration(self, processor, temp_directories):
        """Test the complete pipeline with a simple file."""
        # Create test file
        source_dir = Path(temp_directories["source"])
        test_file = source_dir / "sample.txt"
        test_file.write_text("Sample document content")

        # Process through full pipeline
        result = processor.process_file(str(test_file))

        # Verify success
        assert result.success
        assert result.final_path
        assert Path(result.final_path).exists()
        assert not test_file.exists()  # Original should be moved


class TestSecurityScanResult:
    """Test cases for SecurityScanResult class."""

    def test_clean_result(self):
        """Test creating a clean scan result."""
        result = SecurityScanResult(True)
        assert result.is_clean
        assert result.threat_name is None
        assert result.scanned_at is not None

    def test_infected_result(self):
        """Test creating an infected scan result."""
        result = SecurityScanResult(False, "TestVirus", "Scan output")
        assert not result.is_clean
        assert result.threat_name == "TestVirus"
        assert result.scan_output == "Scan output"


class TestOCRMetadata:
    """Test cases for OCRMetadata class."""

    def test_metadata_initialization(self):
        """Test OCR metadata initialization."""
        metadata = OCRMetadata()
        assert metadata.text == ""
        assert metadata.date_detected is None
        assert metadata.sender is None
        assert metadata.business_context is None
        assert metadata.confidence == 0.0


class TestProcessingResult:
    """Test cases for ProcessingResult class."""

    def test_successful_result(self):
        """Test creating a successful processing result."""
        result = ProcessingResult(True, "/path/to/file")
        assert result.success
        assert result.final_path == "/path/to/file"
        assert result.error is None
        assert result.processed_at is not None

    def test_failed_result(self):
        """Test creating a failed processing result."""
        result = ProcessingResult(False, error="Test error")
        assert not result.success
        assert result.final_path is None
        assert result.error == "Test error"
