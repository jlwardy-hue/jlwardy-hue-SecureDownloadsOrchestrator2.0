"""
Unit tests for setup script directory creation functionality.
"""

import os
import sys
import tempfile
from pathlib import Path

import yaml

# Add repo root to path to import setup module
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

from scripts.setup import SetupManager


class TestSetupDirectoryCreation:
    """Test directory creation functionality in setup script."""

    def test_create_runtime_directories_with_valid_config(self):
        """Test that setup creates directories from config.yaml."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a test config file
            config_content = {
                "directories": {
                    "source": str(temp_path / "test_source"),
                    "destination": str(temp_path / "test_dest"),
                },
                "categories": {
                    "documents": {
                        "extensions": [".pdf", ".txt"],
                        "destination": "documents",
                    },
                    "images": {"extensions": [".jpg", ".png"], "destination": "images"},
                },
                "logging": {"console": {"enabled": True}},
                "application": {"name": "test"},
            }

            config_file = temp_path / "config.yaml"
            with open(config_file, "w") as f:
                yaml.dump(config_content, f)

            # Initialize SetupManager and test directory creation
            setup_manager = SetupManager(temp_path)

            # Change to temp directory to find the config file
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_path)
                result = setup_manager.create_runtime_directories()
                assert result is True

                # Verify source and destination directories were created
                assert (temp_path / "test_source").exists()
                assert (temp_path / "test_dest").exists()

                # Verify category subdirectories were created
                assert (temp_path / "test_dest" / "documents").exists()
                assert (temp_path / "test_dest" / "images").exists()

                # Verify logs directory was created
                assert (temp_path / "logs").exists()

            finally:
                os.chdir(original_cwd)

    def test_create_runtime_directories_with_relative_paths(self):
        """Test directory creation with relative paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            config_content = {
                "directories": {"source": "./rel_source", "destination": "./rel_dest"},
                "categories": {
                    "documents": {"extensions": [".pdf"], "destination": "documents"}
                },
                "logging": {"console": {"enabled": True}},
                "application": {"name": "test"},
            }

            config_file = temp_path / "config.yaml"
            with open(config_file, "w") as f:
                yaml.dump(config_content, f)

            setup_manager = SetupManager(temp_path)

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_path)
                result = setup_manager.create_runtime_directories()
                assert result is True

                # Verify relative path directories were created
                assert (temp_path / "rel_source").exists()
                assert (temp_path / "rel_dest").exists()
                assert (temp_path / "rel_dest" / "documents").exists()

            finally:
                os.chdir(original_cwd)

    def test_create_runtime_directories_permission_error(self):
        """Test error handling when directory creation fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create config with inaccessible path
            config_content = {
                "directories": {
                    "source": "/root/inaccessible",
                    "destination": str(temp_path / "test_dest"),
                },
                "categories": {},
                "logging": {"console": {"enabled": True}},
                "application": {"name": "test"},
            }

            config_file = temp_path / "config.yaml"
            with open(config_file, "w") as f:
                yaml.dump(config_content, f)

            setup_manager = SetupManager(temp_path)

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_path)
                result = setup_manager.create_runtime_directories()

                # Should fail due to permission error
                assert result is False
                assert len(setup_manager.issues) > 0
                assert "Permission denied" in str(
                    setup_manager.issues[0]
                ) or "Failed to create directory" in str(setup_manager.issues[0])

            finally:
                os.chdir(original_cwd)

    def test_create_runtime_directories_missing_config(self):
        """Test graceful handling when config.yaml is missing or invalid."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # No config.yaml file
            setup_manager = SetupManager(temp_path)

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_path)
                result = setup_manager.create_runtime_directories()

                # Should still succeed (logs dir created) but warn about config directories
                assert result is True
                assert len(setup_manager.warnings) > 0
                assert "Could not create config directories" in str(
                    setup_manager.warnings[0]
                )

                # Logs directory should still be created
                assert (temp_path / "logs").exists()

            finally:
                os.chdir(original_cwd)

    def test_create_runtime_directories_empty_paths(self):
        """Test handling of empty or missing directory paths in config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            config_content = {
                "directories": {
                    "source": "",  # Empty path
                    "destination": None,  # Null path
                },
                "categories": {},
                "logging": {"console": {"enabled": True}},
                "application": {"name": "test"},
            }

            config_file = temp_path / "config.yaml"
            with open(config_file, "w") as f:
                yaml.dump(config_content, f)

            setup_manager = SetupManager(temp_path)

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_path)
                result = setup_manager.create_runtime_directories()

                # Should succeed - empty paths are skipped
                assert result is True

                # Only logs directory should be created
                assert (temp_path / "logs").exists()

            finally:
                os.chdir(original_cwd)
