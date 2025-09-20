import os
from copy import deepcopy

import yaml


def deep_merge_dicts(a, b):
    """Recursively merge dict b into dict a. Modifies a in place."""
    for key, value in b.items():
        if key in a and isinstance(a[key], dict) and isinstance(value, dict):
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
            if isinstance(v, str) and ("/" in v or "\\" in v):
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
        "processing": {
            "enable_ai_classification": False,
            "enable_security_scan": False,
            "enable_ocr": True,
            "enable_archive_extraction": True,
            "enable_unified_pipeline": True,
        },
        "ai_classification": {
            "enabled": False,
            "model": "gpt-3.5-turbo",
            "max_tokens": 1000,
            "temperature": 0.1,
            "max_file_size_bytes": 1048576,
            "max_content_length": 8000,
            "supported_mime_types": [
                "text/plain",
                "text/markdown",
                "text/html",
                "text/css",
                "text/javascript",
                "application/javascript",
                "application/json",
                "application/xml",
                "text/xml",
                "text/csv",
                "application/x-python",
                "text/x-python",
                "text/x-script.python",
            ],
            "fallback_to_rule_based": True,
            "log_prompts": False,
            "log_responses": False,
            "log_errors": True,
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
    logging_cfg.setdefault(
        "file", {"enabled": True, "path": "./logs/app.log", "level": "INFO"}
    )
    return logging_cfg


def get_ai_classification_config(config):
    """Get AI classification configuration with defaults."""
    ai_config = config.get("ai_classification", {})
    # Set defaults if not present
    ai_config.setdefault("enabled", False)
    ai_config.setdefault("model", "gpt-3.5-turbo")
    ai_config.setdefault("max_tokens", 1000)
    ai_config.setdefault("temperature", 0.1)
    ai_config.setdefault("max_file_size_bytes", 1048576)
    ai_config.setdefault("max_content_length", 8000)
    ai_config.setdefault("fallback_to_rule_based", True)
    ai_config.setdefault("log_prompts", False)
    ai_config.setdefault("log_responses", False)
    ai_config.setdefault("log_errors", True)

    # Default prompt template if not specified
    if "prompt_template" not in ai_config:
        ai_config[
            "prompt_template"
        ] = """You are an expert file analyzer. Analyze the following file and provide a comprehensive classification and analysis.

File Information:
- Filename: {filename}
- Extension: {file_extension}
- MIME Type: {mime_type}
- Size: {file_size} bytes

File Content (first {max_content_length} characters):
```
{file_content}
```

Please analyze this file and respond with a JSON object containing:
1. "category": Primary file category (document, code, data, config, script, etc.)
2. "subcategory": More specific classification (python_script, html_document, json_config, etc.)
3. "programming_language": If it's code, specify the language (or null if not applicable)
4. "summary": Brief 1-2 sentence description of the file's purpose/content
5. "key_technologies": Array of technologies/frameworks detected (e.g., ["React", "CSS3"])
6. "sensitive_data_indicators": Array of potential sensitive data types found (e.g., ["email_addresses", "api_keys", "passwords"])
7. "confidence_score": Float between 0-1 indicating classification confidence
8. "metadata": Object with additional relevant information

Respond ONLY with valid JSON, no other text or explanations."""

    return ai_config
