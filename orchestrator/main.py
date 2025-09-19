"""
Main entry point for SecureDownloadsOrchestrator 2.0

Loads configuration, sets up logging, and displays startup information.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the Python path to allow imports

from orchestrator.config_loader import ConfigLoader
from orchestrator.logger import setup_logger, log_startup_info, log_shutdown_info


def create_directories(config: dict, logger) -> bool:
    """
    Create necessary directories based on configuration.
    
    Args:
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        True if all directories were created successfully, False otherwise
    """
    directories = config.get('directories', {})
    
    for dir_type, dir_path in directories.items():
        if dir_path:
            path = Path(dir_path)
            try:
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Directory ready: {dir_type} -> {dir_path}")
            except Exception as e:
                logger.error(f"Failed to create directory {dir_type} ({dir_path}): {e}")
                return False
    
    # Create category destination directories
    categories = config.get('categories', {})
    base_dest = directories.get('destination', '')
    
    if base_dest:
        for category_name, category_config in categories.items():
            dest_dir = Path(base_dest) / category_config.get('destination', category_name)
            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Category directory ready: {category_name} -> {dest_dir}")
            except Exception as e:
                logger.warning(f"Failed to create category directory {category_name}: {e}")
    
    return True


def validate_configuration(config: dict, logger) -> bool:
    """
    Validate the loaded configuration.
    
    Args:
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        True if configuration is valid, False otherwise
    """
    # Check required sections
    required_sections = ['directories', 'categories', 'logging', 'application']
    missing_sections = [section for section in required_sections if section not in config]
    
    if missing_sections:
        logger.error(f"Missing required configuration sections: {missing_sections}")
        return False
    
    # Check directory configuration
    directories = config.get('directories', {})
    if not directories.get('source'):
        logger.error("Source directory not configured")
        return False
    
    if not directories.get('destination'):
        logger.error("Destination directory not configured")
        return False
    
    # Check if source directory exists
    source_path = Path(directories['source'])
    if not source_path.exists():
        logger.warning(f"Source directory does not exist: {source_path}")
        logger.info("This is normal for initial setup - directory will be monitored when created")
    
    logger.info("Configuration validation passed")
    return True


def display_configuration_summary(config: dict, logger) -> None:
    """
    Display a summary of the current configuration.
    
    Args:
        config: Configuration dictionary
        logger: Logger instance
    """
    logger.info("Configuration Summary:")
    logger.info("-" * 40)
    
    # Directory configuration
    directories = config.get('directories', {})
    logger.info("Directory Configuration:")
    for dir_type, dir_path in directories.items():
        logger.info(f"  {dir_type.capitalize()}: {dir_path}")
    
    # Categories
    categories = config.get('categories', {})
    logger.info(f"File Categories: {len(categories)} configured")
    for category_name, category_config in categories.items():
        extensions = ', '.join(category_config.get('extensions', []))
        logger.info(f"  {category_name}: {extensions}")
    
    # Processing settings
    processing = config.get('processing', {})
    ai_enabled = processing.get('enable_ai_classification', False)
    security_enabled = processing.get('enable_security_scan', False)
    logger.info(f"AI Classification: {'ENABLED' if ai_enabled else 'DISABLED'}")
    logger.info(f"Security Scanning: {'ENABLED' if security_enabled else 'DISABLED'}")


def main():
    """Main application entry point."""
    try:
        # Load configuration
        config_loader = ConfigLoader()
        config = config_loader.load()
        
        # Set up logging
        logging_config = config.get('logging', {})
        logger = setup_logger('orchestrator', logging_config)
        
        # Log startup information
        app_config = config.get('application', {})
        log_startup_info(logger, app_config)
        
        # Validate configuration if enabled
        startup_config = app_config.get('startup', {})
        if startup_config.get('validate_config', True):
            if not validate_configuration(config, logger):
                logger.error("Configuration validation failed. Exiting.")
                sys.exit(1)
        
        # Create directories if enabled
        if startup_config.get('create_missing_dirs', True):
            if not create_directories(config, logger):
                logger.error("Failed to create required directories. Exiting.")
                sys.exit(1)
        
        # Display configuration summary
        display_configuration_summary(config, logger)
        
        logger.info("SecureDownloadsOrchestrator 2.0 initialized successfully")
        logger.info("Ready for modular expansion...")
        logger.info("Current status: Foundation complete - awaiting file monitoring and AI classification modules")
        
        # For now, just show that the application can start and load everything correctly
        logger.info("Application startup test completed successfully")
        
        # Log shutdown
        log_shutdown_info(logger)
        
=======
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
 main
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure config.yaml exists in the project root directory.")
        sys.exit(1)

        

 main
    except Exception as e:
        print(f"Unexpected error during startup: {e}")
        sys.exit(1)




 main
if __name__ == "__main__":
    main()