"""
SecureDownloadsOrchestrator 2.0

A modular file monitoring and intelligent classification system.
"""

__version__ = "2.0.0"
__author__ = "SecureDownloadsOrchestrator Team"
__description__ = "Intelligent file monitoring and classification system"

# Package imports for convenience
from .config_loader import ConfigLoader
from .logger import setup_logger

__all__ = ["ConfigLoader", "setup_logger"]