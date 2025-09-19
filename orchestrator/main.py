"""
Main entry point for SecureDownloadsOrchestrator 2.0+

Loads configuration, sets up logging, and manages application startup.
"""

import sys
import time
from pathlib import Path
from orchestrator.config_loader import load_config
from orchestrator.logger import setup_logger, log_startup_info, log_shutdown_info
from orchestrator.file_watcher import FileWatcher
from orchestrator.classifier import classify_file
from orchestrator.pipeline import create_unified_processor

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

def handle_new_file(filepath, logger, config=None):
    """
    Handle newly detected or modified files.
    Uses the unified pipeline for comprehensive processing if enabled,
    otherwise falls back to simple classification.
    """
    logger.info(f"Processing detected file: {filepath}")
    
    try:
        # Check if unified pipeline is enabled
        processing_config = config.get("processing", {}) if config else {}
        use_unified_pipeline = processing_config.get("enable_unified_pipeline", False)
        
        if use_unified_pipeline:
            # Use the new unified pipeline
            logger.info("Using unified file processing pipeline")
            processor = create_unified_processor(config, logger)
            result = processor.process_file(filepath)
            
            if result.success:
                logger.info(f"Pipeline processing complete: {filepath} -> {result.final_path}")
                if result.metadata:
                    logger.debug(f"Processing metadata: {result.metadata}")
            else:
                logger.error(f"Pipeline processing failed: {result.error}")
        else:
            # Fallback to simple classification
            logger.info("Using simple classification (unified pipeline disabled)")
            file_category = classify_file(filepath, logger)
            logger.info(f"File classification complete: {filepath} -> {file_category}")
            
            # TODO: Future processing steps based on classification:
            # - Move files to appropriate category directories
            # - Trigger security scanning for executable files
            # - Generate alerts for sensitive file types
            # - Apply category-specific processing rules
        
    except Exception as e:
        logger.error(f"Error during file processing: {e}")

def main():
    watcher = None
    try:
        # Allow config file to be specified as command line argument
        config_file = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
        config = load_config(config_file)
        logger = setup_logger("orchestrator", config.get("logging", {}))
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
        
        # Initialize and start file watcher
        source_dir = config.get("directories", {}).get("source")
        if source_dir:
            logger.info("Initializing file monitoring service...")
            # Create a callback that includes the logger and config
            def file_callback(filepath):
                handle_new_file(filepath, logger, config)
            
            watcher = FileWatcher(source_dir, file_callback, logger)
            watcher.start()
            logger.info("File monitoring service started successfully")
        else:
            logger.warning("No source directory configured - file monitoring disabled")
        
        logger.info("SecureDownloadsOrchestrator initialized successfully")
        logger.info("Ready for modular expansion...")
        logger.info("Current status: Foundation complete - file monitoring active")
        
        # Keep the application running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal...")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure config.yaml exists in the project root directory.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during startup: {e}")
        sys.exit(1)
    finally:
        if watcher:
            logger.info("Shutting down file monitoring service...")
            watcher.stop()
        log_shutdown_info(logger)

if __name__ == "__main__":
    main()