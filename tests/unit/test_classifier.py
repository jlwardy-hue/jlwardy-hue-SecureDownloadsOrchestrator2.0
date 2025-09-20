"""
Unit tests for file classifier module.
"""

import tempfile
from pathlib import Path

import pytest

from orchestrator.classifier import FileClassifier, classify_file


class TestFileClassifier:

    def test_classifier_initialization(self):
        """Test FileClassifier initialization."""
        classifier = FileClassifier()

        assert classifier is not None
        assert hasattr(classifier, "extension_map")
        assert hasattr(classifier, "mime_type_map")
        assert hasattr(classifier, "file_detector")

    def test_classify_pdf_file(self, sample_files):
        """Test classification of PDF file."""
        pdf_file = sample_files["document.pdf"]
        category = classify_file(pdf_file)

        # Should classify as document or pdf based on extension
        assert category in ["pdf", "document"]

    def test_classify_image_file(self, sample_files):
        """Test classification of image file."""
        jpg_file = sample_files["image.jpg"]
        category = classify_file(jpg_file)

        # Should classify as image
        assert category == "image"

    def test_classify_code_file(self, sample_files):
        """Test classification of code file."""
        py_file = sample_files["script.py"]
        category = classify_file(py_file)

        # Should classify as code
        assert category == "code"

    def test_classify_unknown_file(self, sample_files):
        """Test classification of unknown file type."""
        unknown_file = sample_files["unknown.xyz"]
        category = classify_file(unknown_file)

        # Should classify as unknown
        assert category == "unknown"

    def test_classify_nonexistent_file(self):
        """Test classification of non-existent file."""
        category = classify_file("/nonexistent/file.txt")

        # Should handle gracefully and return unknown
        assert category == "unknown"

    def test_extension_mapping(self):
        """Test that extension mapping contains expected entries."""
        classifier = FileClassifier()

        # Test some key extensions
        assert ".pdf" in classifier.extension_map
        assert ".jpg" in classifier.extension_map
        assert ".py" in classifier.extension_map
        assert ".mp4" in classifier.extension_map
        assert ".zip" in classifier.extension_map

    def test_mime_type_mapping(self):
        """Test that MIME type mapping contains expected entries."""
        classifier = FileClassifier()

        # Test some key MIME types
        assert "application/pdf" in classifier.mime_type_map
        assert "image/jpeg" in classifier.mime_type_map
        assert "text/x-python" in classifier.mime_type_map
