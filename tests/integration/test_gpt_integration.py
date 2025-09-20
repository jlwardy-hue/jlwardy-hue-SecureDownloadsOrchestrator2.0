"""
Integration tests for GPT classification functionality.
"""

import json
import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from orchestrator.classifier import classify_file
from orchestrator.config_loader import get_ai_classification_config, load_config


class TestGPTIntegration:
    """Integration tests for GPT classification."""

    @pytest.fixture
    def test_config_file(self):
        """Create a temporary config file with GPT enabled."""
        config_content = """
directories:
  source: "/tmp/test_watch"
  destination: "/tmp/test_dest"

processing:
  enable_ai_classification: true

ai_classification:
  enabled: true
  model: "gpt-3.5-turbo"
  max_tokens: 1000
  temperature: 0.1
  max_file_size_bytes: 1048576
  max_content_length: 8000
  supported_mime_types:
    - "text/plain"
    - "text/x-python"
    - "text/x-script.python"
    - "application/json"
    - "text/javascript"
  fallback_to_rule_based: true
  log_prompts: false
  log_responses: false
  log_errors: true
  prompt_template: |
    Analyze this file: {filename}
    Extension: {file_extension}
    MIME Type: {mime_type}
    Size: {file_size} bytes
    Content: {file_content}
    
    Respond with JSON containing category, confidence_score, and summary.
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            f.flush()
            yield f.name

        os.unlink(f.name)

    @pytest.fixture
    def sample_python_script(self):
        """Create a sample Python script for testing."""
        python_content = '''#!/usr/bin/env python3
"""
A simple Python script for testing GPT classification.
"""

import os
import sys


def main():
    """Main function that prints a greeting."""
    name = input("Enter your name: ")
    print(f"Hello, {name}!")
    
    # Check environment
    python_version = sys.version_info
    print(f"Running Python {python_version.major}.{python_version.minor}")


if __name__ == "__main__":
    main()
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_content)
            f.flush()
            yield f.name

        os.unlink(f.name)

    @pytest.fixture
    def sample_json_config(self):
        """Create a sample JSON config file for testing."""
        json_content = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "myapp",
                "user": "app_user",
            },
            "api": {"base_url": "https://api.example.com", "timeout": 30, "retries": 3},
            "features": {
                "enable_caching": True,
                "enable_logging": True,
                "debug_mode": False,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_content, f, indent=2)
            f.flush()
            yield f.name

        os.unlink(f.name)

    def test_config_loading_with_ai_classification(self, test_config_file):
        """Test loading configuration with AI classification settings."""
        config = load_config(test_config_file)

        # Verify AI classification config is loaded
        assert "ai_classification" in config
        assert config["ai_classification"]["enabled"] is True
        assert config["ai_classification"]["model"] == "gpt-3.5-turbo"

        # Test the helper function
        ai_config = get_ai_classification_config(config)
        assert ai_config["enabled"] is True
        assert "prompt_template" in ai_config

    def test_classify_file_without_gpt_integration(self, sample_python_script):
        """Test file classification without GPT integration (baseline)."""
        # No config provided - should use rule-based classification
        result = classify_file(sample_python_script)

        # Should return string category for rule-based classification
        assert isinstance(result, str)
        assert result == "code"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("orchestrator.classifier.openai.OpenAI")
    def test_classify_file_with_gpt_integration(
        self, mock_openai, test_config_file, sample_python_script
    ):
        """Test complete file classification with GPT integration."""
        # Load configuration
        config = load_config(test_config_file)

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
                "summary": "A Python script with main function that greets users and shows Python version",
                "key_technologies": ["Python", "sys", "os"],
                "sensitive_data_indicators": [],
                "confidence_score": 0.92,
                "metadata": {
                    "has_main_function": True,
                    "imports": ["os", "sys"],
                    "functions": ["main"],
                },
            }
        )

        mock_client.chat.completions.create.return_value = mock_response

        # Classify file with GPT
        result = classify_file(sample_python_script, config=config)

        # Should return detailed dict for GPT classification
        assert isinstance(result, dict)
        assert result["category"] == "code"
        assert result["subcategory"] == "python_script"
        assert result["programming_language"] == "python"
        assert result["confidence_score"] == 0.92
        assert result["source"] == "gpt"
        assert "rule_based_category" in result
        assert "summary" in result
        assert "key_technologies" in result

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("orchestrator.classifier.openai.OpenAI")
    def test_classify_json_file_with_gpt(
        self, mock_openai, test_config_file, sample_json_config
    ):
        """Test GPT classification of a JSON configuration file."""
        # Load configuration
        config = load_config(test_config_file)

        # Mock OpenAI client and response
        mock_client = Mock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "category": "config",
                "subcategory": "application_config",
                "programming_language": None,
                "summary": "Application configuration file with database, API, and feature settings",
                "key_technologies": ["Database", "API", "JSON"],
                "sensitive_data_indicators": ["database_credentials"],
                "confidence_score": 0.88,
                "metadata": {
                    "config_sections": ["database", "api", "features"],
                    "has_sensitive_data": True,
                },
            }
        )

        mock_client.chat.completions.create.return_value = mock_response

        # Classify file with GPT
        result = classify_file(sample_json_config, config=config)

        # Verify GPT classification results
        assert isinstance(result, dict)
        assert result["category"] == "config"
        assert result["subcategory"] == "application_config"
        assert "database_credentials" in result["sensitive_data_indicators"]
        assert result["confidence_score"] == 0.88
        assert result["source"] == "gpt"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("orchestrator.classifier.openai.OpenAI")
    def test_gpt_classification_fallback_on_error(
        self, mock_openai, test_config_file, sample_python_script
    ):
        """Test fallback to rule-based classification when GPT fails."""
        # Load configuration
        config = load_config(test_config_file)

        # Mock OpenAI client to raise an exception
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")

        # Classify file - should fallback to rule-based
        result = classify_file(sample_python_script, config=config)

        # Should fallback to rule-based classification (string result)
        assert isinstance(result, str)
        assert result == "code"

    def test_gpt_classification_with_api_key_missing(
        self, test_config_file, sample_python_script
    ):
        """Test GPT classification when API key is missing."""
        # Ensure no API key in environment
        with patch.dict(os.environ, {}, clear=True):
            config = load_config(test_config_file)

            # Should fallback to rule-based classification
            result = classify_file(sample_python_script, config=config)

            assert isinstance(result, str)
            assert result == "code"

    def test_gpt_disabled_in_config(self, sample_python_script):
        """Test classification when GPT is disabled in config."""
        config = {
            "ai_classification": {"enabled": False, "fallback_to_rule_based": True}
        }

        result = classify_file(sample_python_script, config=config)

        # Should use rule-based classification
        assert isinstance(result, str)
        assert result == "code"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("orchestrator.classifier.openai.OpenAI")
    def test_prompt_template_formatting(
        self, mock_openai, test_config_file, sample_python_script
    ):
        """Test that prompt template is correctly formatted with file information."""
        config = load_config(test_config_file)

        # Mock OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client

        # Create a response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {"category": "code", "confidence_score": 0.9}
        )

        mock_client.chat.completions.create.return_value = mock_response

        # Classify file
        classify_file(sample_python_script, config=config)

        # Verify that GPT was called with formatted prompt
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args

        # Extract the prompt from the call
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        # Verify prompt contains expected file information
        assert "Analyze this file:" in prompt
        assert ".py" in prompt  # file extension
        assert "bytes" in prompt  # file size
        assert "def main" in prompt or "import" in prompt  # file content
