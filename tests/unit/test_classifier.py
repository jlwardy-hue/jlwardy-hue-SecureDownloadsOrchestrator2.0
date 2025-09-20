"""
Unit tests for file classifier module.
"""

from pathlib import Path
from unittest.mock import Mock, patch
import pytest
import tempfile

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


class TestAIClassification:
    """Test AI-powered file classification."""

    def test_ai_classification_disabled_by_default(self):
        """Test that AI classification is disabled by default."""
        classifier = FileClassifier()
        assert not classifier._ai_enabled

    def test_ai_classification_enabled_with_config(self):
        """Test that AI classification can be enabled via config."""
        config = {
            "processing": {"enable_ai_classification": True},
            "ai_classification": {"provider": "openai"},
        }

        # Mock environment variable
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as mock_openai:
                classifier = FileClassifier(config)
                assert classifier._ai_enabled
                mock_openai.assert_called_once()

    def test_ai_classification_disabled_without_api_key(self):
        """Test that AI classification is disabled without API key."""
        config = {
            "processing": {"enable_ai_classification": True},
            "ai_classification": {"provider": "openai"},
        }

        # Ensure no API key in environment
        with patch.dict("os.environ", {}, clear=True):
            classifier = FileClassifier(config)
            assert not classifier._ai_enabled

    def test_is_text_file_by_mime_type(self):
        """Test text file detection by MIME type."""
        classifier = FileClassifier()

        assert classifier._is_text_file("/test/file.txt", "text/plain")
        assert classifier._is_text_file("/test/file.py", "text/x-python")
        assert classifier._is_text_file("/test/file.json", "application/json")
        assert not classifier._is_text_file("/test/file.jpg", "image/jpeg")

    def test_is_text_file_by_extension(self):
        """Test text file detection by extension."""
        classifier = FileClassifier()

        assert classifier._is_text_file("/test/file.txt")
        assert classifier._is_text_file("/test/file.py")
        assert classifier._is_text_file("/test/file.js")
        assert not classifier._is_text_file("/test/file.jpg")

    def test_read_file_content(self, sample_files):
        """Test reading file content for AI classification."""
        config = {"ai_classification": {"max_content_length": 100}}
        classifier = FileClassifier(config)

        # Test reading Python file
        py_file = sample_files["script.py"]
        content = classifier._read_file_content(py_file)
        assert content is not None
        assert "hello" in content

    def test_read_file_content_max_length(self, temp_directories):
        """Test that file content reading respects max length."""
        config = {"ai_classification": {"max_content_length": 10}}
        classifier = FileClassifier(config)

        # Create a large text file
        large_file = Path(temp_directories["source"]) / "large.txt"
        large_file.write_text("A" * 100)

        content = classifier._read_file_content(str(large_file))
        assert content is not None
        assert len(content) == 10

    @patch("openai.OpenAI")
    def test_classify_with_ai_success(self, mock_openai_class, sample_files):
        """Test successful AI classification."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "code"
        mock_client.chat.completions.create.return_value = mock_response

        config = {
            "processing": {"enable_ai_classification": True},
            "ai_classification": {"provider": "openai", "model": "gpt-3.5-turbo"},
        }

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            classifier = FileClassifier(config)

            result = classifier._classify_with_ai(
                sample_files["script.py"], "print('hello')"
            )
            assert result == "code"

    @patch("openai.OpenAI")
    def test_classify_with_ai_invalid_response(self, mock_openai_class, sample_files):
        """Test AI classification with invalid response."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "invalid_category"
        mock_client.chat.completions.create.return_value = mock_response

        config = {
            "processing": {"enable_ai_classification": True},
            "ai_classification": {"provider": "openai"},
        }

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            classifier = FileClassifier(config)

            result = classifier._classify_with_ai(
                sample_files["script.py"], "print('hello')"
            )
            assert result is None

    @patch("openai.OpenAI")
    def test_classify_with_ai_api_error(self, mock_openai_class, sample_files):
        """Test AI classification with API error."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        config = {
            "processing": {"enable_ai_classification": True},
            "ai_classification": {"provider": "openai"},
        }

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            classifier = FileClassifier(config)

            result = classifier._classify_with_ai(
                sample_files["script.py"], "print('hello')"
            )
            assert result is None

    @patch("openai.OpenAI")
    def test_full_classification_with_ai_enabled(self, mock_openai_class, sample_files):
        """Test full file classification with AI enabled."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "document"  # AI says it's a document
        mock_client.chat.completions.create.return_value = mock_response

        config = {
            "processing": {"enable_ai_classification": True},
            "ai_classification": {"provider": "openai"},
        }

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            classifier = FileClassifier(config)

            # Classify Python file - traditional would be "code", AI says "document"
            result = classifier.classify_file(sample_files["script.py"])
            assert result == "document"  # AI override should be used

    @patch("openai.OpenAI")
    def test_ai_classification_fallback_on_failure(
        self, mock_openai_class, sample_files
    ):
        """Test that traditional classification is used when AI fails."""
        # Setup mock to fail
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        config = {
            "processing": {"enable_ai_classification": True},
            "ai_classification": {"provider": "openai"},
        }

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            classifier = FileClassifier(config)

            # Should fall back to traditional classification
            result = classifier.classify_file(sample_files["script.py"])
            assert result == "code"  # Traditional classification

    def test_convenience_function_with_config(self, sample_files):
        """Test the convenience function with AI config."""
        config = {
            "processing": {"enable_ai_classification": False},
        }

        result = classify_file(sample_files["script.py"], config)
        assert result == "code"
