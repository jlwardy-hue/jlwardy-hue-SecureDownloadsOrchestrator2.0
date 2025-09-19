"""
File classification module for SecureDownloadsOrchestrator 2.0

Provides file classification functionality using file extensions and magic numbers
to categorize files into types like 'pdf', 'image', 'archive', etc.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from orchestrator.file_type_detector import FileTypeDetector


class FileClassifier:
    """File classifier that uses both file extensions and MIME types for accurate classification."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the file classifier."""
        self.logger = logger or logging.getLogger(__name__)
        self.file_detector = FileTypeDetector()

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
            file_path = Path(filepath)
            extension = file_path.suffix.lower()

            # Handle compound extensions like .tar.gz
            if extension in [".gz", ".bz2", ".xz"] and len(file_path.suffixes) > 1:
                compound_ext = "".join(file_path.suffixes[-2:]).lower()
                if compound_ext in self.extension_map:
                    extension = compound_ext

            # First try classification by extension
            extension_category = self.extension_map.get(extension)

            # Get MIME type using magic numbers
            metadata = self.file_detector.detect_type_and_metadata(filepath)
            mime_category = None

            if metadata and metadata.get("mime_type"):
                mime_type = metadata["mime_type"]
                mime_category = self.mime_type_map.get(mime_type)

            # Determine final category with improved logic
            final_category = "unknown"

            # Special case: if extension is unknown and MIME type is generic, classify as unknown
            if not extension_category and metadata.get("mime_type") in [
                "text/plain",
                "application/octet-stream",
            ]:
                final_category = "unknown"
            # For specific MIME types that are clearly identifiable, prefer MIME type
            elif mime_category and metadata.get("mime_type") not in [
                "text/plain",
                "application/octet-stream",
            ]:
                final_category = mime_category
            # For generic MIME types or when MIME detection fails, prefer extension
            elif extension_category:
                final_category = extension_category
            # Fallback to MIME category if extension didn't match
            elif mime_category:
                final_category = mime_category

            # Log the classification result
            self.logger.info(
                f"File classified: {filepath} -> {final_category} "
                f"(ext: {extension}, mime: {metadata.get('mime_type', 'unknown') if metadata else 'unknown'})"
            )

            return final_category

        except Exception as e:
            self.logger.error(f"Error classifying file {filepath}: {e}")
            return "unknown"


def classify_file(filepath: str, logger: Optional[logging.Logger] = None) -> str:
    """
    Convenience function to classify a file without creating a classifier instance.

    Args:
        filepath: Path to the file to classify
        logger: Optional logger instance

    Returns:
        str: File category such as 'pdf', 'image', 'archive', 'unknown', etc.
    """
    classifier = FileClassifier(logger)
    return classifier.classify_file(filepath)
