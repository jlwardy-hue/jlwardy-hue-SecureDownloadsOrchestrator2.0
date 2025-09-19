import logging
import time
from orchestrator.config_loader import load_config
from orchestrator.logger import setup_logger
from orchestrator.file_watcher import FileWatcher
from orchestrator.classifier import classify_file
from file_type_detector import FileTypeDetector

def handle_new_file(filepath):
    logging.info(f"Handling new file: {filepath}")
    
    # Classify the file
    category = classify_file(filepath)
    logging.info(f"File classification: {filepath} -> {category}")
    
    # Extract metadata using existing detector
    detector = FileTypeDetector()
    metadata = detector.detect_type_and_metadata(filepath)
    if metadata:
        logging.info(f"Metadata extracted for {filepath}: {metadata}")
    else:
        logging.error(f"Could not extract metadata for {filepath}")
    
    # TODO: Future pipeline steps based on classification
    # - Move files based on category
    # - Security scanning for certain file types
    # - AI/ML enhanced classification
    # - Alert generation for suspicious files
    logging.debug(f"Ready for future pipeline processing of {category} file: {filepath}")

def main():
    config = load_config()
    setup_logger(config)
    downloads_dir = config["directories"]["downloads"]
    logging.info("SecureDownloadsOrchestrator2.0 starting up...")
    watcher = FileWatcher(downloads_dir, handle_new_file)
    watcher.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down watcher.")
        watcher.stop()

if __name__ == "__main__":
    main()