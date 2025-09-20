"""
Basic import test to confirm orchestrator package is always importable.

This test ensures that the orchestrator package and its main modules
can be imported successfully, which is essential for both running
the application and running tests.
"""

import pytest


class TestOrchestratorImports:
    """Test basic imports of orchestrator package."""

    def test_import_orchestrator_package(self):
        """Test that orchestrator package can be imported."""
        try:
            import orchestrator

            assert hasattr(orchestrator, "__version__")
        except ImportError as e:
            pytest.fail(f"Failed to import orchestrator package: {e}")

    def test_import_main_module(self):
        """Test that orchestrator.main module can be imported."""
        try:
            from orchestrator.main import main

            assert callable(main)
        except ImportError as e:
            pytest.fail(f"Failed to import orchestrator.main: {e}")

    def test_import_config_loader(self):
        """Test that orchestrator.config_loader module can be imported."""
        try:
            from orchestrator.config_loader import load_config

            assert callable(load_config)
        except ImportError as e:
            pytest.fail(f"Failed to import orchestrator.config_loader: {e}")

    def test_import_classifier(self):
        """Test that orchestrator.classifier module can be imported."""
        try:
            from orchestrator.classifier import FileClassifier, classify_file

            assert callable(classify_file)
            assert FileClassifier is not None
        except ImportError as e:
            pytest.fail(f"Failed to import orchestrator.classifier: {e}")

    def test_import_logger(self):
        """Test that orchestrator.logger module can be imported."""
        try:
            from orchestrator.logger import setup_logger

            assert callable(setup_logger)
        except ImportError as e:
            pytest.fail(f"Failed to import orchestrator.logger: {e}")

    def test_import_file_watcher(self):
        """Test that orchestrator.file_watcher module can be imported."""
        try:
            from orchestrator.file_watcher import FileWatcher

            assert FileWatcher is not None
        except ImportError as e:
            pytest.fail(f"Failed to import orchestrator.file_watcher: {e}")

    def test_import_file_type_detector(self):
        """Test that orchestrator.file_type_detector module can be imported."""
        try:
            from orchestrator.file_type_detector import FileTypeDetector

            assert FileTypeDetector is not None
        except ImportError as e:
            pytest.fail(f"Failed to import orchestrator.file_type_detector: {e}")
