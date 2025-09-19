
"""
Logging utilities for SecureDownloadsOrchestrator 2.0

Provides structured logging with configurable levels and file output.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any, Optional


def setup_logger(name: str = "orchestrator", config: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Set up a logger with the specified configuration.
    
    Args:
        name: Logger name
        config: Logging configuration dictionary
        
    Returns:
        Configured logger instance
    """
    # Default configuration
    default_config = {
        'level': 'INFO',
        'file': {
            'enabled': True,
            'path': 'logs/orchestrator.log',
            'max_size_mb': 10,
            'backup_count': 5,
            'rotation': True
        },
        'console': {
            'enabled': True,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }
    
    # Merge with provided config
    if config:
        default_config.update(config)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, default_config['level'].upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Set up file logging if enabled
    if default_config['file']['enabled']:
        _setup_file_handler(logger, default_config['file'])
    
    # Set up console logging if enabled
    if default_config['console']['enabled']:
        _setup_console_handler(logger, default_config['console'])
    
    return logger


def _setup_file_handler(logger: logging.Logger, file_config: Dict[str, Any]) -> None:
    """Set up file logging handler."""
    log_file = Path(file_config['path'])
    
    # Create log directory if it doesn't exist
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    if file_config.get('rotation', True):
        # Use rotating file handler
        max_bytes = file_config.get('max_size_mb', 10) * 1024 * 1024
        backup_count = file_config.get('backup_count', 5)
        
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
    else:
        # Use basic file handler
        handler = logging.FileHandler(log_file, encoding='utf-8')
    
    # Set up formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)


def _setup_console_handler(logger: logging.Logger, console_config: Dict[str, Any]) -> None:
    """Set up console logging handler."""
    handler = logging.StreamHandler()
    
    # Set up formatter
    format_string = console_config.get(
        'format', 
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    formatter = logging.Formatter(format_string, datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)


def get_component_logger(component_name: str, config: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Get a logger for a specific component.
    
    Args:
        component_name: Name of the component (e.g., 'file_watcher', 'ai_classifier')
        config: Optional logging configuration
        
    Returns:
        Logger instance for the component
    """
    logger_name = f"orchestrator.{component_name}"
    
    # Check if component-specific logging level is configured
    if config and 'components' in config and component_name in config['components']:
        component_config = config.copy()
        component_config['level'] = config['components'][component_name]
        return setup_logger(logger_name, component_config)
    
    return setup_logger(logger_name, config)


class LoggerMixin:
    """Mixin class to provide logging capabilities to other classes."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = None
    
    @property
    def logger(self) -> logging.Logger:
        """Get or create a logger for this class."""
        if self._logger is None:
            class_name = self.__class__.__name__.lower()
            self._logger = get_component_logger(class_name)
        return self._logger
    
    def set_logger(self, logger: logging.Logger) -> None:
        """Set a custom logger for this instance."""
        self._logger = logger


def log_startup_info(logger: logging.Logger, app_config: Dict[str, Any]) -> None:
    """
    Log application startup information.
    
    Args:
        logger: Logger instance
        app_config: Application configuration
    """
    app_name = app_config.get('name', 'SecureDownloadsOrchestrator')
    app_version = app_config.get('version', '2.0.0')
    
    logger.info("=" * 60)
    logger.info(f"Starting {app_name} v{app_version}")
    logger.info("=" * 60)
    
    # Log configuration summary
    startup_config = app_config.get('startup', {})
    if startup_config.get('check_directories', True):
        logger.info("Directory validation: ENABLED")
    if startup_config.get('create_missing_dirs', True):
        logger.info("Auto-create missing directories: ENABLED")
    if startup_config.get('validate_config', True):
        logger.info("Configuration validation: ENABLED")


def log_shutdown_info(logger: logging.Logger) -> None:
    """Log application shutdown information."""
    logger.info("=" * 60)
    logger.info("SecureDownloadsOrchestrator shutdown complete")
    logger.info("=" * 60)
=======
import logging
import os

def setup_logger(name, config):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate logs if root handlers exist
    logger.propagate = False

    logging_cfg = config.get("logging", {})
    # Hydrate defaults
    logging_cfg.setdefault("console", {"enabled": True, "level": "INFO"})
    logging_cfg.setdefault("file", {"enabled": True, "path": "./logs/app.log", "level": "INFO"})

    if logging_cfg["console"].get("enabled", True):
        ch = logging.StreamHandler()
        ch.setLevel(logging_cfg["console"].get("level", "INFO"))
        ch.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(ch)

    if logging_cfg["file"].get("enabled", True):
        log_path = os.path.expanduser(logging_cfg["file"].get("path", "./logs/app.log"))
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging_cfg["file"].get("level", "INFO"))
        fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(fh)

    return logger
 main
