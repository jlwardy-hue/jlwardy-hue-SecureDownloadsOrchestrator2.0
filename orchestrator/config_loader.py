
"""
Configuration loader for SecureDownloadsOrchestrator 2.0

Handles loading and validation of YAML configuration files.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Loads and manages application configuration from YAML files."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_path: Path to the configuration file. Defaults to 'config.yaml'
        """
        if config_path is None:
            # Default to config.yaml in the project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config: Optional[Dict[str, Any]] = None
        
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from the YAML file.
        
        Returns:
            Dictionary containing the configuration data
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            yaml.YAMLError: If configuration file is invalid YAML
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._config = yaml.safe_load(file)
                
            # Expand user paths in directory settings
            self._expand_paths()
            
            return self._config
            
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in configuration file: {e}")
    
    def _expand_paths(self):
        """Expand user paths (~) in directory configuration."""
        if self._config and 'directories' in self._config:
            for key, path in self._config['directories'].items():
                if isinstance(path, str) and path.startswith('~'):
                    self._config['directories'][key] = os.path.expanduser(path)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'logging.level')
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        if self._config is None:
            self.load()
        
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_directories(self) -> Dict[str, str]:
        """Get directory configuration."""
        return self.get('directories', {})
    
    def get_categories(self) -> Dict[str, Dict[str, Any]]:
        """Get file categories configuration."""
        return self.get('categories', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get('logging', {})
    
    def get_gpt_config(self) -> Dict[str, Any]:
        """Get GPT configuration."""
        return self.get('gpt', {})
    
    def get_application_config(self) -> Dict[str, Any]:
        """Get application configuration."""
        return self.get('application', {})
    
    def validate(self) -> bool:
        """
        Validate the loaded configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if self._config is None:
            return False
        
        required_sections = ['directories', 'categories', 'logging', 'application']
        
        for section in required_sections:
            if section not in self._config:
                print(f"Warning: Missing required configuration section: {section}")
                return False
        
        # Validate directory paths
        directories = self.get_directories()
        if not directories.get('source'):
            print("Warning: Source directory not configured")
            return False
        
        if not directories.get('destination'):
            print("Warning: Destination directory not configured")
            return False
        
        return True
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary."""
        if self._config is None:
            self.load()
        return self._config or {}
    
    def reload(self) -> Dict[str, Any]:
        """Reload configuration from file."""
        self._config = None
        return self.load()
=======
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
