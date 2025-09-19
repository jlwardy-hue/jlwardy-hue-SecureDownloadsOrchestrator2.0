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
