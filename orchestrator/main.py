"""
Main entry point for SecureDownloadsOrchestrator 2.0

Loads configuration, sets up logging, and displays startup information.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the Python path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure config.yaml exists in the project root directory.")
        sys.exit(1)
        
    except Exception as e:
        print(f"Unexpected error during startup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()