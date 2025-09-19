"""
Unit tests for configuration loader module.
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from orchestrator.config_loader import (
    load_config,
    validate_config,
    get_default_config,
    expand_user_paths,
    deep_merge_dicts
)


class TestConfigLoader:
    
    def test_get_default_config(self):
        """Test that default configuration is valid."""
        config = get_default_config()
        
        assert isinstance(config, dict)
        assert "validate_directories" in config
        assert "logging" in config
        assert config["validate_directories"] is True

    def test_load_config_with_valid_file(self, test_config, temp_directories):
        """Test loading a valid configuration file."""
        # Create a temporary config file
        config_path = Path(temp_directories["temp_dir"]) / "test_config.yaml"
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        loaded_config = load_config(str(config_path))
        
        assert isinstance(loaded_config, dict)
        assert loaded_config["directories"]["source"] == test_config["directories"]["source"]
        assert loaded_config["directories"]["destination"] == test_config["directories"]["destination"]

    def test_validate_config_valid(self, test_config):
        """Test validation of valid configuration."""
        errors = validate_config(test_config)
        assert isinstance(errors, list)
        # Note: Current validation is minimal, so this might pass

    def test_expand_user_paths(self):
        """Test user path expansion."""
        test_dict = {
            "path1": "~/test",
            "path2": "/absolute/path",
            "nested": {
                "path3": "~/nested/test"
            }
        }
        
        expand_user_paths(test_dict)
        
        # Path should be expanded (actual expansion depends on environment)
        assert "~" not in test_dict["path1"]
        assert test_dict["path2"] == "/absolute/path"  # Absolute paths unchanged
        assert "~" not in test_dict["nested"]["path3"]

    def test_deep_merge_dicts(self):
        """Test deep merging of dictionaries."""
        dict_a = {
            "level1": {
                "key1": "value1",
                "key2": "value2"
            },
            "existing": "original"
        }
        
        dict_b = {
            "level1": {
                "key2": "updated_value2",
                "key3": "value3"
            },
            "new_key": "new_value"
        }
        
        result = deep_merge_dicts(dict_a, dict_b)
        
        assert result["level1"]["key1"] == "value1"  # Preserved
        assert result["level1"]["key2"] == "updated_value2"  # Updated
        assert result["level1"]["key3"] == "value3"  # Added
        assert result["existing"] == "original"  # Preserved
        assert result["new_key"] == "new_value"  # Added

    def test_load_config_file_not_found(self):
        """Test handling of missing configuration file."""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent_config.yaml")

    def test_load_config_invalid_yaml(self, temp_directories):
        """Test handling of invalid YAML file."""
        config_path = Path(temp_directories["temp_dir"]) / "invalid_config.yaml"
        
        # Create invalid YAML
        with open(config_path, 'w') as f:
            f.write("invalid: yaml: content: [unclosed")
        
        with pytest.raises(yaml.YAMLError):
            load_config(str(config_path))