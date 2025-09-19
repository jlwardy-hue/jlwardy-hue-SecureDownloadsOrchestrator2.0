import logging
import logging.handlers
import os


def setup_logger(name, config):
    """
    Set up logger with rotation support for persistent logs.
    
    Implements log rotation with reasonable defaults to prevent disk space
    exhaustion from unbounded log growth.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate logs if root handlers exist
    logger.propagate = False

    logging_cfg = config.get("logging", {})
    # Hydrate defaults
    logging_cfg.setdefault("console", {"enabled": True, "level": "INFO"})
    logging_cfg.setdefault("file", {
        "enabled": True, 
        "path": "./logs/app.log", 
        "level": "INFO",
        "rotation": {
            "enabled": True,
            "max_bytes": 10 * 1024 * 1024,  # 10MB per file
            "backup_count": 5,  # Keep 5 backup files
            "when": "midnight",  # Rotate at midnight
            "interval": 1  # Every 1 day
        }
    })

    # Console handler
    if logging_cfg["console"].get("enabled", True):
        ch = logging.StreamHandler()
        ch.setLevel(logging_cfg["console"].get("level", "INFO"))
        ch.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(ch)

    # File handler with rotation
    if logging_cfg["file"].get("enabled", True):
        log_path = os.path.expanduser(logging_cfg["file"].get("path", "./logs/app.log"))
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        rotation_config = logging_cfg["file"].get("rotation", {})
        
        if rotation_config.get("enabled", True):
            # Use rotating file handler to prevent disk space issues
            max_bytes = rotation_config.get("max_bytes", 10 * 1024 * 1024)  # 10MB default
            backup_count = rotation_config.get("backup_count", 5)
            
            fh = logging.handlers.RotatingFileHandler(
                log_path, 
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            
            logger.info(f"Log rotation enabled: max_bytes={max_bytes}, backup_count={backup_count}")
        else:
            # Use standard file handler (no rotation)
            fh = logging.FileHandler(log_path)
            logger.warning("Log rotation disabled - monitor disk space manually")
        
        fh.setLevel(logging_cfg["file"].get("level", "INFO"))
        fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(fh)

    return logger

def log_startup_info(logger, app_cfg):
    """Log application startup information."""
    app_name = app_cfg.get("name", "SecureDownloadsOrchestrator")
    app_version = app_cfg.get("version", "2.0")
    logger.info(f"Starting {app_name} v{app_version}")
    logger.info("Initializing application components...")

def log_shutdown_info(logger):
    """Log application shutdown information."""
    logger.info("Application shutdown completed successfully")
