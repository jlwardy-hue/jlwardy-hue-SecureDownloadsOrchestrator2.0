import os
import yaml
from pathlib import Path
from copy import deepcopy

def deep_merge_dicts(a, b):
    """Recursively merge dict b into dict a. Modifies a in place."""
    for key, value in b.items():
        if (
            key in a and isinstance(a[key], dict) and isinstance(value, dict)
        ):
            deep_merge_dicts(a[key], value)
        else:
            a[key] = deepcopy(value)
    return a

def load_config(config_path):
    with open(config_path, "r") as f:
        user_config = yaml.safe_load(f)
    # Load defaults (hardcoded or from a file)
    default_config = get_default_config()
    config = deepcopy(default_config)
    deep_merge_dicts(config, user_config or {})
    # Expand user paths (e.g., ~)
    expand_user_paths(config)
    return config

def expand_user_paths(cfg_section):
    # Recursively expand paths
    if isinstance(cfg_section, dict):
        for k, v in cfg_section.items():
            if isinstance(v, str) and ("/" in v or "\" in v):
                cfg_section[k] = os.path.expanduser(v)
            else:
                expand_user_paths(v)

def get_default_config():
    # You may want to load this from a yaml, or keep it hardcoded.
    return {
        "validate_directories": True,
        "logging": {
            "console": {"enabled": True, "level": "INFO"},
            "file": {"enabled": True, "path": "./logs/app.log", "level": "INFO"},
        },
        # ...other defaults...
    }

def validate_config(config, logger=None):
    errors = []
    # Example: required keys
    if "logging" not in config:
        errors.append("Missing logging config section.")
    if "validate_directories" not in config:
        errors.append("Missing validate_directories config option.")
    # Add more validation rules as needed...
    if logger:
        for err in errors:
            logger.warning(f"Config validation: {err}")
    return errors

def get_logging_config(config):
    logging_cfg = config.get("logging", {})
    # Hydrate defaults using setdefault for nested sections
    logging_cfg.setdefault("console", {"enabled": True, "level": "INFO"})
    logging_cfg.setdefault("file", {"enabled": True, "path": "./logs/app.log", "level": "INFO"})
    return logging_cfg
