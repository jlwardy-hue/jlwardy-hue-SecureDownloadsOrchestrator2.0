"""
Unit tests for GPT classification functionality in the classifier module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from orchestrator.classifier import FileClassifier
from orchestrator.config_loader import get_ai_classification_config


class TestGPTClassification:
    """Test GPT classification functionality."""

    @pytest.fixture
    def ai_config(self):
        """GPT-enabled configuration for testing."""
        return {
            "ai_classification": {
                "enabled": True,
                "model": "gpt-3.5-turbo",
                "max_tokens": 1000,
                "temperature": 0.1,
                "max_file_size_bytes": 1048576,
                "max_content_length": 8000,
                "supported_mime_types": [
                    "text/plain",
                    "text/x-python",
                    "application/json",
                ],
                "fallback_to_rule_based": True,
                "log_prompts": False,
                "log_responses": False,
                "log_errors": True,
                "prompt_template": "Analyze this file: {filename}\nContent: {file_content}\nRespond with JSON.",
            }
        }

    @pytest.fixture
    def sample_python_file(self):
        """Create a temporary Python file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('Hello, World!')\n# This is a test Python script")
            f.flush()
            yield f.name
        os.unlink(f.name)

    @pytest.fixture
    def sample_large_file(self):
        """Create a large file that exceeds size limits."""
        content = "x" * 2000000  # 2MB of content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()
            yield f.name
        os.unlink(f.name)

    def test_ai_classification_disabled_by_default(self):
        """Test that AI classification is disabled by default."""
        classifier = FileClassifier()
        assert not classifier.ai_enabled

    def test_ai_classification_without_openai_package(self, ai_config):
        """Test AI classification when OpenAI package is not available."""
        with patch("orchestrator.classifier.HAS_OPENAI", False):
            classifier = FileClassifier(config=ai_config)
            assert not classifier.ai_enabled

    @patch.dict(os.environ, {}, clear=True)
    def test_ai_classification_without_api_key(self, ai_config):
        """Test AI classification when API key is not set."""
        classifier = FileClassifier(config=ai_config)
        assert not classifier.ai_enabled

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("orchestrator.classifier.openai.OpenAI")
    def test_ai_classification_initialization_success(self, mock_openai, ai_config):
        """Test successful AI classification initialization."""
        mock_client = Mock()
        mock_openai.return_value = mock_client

        classifier = FileClassifier(config=ai_config)
        assert classifier.ai_enabled
        assert classifier.openai_client == mock_client

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("orchestrator.classifier.openai.OpenAI")
    def test_ai_classification_initialization_failure(self, mock_openai, ai_config):
        """Test AI classification initialization failure."""
        mock_openai.side_effect = Exception("API connection failed")

        classifier = FileClassifier(config=ai_config)
        assert not classifier.ai_enabled

    def test_is_text_file_with_supported_mime_type(self, ai_config, sample_python_file):
        """Test text file detection with supported MIME type."""
        classifier = FileClassifier(config=ai_config)

        # Mock file type detector to return Python MIME type
        with patch.object(
            classifier.file_detector, "detect_type_and_metadata"
        ) as mock_detect:
            mock_detect.return_value = {"mime_type": "text/x-python"}

            assert classifier._is_text_file(sample_python_file)

    def test_is_text_file_with_unsupported_mime_type(
        self, ai_config, sample_python_file
    ):
        """Test text file detection with unsupported MIME type."""
        classifier = FileClassifier(config=ai_config)

        # Mock file type detector to return unsupported MIME type
        with patch.object(
            classifier.file_detector, "detect_type_and_metadata"
        ) as mock_detect:
            mock_detect.return_value = {"mime_type": "image/jpeg"}

            assert not classifier._is_text_file(sample_python_file)

    def test_read_file_content_success(self, ai_config, sample_python_file):
        """Test successful file content reading."""
        classifier = FileClassifier(config=ai_config)
        content = classifier._read_file_content(sample_python_file)

        assert content is not None
        assert "Hello, World!" in content
        assert "test Python script" in content

    def test_read_file_content_size_limit(self, ai_config, sample_large_file):
        """Test file content reading with size limit."""
        classifier = FileClassifier(config=ai_config)
        content = classifier._read_file_content(sample_large_file)

        # Should return None due to size limit
        assert content is None

    def test_read_file_content_truncation(self, ai_config):
        """Test file content truncation."""
        # Create config with small content limit
        ai_config["ai_classification"]["max_content_length"] = 10

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a very long content that should be truncated")
            f.flush()

            classifier = FileClassifier(config=ai_config)
            content = classifier._read_file_content(f.name)

            assert content is not None
            assert len(content) == 10
            assert content == "This is a "

        os.unlink(f.name)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("orchestrator.classifier.openai.OpenAI")
    def test_gpt_classification_success(
        self, mock_openai, ai_config, sample_python_file
    ):
        """Test successful GPT classification."""
        # Mock OpenAI client and response
        mock_client = Mock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "category": "code",
                "subcategory": "python_script",
                "programming_language": "python",
                "summary": "A simple Python script that prints 'Hello, World!'",
                "confidence_score": 0.95,
                "metadata": {"functions": [], "imports": []},
            }
        )

        mock_client.chat.completions.create.return_value = mock_response

        # Mock file type detector
        classifier = FileClassifier(config=ai_config)
        with patch.object(
            classifier.file_detector, "detect_type_and_metadata"
        ) as mock_detect:
            mock_detect.return_value = {"mime_type": "text/x-python"}

            result = classifier._classify_with_gpt(sample_python_file)

            assert result is not None
            assert result["category"] == "code"
            assert result["subcategory"] == "python_script"
            assert result["programming_language"] == "python"
            assert result["confidence_score"] == 0.95
            assert result["source"] == "gpt"
            assert "filepath" in result

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("orchestrator.classifier.openai.OpenAI")
    def test_gpt_classification_invalid_json(
        self, mock_openai, ai_config, sample_python_file
    ):
        """Test GPT classification with invalid JSON response."""
        # Mock OpenAI client and invalid response
        mock_client = Mock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is not valid JSON"

        mock_client.chat.completions.create.return_value = mock_response

        classifier = FileClassifier(config=ai_config)
        with patch.object(
            classifier.file_detector, "detect_type_and_metadata"
        ) as mock_detect:
            mock_detect.return_value = {"mime_type": "text/x-python"}

            result = classifier._classify_with_gpt(sample_python_file)

            assert result is None

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("orchestrator.classifier.openai.OpenAI")
    def test_gpt_classification_missing_required_fields(
        self, mock_openai, ai_config, sample_python_file
    ):
        """Test GPT classification with missing required fields."""
        # Mock OpenAI client and incomplete response
        mock_client = Mock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "category": "code",
                # Missing confidence_score
            }
        )

        mock_client.chat.completions.create.return_value = mock_response

        classifier = FileClassifier(config=ai_config)
        with patch.object(
            classifier.file_detector, "detect_type_and_metadata"
        ) as mock_detect:
            mock_detect.return_value = {"mime_type": "text/x-python"}

            result = classifier._classify_with_gpt(sample_python_file)

            assert result is None

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("orchestrator.classifier.openai.OpenAI")
    def test_classify_file_with_gpt_enabled(
        self, mock_openai, ai_config, sample_python_file
    ):
        """Test complete file classification with GPT enabled."""
        # Mock OpenAI client and response
        mock_client = Mock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "category": "code",
                "subcategory": "python_script",
                "programming_language": "python",
                "summary": "A simple Python script",
                "confidence_score": 0.95,
            }
        )

        mock_client.chat.completions.create.return_value = mock_response

        classifier = FileClassifier(config=ai_config)
        with patch.object(
            classifier.file_detector, "detect_type_and_metadata"
        ) as mock_detect:
            mock_detect.return_value = {"mime_type": "text/x-python"}

            result = classifier.classify_file(sample_python_file)

            # Should return GPT result (dict) instead of rule-based result (string)
            assert isinstance(result, dict)
            assert result["category"] == "code"
            assert result["source"] == "gpt"
            assert "rule_based_category" in result

    def test_classify_file_gpt_disabled_fallback(self, sample_python_file):
        """Test file classification with GPT disabled, falling back to rule-based."""
        # Default config has AI disabled
        classifier = FileClassifier()
        result = classifier.classify_file(sample_python_file)

        # Should return rule-based result (string)
        assert isinstance(result, str)
        assert result == "code"

    def test_get_ai_classification_config_defaults(self):
        """Test AI configuration helper with defaults."""
        config = {}
        ai_config = get_ai_classification_config(config)

        assert ai_config["enabled"] is False
        assert ai_config["model"] == "gpt-3.5-turbo"
        assert ai_config["max_tokens"] == 1000
        assert ai_config["temperature"] == 0.1
        assert ai_config["fallback_to_rule_based"] is True
        assert "prompt_template" in ai_config

    def test_get_ai_classification_config_custom(self):
        """Test AI configuration helper with custom values."""
        config = {
            "ai_classification": {
                "enabled": True,
                "model": "gpt-4",
                "max_tokens": 2000,
            }
        }

        ai_config = get_ai_classification_config(config)

        assert ai_config["enabled"] is True
        assert ai_config["model"] == "gpt-4"
        assert ai_config["max_tokens"] == 2000
        # Should still have defaults for unspecified values
        assert ai_config["temperature"] == 0.1
