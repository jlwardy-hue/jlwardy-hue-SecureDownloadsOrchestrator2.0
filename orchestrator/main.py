"""
Main entry point for SecureDownloadsOrchestrator 2.0+

Loads configuration, sets up logging, and manages application startup.
"""

import sys
from pathlib import Path
from orchestrator.config_loader import load_config
from orchestrator.logger import setup_logger, log_startup_info, log_shutdown_info

def create_directories(config: dict, logger) -> bool:
    directories = config.get("directories", {})
    for kind, path in directories.items():
        if path:
            dir_path = Path(path)
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Directory ready: {kind} -> {dir_path}")
            except Exception as e:
                logger.error(f"Failed to create directory {kind} ({dir_path}): {e}")
                return False

    # Create category destination dirs
    categories = config.get("categories", {})
    base_dest = directories.get("destination", "")
    if base_dest:
        for cat, cat_cfg in categories.items():
            dest_dir = Path(base_dest) / cat_cfg.get("destination", cat)
            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Category directory ready: {cat} -> {dest_dir}")
            except Exception as e:
                logger.warning(f"Failed to create category directory {cat}: {e}")
    return True

def display_configuration_summary(config: dict, logger):
    logger.info("Configuration Summary:")
    logger.info("-" * 40)
    directories = config.get("directories", {})
    logger.info("Directory Configuration:")
    for dtype, dpath in directories.items():
        logger.info(f"  {dtype.capitalize()}: {dpath}")
    categories = config.get("categories", {})
    logger.info(f"File Categories: {len(categories)} configured")
    for cname, ccfg in categories.items():
        exts = ', '.join(ccfg.get("extensions", []))
        logger.info(f"  {cname}: {exts}")
    processing = config.get("processing", {})
    logger.info(f"AI Classification: {'ENABLED' if processing.get('enable_ai_classification', False) else 'DISABLED'}")
    logger.info(f"Security Scanning: {'ENABLED' if processing.get('enable_security_scan', False) else 'DISABLED'}")

def validate_configuration(config: dict, logger) -> bool:
    required = ["directories", "categories", "logging", "application"]
    missing = [k for k in required if k not in config]
    if missing:
        logger.error(f"Missing required configuration sections: {missing}")
        return False
    directories = config.get("directories", {})
    if not directories.get("source"):
        logger.error("Source directory not configured")
        return False
    if not directories.get("destination"):
        logger.error("Destination directory not configured")
        return False
    source_path = Path(directories["source"])
    if not source_path.exists():
        logger.warning(f"Source directory does not exist: {source_path}")
        logger.info("This is normal for initial setup - directory will be monitored when created")
    logger.info("Configuration validation passed")
    return True

def main():
    try:
        config = load_config("config.yaml")
        logger = setup_logger("orchestrator", config.get("logging", {}), force=True)
        app_cfg = config.get("application", {})
        log_startup_info(logger, app_cfg)
        startup_cfg = app_cfg.get("startup", {})
        if startup_cfg.get("validate_config", True):
            if not validate_configuration(config, logger):
                logger.error("Configuration validation failed. Exiting.")
                sys.exit(1)
        if startup_cfg.get("create_missing_dirs", True):
            if not create_directories(config, logger):
                logger.error("Failed to create required directories. Exiting.")
                sys.exit(1)
        display_configuration_summary(config, logger)
        logger.info("SecureDownloadsOrchestrator initialized successfully")
        logger.info("Ready for modular expansion...")
        logger.info("Current status: Foundation complete - awaiting file monitoring and AI modules")
        logger.info("Application startup test completed successfully")
        log_shutdown_info(logger)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure config.yaml exists in the project root directory.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during startup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()