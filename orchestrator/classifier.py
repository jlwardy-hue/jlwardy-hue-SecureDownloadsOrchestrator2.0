"""
File classification module for SecureDownloadsOrchestrator 2.0

Provides file classification functionality using file extensions, magic numbers,
and optional AI-powered classification via OpenAI GPT.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from orchestrator.file_type_detector import FileTypeDetector


class FileClassifier:
    """File classifier that uses both file extensions, MIME types, and optional AI classification."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the file classifier.

        Args:
            config: Configuration dictionary containing AI settings
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.file_detector = FileTypeDetector()
        self.config = config or {}

        # Initialize OpenAI client if AI classification is enabled
        self._openai_client: Optional[Any] = None
        self._ai_enabled = self._should_enable_ai_classification()

        if self._ai_enabled:
            self._initialize_openai_client()

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

    def _should_enable_ai_classification(self) -> bool:
        """Check if AI classification should be enabled based on configuration."""
        try:
            processing_config = self.config.get("processing", {})
            return processing_config.get("enable_ai_classification", False)
        except Exception as e:
            self.logger.warning(f"Error checking AI classification config: {e}")
            return False

    def _initialize_openai_client(self) -> None:
        """Initialize OpenAI client if configuration is valid."""
        try:
            import os

            import openai

            # Check for API key in environment
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                self.logger.warning(
                    "AI classification enabled but OPENAI_API_KEY environment variable not set. "
                    "AI classification will be disabled."
                )
                self._ai_enabled = False
                return

            # Get AI configuration
            ai_config = self.config.get("ai_classification", {})
            endpoint = ai_config.get("endpoint", "https://api.openai.com/v1")

            # Initialize OpenAI client
            self._openai_client = openai.OpenAI(api_key=api_key, base_url=endpoint)

            self.logger.info(
                "OpenAI client initialized successfully for AI classification"
            )

        except ImportError:
            self.logger.error(
                "OpenAI package not installed. Install with: pip install openai. "
                "AI classification will be disabled."
            )
            self._ai_enabled = False
        except Exception as e:
            self.logger.error(
                f"Failed to initialize OpenAI client: {e}. AI classification disabled."
            )
            self._ai_enabled = False

    def _is_text_file(self, filepath: str, mime_type: Optional[str] = None) -> bool:
        """Check if a file is likely to contain readable text."""
        try:
            # Check MIME type first if available
            if mime_type:
                if mime_type.startswith("text/"):
                    return True
                # Some code files might have application MIME types
                if mime_type in [
                    "application/json",
                    "application/xml",
                    "application/javascript",
                    "application/x-python",
                    "application/x-sh",
                ]:
                    return True

            # Check file extension
            file_path = Path(filepath)
            text_extensions = {
                ".txt",
                ".md",
                ".py",
                ".js",
                ".html",
                ".css",
                ".json",
                ".xml",
                ".yaml",
                ".yml",
                ".ini",
                ".cfg",
                ".conf",
                ".log",
                ".csv",
                ".sql",
                ".sh",
                ".bat",
                ".ps1",
                ".c",
                ".cpp",
                ".h",
                ".java",
                ".php",
                ".rb",
                ".go",
                ".rs",
                ".swift",
                ".kt",
            }

            if file_path.suffix.lower() in text_extensions:
                return True

            return False

        except Exception as e:
            self.logger.warning(f"Error checking if file is text: {filepath}: {e}")
            return False

    def _read_file_content(self, filepath: str) -> Optional[str]:
        """Read the first part of a file for AI classification."""
        try:
            ai_config = self.config.get("ai_classification", {})
            max_length = ai_config.get("max_content_length", 2048)

            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(max_length)

            self.logger.debug(
                f"Read {len(content)} characters from {filepath} for AI classification"
            )
            return content

        except UnicodeDecodeError:
            self.logger.debug(
                f"File {filepath} contains non-UTF8 content, skipping AI classification"
            )
            return None
        except Exception as e:
            self.logger.warning(
                f"Error reading file content for AI classification: {filepath}: {e}"
            )
            return None

    def _classify_with_ai(self, filepath: str, content: str) -> Optional[str]:
        """Classify file content using OpenAI GPT."""
        if not self._ai_enabled or not self._openai_client:
            return None

        try:
            ai_config = self.config.get("ai_classification", {})
            model = ai_config.get("model", "gpt-3.5-turbo")
            timeout = ai_config.get("timeout", 30)

            # Prepare the prompt
            prompt = (
                "Analyze the following file content and classify it into one of these categories: "
                "document, image, audio, video, archive, code, executable, pdf, spreadsheet, "
                "presentation, or unknown. Return only the category name.\n\n"
                f"File: {os.path.basename(filepath)}\n"
                f"Content preview:\n{content[:1000]}..."
            )

            self.logger.debug(f"Sending AI classification request for {filepath}")

            response = self._openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a file classifier. Return only the category name.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=50,
                temperature=0.1,
                timeout=timeout,
            )

            ai_category = response.choices[0].message.content.strip().lower()

            # Validate the response
            valid_categories = {
                "document",
                "image",
                "audio",
                "video",
                "archive",
                "code",
                "executable",
                "pdf",
                "spreadsheet",
                "presentation",
                "unknown",
            }

            if ai_category not in valid_categories:
                self.logger.warning(
                    f"AI returned invalid category '{ai_category}' for {filepath}"
                )
                return None

            self.logger.info(f"AI classified {filepath} as '{ai_category}'")
            return ai_category

        except Exception as e:
            self.logger.error(f"Error in AI classification for {filepath}: {e}")
            return None

    def _get_file_extension(self, filepath: str) -> str:
        """Get the file extension, handling compound extensions."""
        file_path = Path(filepath)
        extension = file_path.suffix.lower()

        # Handle compound extensions like .tar.gz
        if extension in [".gz", ".bz2", ".xz"] and len(file_path.suffixes) > 1:
            compound_ext = "".join(file_path.suffixes[-2:]).lower()
            if compound_ext in self.extension_map:
                extension = compound_ext

        return extension

    def _get_traditional_classification(self, filepath: str, extension: str) -> tuple:
        """Get traditional classification based on extension and MIME type."""
        # First try classification by extension
        extension_category = self.extension_map.get(extension)

        # Get MIME type using magic numbers
        metadata = self.file_detector.detect_type_and_metadata(filepath)
        mime_category = None

        if metadata and metadata.get("mime_type"):
            mime_type = metadata["mime_type"]
            mime_category = self.mime_type_map.get(mime_type)

        return extension_category, mime_category, metadata

    def _determine_final_category(
        self, extension_category: str, mime_category: str, metadata: dict
    ) -> str:
        """Determine the final category using traditional classification logic."""
        # Special case: if extension is unknown and MIME type is generic, classify as unknown
        if not extension_category and metadata.get("mime_type") in [
            "text/plain",
            "application/octet-stream",
        ]:
            return "unknown"
        # For specific MIME types that are clearly identifiable, prefer MIME type
        elif mime_category and metadata.get("mime_type") not in [
            "text/plain",
            "application/octet-stream",
        ]:
            return mime_category
        # For generic MIME types or when MIME detection fails, prefer extension
        elif extension_category:
            return extension_category
        # Fallback to MIME category if extension didn't match
        elif mime_category:
            return mime_category
        else:
            return "unknown"

    def classify_file(self, filepath: str) -> str:
        """
        Classify a file based on its extension and magic numbers.

        Args:
            filepath: Path to the file to classify

        Returns:
            str: File category such as 'pdf', 'image', 'archive', 'unknown', etc.
        """
        if not os.path.isfile(filepath):
            self.logger.warning(f"Cannot classify non-existent file: {filepath}")
            return "unknown"

        try:
            # Get file extension
            extension = self._get_file_extension(filepath)

            # Get traditional classification
            extension_category, mime_category, metadata = self._get_traditional_classification(
                filepath, extension
            )

            # Determine final category with traditional logic
            final_category = self._determine_final_category(
                extension_category, mime_category, metadata
            )

            # Try AI classification if enabled and file is suitable
            ai_category = None
            if self._ai_enabled:
                mime_type = metadata.get("mime_type") if metadata else None
                if self._is_text_file(filepath, mime_type):
                    content = self._read_file_content(filepath)
                    if content:
                        ai_category = self._classify_with_ai(filepath, content)

            # Use AI classification if available and different from traditional classification
            if ai_category:
                if final_category == "unknown" or ai_category != final_category:
                    self.logger.info(
                        f"AI classification override: {filepath} "
                        f"traditional: {final_category} -> AI: {ai_category}"
                    )
                    final_category = ai_category

            # Log the classification result
            log_msg = f"File classified: {filepath} -> {final_category} "
            log_msg += f"(ext: {extension}, mime: {metadata.get('mime_type', 'unknown') if metadata else 'unknown'}"
            if ai_category:
                log_msg += f", AI: {ai_category}"
            log_msg += ")"
            self.logger.info(log_msg)

            return final_category

        except Exception as e:
            self.logger.error(f"Error classifying file {filepath}: {e}")
            return "unknown"


def classify_file(
    filepath: str,
    config: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None,
) -> str:
    """
    Convenience function to classify a file without creating a classifier instance.

    Args:
        filepath: Path to the file to classify
        config: Optional configuration dictionary containing AI settings
        logger: Optional logger instance

    Returns:
        str: File category such as 'pdf', 'image', 'archive', 'unknown', etc.
    """
    classifier = FileClassifier(config, logger)
    return classifier.classify_file(filepath)
