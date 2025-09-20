"""
File classification module for SecureDownloadsOrchestrator 2.0

Provides file classification functionality using file extensions, magic numbers,
and optionally OpenAI GPT for intelligent content analysis and categorization.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from orchestrator.file_type_detector import FileTypeDetector

# Optional OpenAI import - gracefully handle if not available
try:
    import openai

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class FileClassifier:
    """File classifier that uses both file extensions and MIME types for accurate classification.

    Optionally supports OpenAI GPT-powered classification for enhanced accuracy and
    metadata extraction when configured.
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the file classifier.

        Args:
            logger: Optional logger instance
            config: Optional configuration dictionary containing ai_classification settings
        """
        self.logger = logger or logging.getLogger(__name__)
        self.file_detector = FileTypeDetector()
        self.config = config or {}

        # Initialize AI classification if configured and available
        self.ai_config = self.config.get("ai_classification", {})
        self.ai_enabled = self._initialize_ai_classification()

        # Define classification mappings based on file extensions
        self.extension_map = {
            # Documents
            ".pdf": "pdf",
            ".doc": "document",
            ".docx": "document",
            ".txt": "document",
            ".rtf": "document",
            ".odt": "document",
            ".pages": "document",
            # Spreadsheets
            ".xls": "spreadsheet",
            ".xlsx": "spreadsheet",
            ".csv": "spreadsheet",
            ".ods": "spreadsheet",
            ".numbers": "spreadsheet",
            # Presentations
            ".ppt": "presentation",
            ".pptx": "presentation",
            ".odp": "presentation",
            ".key": "presentation",
            # Images
            ".jpg": "image",
            ".jpeg": "image",
            ".png": "image",
            ".gif": "image",
            ".bmp": "image",
            ".tiff": "image",
            ".tif": "image",
            ".svg": "image",
            ".webp": "image",
            ".ico": "image",
            ".heic": "image",
            ".raw": "image",
            # Audio
            ".mp3": "audio",
            ".wav": "audio",
            ".flac": "audio",
            ".aac": "audio",
            ".ogg": "audio",
            ".wma": "audio",
            ".m4a": "audio",
            # Video
            ".mp4": "video",
            ".avi": "video",
            ".mkv": "video",
            ".mov": "video",
            ".wmv": "video",
            ".flv": "video",
            ".webm": "video",
            ".m4v": "video",
            ".3gp": "video",
            # Archives
            ".zip": "archive",
            ".rar": "archive",
            ".7z": "archive",
            ".tar": "archive",
            ".gz": "archive",
            ".bz2": "archive",
            ".xz": "archive",
            ".tar.gz": "archive",
            ".tar.bz2": "archive",
            ".tar.xz": "archive",
            # Executables
            ".exe": "executable",
            ".msi": "executable",
            ".dmg": "executable",
            ".pkg": "executable",
            ".deb": "executable",
            ".rpm": "executable",
            ".appimage": "executable",
            # Code/Development
            ".py": "code",
            ".js": "code",
            ".html": "code",
            ".css": "code",
            ".java": "code",
            ".cpp": "code",
            ".c": "code",
            ".h": "code",
            ".php": "code",
            ".rb": "code",
            ".go": "code",
            ".rs": "code",
            ".swift": "code",
            ".kt": "code",
            ".json": "code",
            ".xml": "code",
            ".yaml": "code",
            ".yml": "code",
        }

        # MIME type mappings for magic number detection
        self.mime_type_map = {
            # Documents
            "application/pdf": "pdf",
            "application/msword": "document",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document",
            "text/plain": "document",
            "application/rtf": "document",
            # Spreadsheets
            "application/vnd.ms-excel": "spreadsheet",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "spreadsheet",
            "text/csv": "spreadsheet",
            # Presentations
            "application/vnd.ms-powerpoint": "presentation",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "presentation",
            # Images
            "image/jpeg": "image",
            "image/png": "image",
            "image/gif": "image",
            "image/bmp": "image",
            "image/tiff": "image",
            "image/svg+xml": "image",
            "image/webp": "image",
            "image/x-icon": "image",
            # Audio
            "audio/mpeg": "audio",
            "audio/wav": "audio",
            "audio/flac": "audio",
            "audio/aac": "audio",
            "audio/ogg": "audio",
            # Video
            "video/mp4": "video",
            "video/x-msvideo": "video",
            "video/x-matroska": "video",
            "video/quicktime": "video",
            "video/webm": "video",
            # Archives
            "application/zip": "archive",
            "application/x-rar-compressed": "archive",
            "application/x-7z-compressed": "archive",
            "application/x-tar": "archive",
            "application/gzip": "archive",
            "application/x-bzip2": "archive",
            # Executables
            "application/x-msdownload": "executable",
            "application/x-msi": "executable",
            "application/x-apple-diskimage": "executable",
            "application/vnd.debian.binary-package": "executable",
            # Code
            "text/x-python": "code",
            "application/javascript": "code",
            "text/html": "code",
            "text/css": "code",
            "application/json": "code",
            "application/xml": "code",
            "text/xml": "code",
        }

    def _initialize_ai_classification(self) -> bool:
        """Initialize AI classification if configured and available.

        Returns:
            bool: True if AI classification is available and configured, False otherwise
        """
        if not HAS_OPENAI:
            if self.ai_config.get("enabled", False):
                self.logger.warning(
                    "AI classification is enabled in config but OpenAI package is not installed. "
                    "Install with: pip install openai>=1.0.0"
                )
            return False

        if not self.ai_config.get("enabled", False):
            return False

        # Check for API key in environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.logger.warning(
                "AI classification is enabled but OPENAI_API_KEY environment variable is not set. "
                "Set OPENAI_API_KEY to enable GPT-powered classification."
            )
            return False

        try:
            # Initialize OpenAI client
            self.openai_client = openai.OpenAI(api_key=api_key)
            self.logger.info("AI classification initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize AI classification: {e}")
            return False

    def _is_text_file(
        self, filepath: str, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if a file is a text file suitable for GPT analysis.

        Args:
            filepath: Path to the file
            metadata: Optional file metadata from file type detector

        Returns:
            bool: True if file is suitable for GPT analysis, False otherwise
        """
        if not metadata:
            metadata = self.file_detector.detect_type_and_metadata(filepath)

        if not metadata:
            return False

        mime_type = metadata.get("mime_type", "")
        supported_types = self.ai_config.get("supported_mime_types", [])

        return mime_type in supported_types

    def _read_file_content(self, filepath: str) -> Optional[str]:
        """Safely read file content for GPT analysis.

        Args:
            filepath: Path to the file to read

        Returns:
            str: File content truncated to max_content_length, or None if reading fails
        """
        try:
            # Check file size limit
            file_size = os.path.getsize(filepath)
            max_size = self.ai_config.get("max_file_size_bytes", 1048576)  # 1MB default

            if file_size > max_size:
                self.logger.warning(
                    f"File {filepath} ({file_size} bytes) exceeds maximum size "
                    f"for GPT analysis ({max_size} bytes)"
                )
                return None

            # Read file content
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Truncate if necessary
            max_length = self.ai_config.get("max_content_length", 8000)
            if len(content) > max_length:
                content = content[:max_length]
                self.logger.debug(f"File content truncated to {max_length} characters")

            return content

        except Exception as e:
            self.logger.error(f"Failed to read file content from {filepath}: {e}")
            return None

    def _classify_with_gpt(
        self, filepath: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Classify file using OpenAI GPT.

        Args:
            filepath: Path to the file to classify
            metadata: Optional file metadata from file type detector

        Returns:
            dict: GPT classification result with category, summary, metadata, etc., or None if failed
        """
        if not self.ai_enabled:
            return None

        try:
            # Get file information
            file_path = Path(filepath)
            filename = file_path.name
            file_extension = file_path.suffix.lower()
            file_size = os.path.getsize(filepath)

            if not metadata:
                metadata = self.file_detector.detect_type_and_metadata(filepath)

            mime_type = metadata.get("mime_type", "unknown") if metadata else "unknown"

            # Check if file is suitable for GPT analysis
            if not self._is_text_file(filepath, metadata):
                self.logger.debug(
                    f"File {filepath} is not suitable for GPT analysis (MIME type: {mime_type})"
                )
                return None

            # Read file content
            file_content = self._read_file_content(filepath)
            if file_content is None:
                return None

            # Prepare prompt using template
            prompt_template = self.ai_config.get("prompt_template", "")
            max_content_length = self.ai_config.get("max_content_length", 8000)

            prompt = prompt_template.format(
                filename=filename,
                file_extension=file_extension,
                mime_type=mime_type,
                file_size=file_size,
                file_content=file_content,
                max_content_length=max_content_length,
            )

            # Log prompt if configured
            if self.ai_config.get("log_prompts", False):
                self.logger.debug(f"GPT prompt for {filepath}:\n{prompt}")

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model=self.ai_config.get("model", "gpt-3.5-turbo"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.ai_config.get("max_tokens", 1000),
                temperature=self.ai_config.get("temperature", 0.1),
                response_format={"type": "json_object"},
            )

            # Extract response content
            response_content = response.choices[0].message.content

            # Log response if configured
            if self.ai_config.get("log_responses", False):
                self.logger.debug(f"GPT response for {filepath}:\n{response_content}")

            # Parse JSON response
            try:
                classification_result = json.loads(response_content)

                # Validate required fields
                required_fields = ["category", "confidence_score"]
                for field in required_fields:
                    if field not in classification_result:
                        self.logger.warning(
                            f"GPT response missing required field '{field}' for {filepath}"
                        )
                        return None

                # Add metadata
                classification_result["source"] = "gpt"
                classification_result["model"] = self.ai_config.get(
                    "model", "gpt-3.5-turbo"
                )
                classification_result["filepath"] = filepath

                self.logger.info(
                    f"GPT classified {filepath} as '{classification_result.get('category')}' "
                    f"with confidence {classification_result.get('confidence_score', 0):.2f}"
                )

                return classification_result

            except json.JSONDecodeError as e:
                self.logger.error(
                    f"Failed to parse GPT response as JSON for {filepath}: {e}"
                )
                if self.ai_config.get("log_errors", True):
                    self.logger.error(f"Raw GPT response: {response_content}")
                return None

        except Exception as e:
            if self.ai_config.get("log_errors", True):
                self.logger.error(f"GPT classification failed for {filepath}: {e}")
            return None

    def classify_file(self, filepath: str) -> Union[str, Dict[str, Any]]:
        """
        Classify a file based on its extension, magic numbers, and optionally GPT analysis.

        Args:
            filepath: Path to the file to classify

        Returns:
            Union[str, Dict[str, Any]]: If AI classification is disabled or fails, returns
            a string category. If AI classification succeeds, returns a detailed dictionary
            with classification results, summary, metadata, etc.
        """
        if not os.path.isfile(filepath):
            self.logger.warning(f"Cannot classify non-existent file: {filepath}")
            return "unknown"

        try:
            # Get file extension and metadata
            file_path = Path(filepath)
            extension = file_path.suffix.lower()

            # Handle compound extensions like .tar.gz
            if extension in [".gz", ".bz2", ".xz"] and len(file_path.suffixes) > 1:
                compound_ext = "".join(file_path.suffixes[-2:]).lower()
                if compound_ext in self.extension_map:
                    extension = compound_ext

            # Get MIME type using magic numbers
            metadata = self.file_detector.detect_type_and_metadata(filepath)

            # Try GPT classification first if enabled
            if self.ai_enabled:
                gpt_result = self._classify_with_gpt(filepath, metadata)
                if gpt_result:
                    # GPT classification successful - enrich with rule-based classification
                    rule_based_category = self._get_rule_based_category(
                        extension, metadata
                    )
                    gpt_result["rule_based_category"] = rule_based_category
                    return gpt_result

            # Fallback to rule-based classification
            fallback_enabled = self.ai_config.get("fallback_to_rule_based", True)
            if not self.ai_enabled or fallback_enabled:
                category = self._get_rule_based_category(extension, metadata)

                # Log the classification result
                mime_type = (
                    metadata.get("mime_type", "unknown") if metadata else "unknown"
                )
                self.logger.info(
                    f"File classified (rule-based): {filepath} -> {category} "
                    f"(ext: {extension}, mime: {mime_type})"
                )

                return category
            else:
                self.logger.warning(
                    f"AI classification failed and fallback is disabled for {filepath}"
                )
                return "unknown"

        except Exception as e:
            self.logger.error(f"Error classifying file {filepath}: {e}")
            return "unknown"

    def _get_rule_based_category(
        self, extension: str, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get rule-based classification using extension and MIME type.

        Args:
            extension: File extension (e.g., '.py')
            metadata: Optional file metadata containing MIME type

        Returns:
            str: File category
        """
        # First try classification by extension
        extension_category = self.extension_map.get(extension)

        # Get MIME category
        mime_category = None
        if metadata and metadata.get("mime_type"):
            mime_type = metadata["mime_type"]
            mime_category = self.mime_type_map.get(mime_type)

        # Determine final category with improved logic
        final_category = "unknown"

        # Special case: if extension is unknown and MIME type is generic, classify as unknown
        if (
            not extension_category
            and metadata
            and metadata.get("mime_type")
            in [
                "text/plain",
                "application/octet-stream",
            ]
        ):
            final_category = "unknown"
        # For specific MIME types that are clearly identifiable, prefer MIME type
        elif (
            mime_category
            and metadata
            and metadata.get("mime_type")
            not in [
                "text/plain",
                "application/octet-stream",
            ]
        ):
            final_category = mime_category
        # For generic MIME types or when MIME detection fails, prefer extension
        elif extension_category:
            final_category = extension_category
        # Fallback to MIME category if extension didn't match
        elif mime_category:
            final_category = mime_category

        return final_category


def classify_file(
    filepath: str,
    logger: Optional[logging.Logger] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Union[str, Dict[str, Any]]:
    """
    Convenience function to classify a file without creating a classifier instance.

    Args:
        filepath: Path to the file to classify
        logger: Optional logger instance
        config: Optional configuration dictionary containing ai_classification settings

    Returns:
        Union[str, Dict[str, Any]]: If AI classification is disabled or fails, returns
        a string category. If AI classification succeeds, returns a detailed dictionary
        with classification results, summary, metadata, etc.
    """
    classifier = FileClassifier(logger, config)
    return classifier.classify_file(filepath)
