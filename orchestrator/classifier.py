import os
import logging
import magic
from typing import Optional


class FileClassifier:
    """
    File classifier that categorizes files based on extension and magic numbers.
    Future-proofed for AI/ML integration.
    """
    
    def __init__(self):
        """Initialize the file classifier with magic detection."""
        self.magic = magic.Magic(mime=True)
        
        # Define file categories based on extensions
        self.extension_categories = {
            'pdf': ['.pdf'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'],
            'document': ['.doc', '.docx', '.txt', '.rtf', '.odt'],
            'spreadsheet': ['.xls', '.xlsx', '.csv', '.ods'],
            'presentation': ['.ppt', '.pptx', '.odp'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
            'video': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'],
            'executable': ['.exe', '.msi', '.deb', '.rpm', '.dmg', '.pkg'],
            'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb'],
        }
        
        # Define MIME type patterns for additional classification
        self.mime_patterns = {
            'pdf': ['application/pdf'],
            'image': ['image/'],
            'document': ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'],
            'spreadsheet': ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/csv'],
            'presentation': ['application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'],
            'archive': ['application/zip', 'application/x-rar', 'application/x-7z-compressed', 'application/x-tar'],
            'video': ['video/'],
            'audio': ['audio/'],
            'executable': ['application/x-executable', 'application/x-msdownload'],
            'code': ['text/x-python', 'text/javascript', 'text/html', 'text/css'],
        }
    
    def classify_file(self, filepath: str) -> str:
        """
        Classify a file based on its extension and magic numbers.
        
        Args:
            filepath (str): Path to the file to classify
            
        Returns:
            str: Category of the file (e.g., 'pdf', 'image', 'archive', etc.)
                 Returns 'unknown' if classification fails
        """
        if not os.path.isfile(filepath):
            logging.warning(f"Cannot classify non-existent file: {filepath}")
            return 'unknown'
        
        try:
            # First, try classification by extension
            extension_category = self._classify_by_extension(filepath)
            
            # Then, try classification by MIME type for validation/fallback
            mime_category = self._classify_by_mime_type(filepath)
            
            # Use extension as primary, MIME as fallback
            category = extension_category if extension_category != 'unknown' else mime_category
            
            logging.info(f"File classified: {filepath} -> {category}")
            return category
            
        except Exception as e:
            logging.error(f"Error classifying file {filepath}: {e}")
            return 'unknown'
    
    def _classify_by_extension(self, filepath: str) -> str:
        """Classify file based on its extension."""
        file_extension = os.path.splitext(filepath)[1].lower()
        
        for category, extensions in self.extension_categories.items():
            if file_extension in extensions:
                return category
        
        return 'unknown'
    
    def _classify_by_mime_type(self, filepath: str) -> str:
        """Classify file based on its MIME type using magic numbers."""
        try:
            mime_type = self.magic.from_file(filepath)
            
            for category, patterns in self.mime_patterns.items():
                for pattern in patterns:
                    if mime_type.startswith(pattern):
                        return category
            
            return 'unknown'
            
        except Exception as e:
            logging.debug(f"MIME type detection failed for {filepath}: {e}")
            return 'unknown'
    
    def get_supported_categories(self) -> list:
        """Return list of supported file categories."""
        return list(self.extension_categories.keys())


def classify_file(filepath: str) -> str:
    """
    Convenience function to classify a single file.
    
    Args:
        filepath (str): Path to the file to classify
        
    Returns:
        str: Category of the file
    """
    classifier = FileClassifier()
    return classifier.classify_file(filepath)