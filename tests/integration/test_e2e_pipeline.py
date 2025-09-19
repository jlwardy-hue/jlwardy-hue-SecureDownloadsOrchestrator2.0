"""
End-to-end integration tests for SecureDownloadsOrchestrator 2.0.

This module provides comprehensive integration tests that validate the complete
file processing pipeline from file detection through final organization.
"""

import os
import time
import tempfile
import zipfile
import threading
from pathlib import Path
import pytest
import yaml

from orchestrator.main import create_unified_processor
from orchestrator.config_loader import load_config


class TestEndToEndPipeline:
    """End-to-end integration tests for the complete pipeline."""
    
    @pytest.fixture
    def integration_config(self):
        """Create integration test configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test directories
            source_dir = temp_path / "source"
            dest_dir = temp_path / "destination"
            quarantine_dir = temp_path / "quarantine"
            
            source_dir.mkdir()
            dest_dir.mkdir()
            quarantine_dir.mkdir()
            
            config = {
                "app": {
                    "name": "SecureDownloadsOrchestrator",
                    "version": "2.0"
                },
                "directories": {
                    "source": str(source_dir),
                    "destination": str(dest_dir),
                    "quarantine": str(quarantine_dir)
                },
                "categories": {
                    "documents": {
                        "extensions": [".pdf", ".doc", ".docx", ".txt"],
                        "destination": "documents"
                    },
                    "images": {
                        "extensions": [".jpg", ".jpeg", ".png", ".gif"],
                        "destination": "images"
                    },
                    "archive": {
                        "extensions": [".zip", ".tar", ".tar.gz"],
                        "destination": "archives"
                    }
                },
                "security": {
                    "fail_closed": False,  # Use fail-open for integration tests
                    "archive_limits": {
                        "max_files": 50,
                        "max_total_size": 10 * 1024 * 1024,  # 10MB
                        "max_depth": 5,
                        "max_file_size": 5 * 1024 * 1024  # 5MB
                    }
                },
                "processing": {
                    "enable_security_scan": True,
                    "enable_ocr": False,  # Disable OCR for faster tests
                    "enable_archive_extraction": True
                },
                "atomic_move": {
                    "enabled": True,
                    "duration_seconds": 1,  # Short duration for tests
                    "check_interval": 0.2
                },
                "logging": {
                    "console": {"enabled": True, "level": "INFO"},
                    "file": {"enabled": False}
                }
            }
            
            yield config, source_dir, dest_dir, quarantine_dir
    
    def test_simple_file_processing(self, integration_config):
        """Test processing of simple files through the complete pipeline."""
        config, source_dir, dest_dir, quarantine_dir = integration_config
        
        # Create processor
        processor = create_unified_processor(config)
        
        # Create test files
        test_files = {
            "document.txt": "This is a test document",
            "image.jpg": b"fake image data",
            "test.pdf": b"fake pdf content"
        }
        
        for filename, content in test_files.items():
            test_file = source_dir / filename
            if isinstance(content, str):
                test_file.write_text(content)
            else:
                test_file.write_bytes(content)
        
        # Process each file
        results = {}
        for filename in test_files.keys():
            file_path = source_dir / filename
            result = processor.process_file(str(file_path))
            results[filename] = result
        
        # Verify processing results
        for filename, result in results.items():
            assert result.success, f"Processing failed for {filename}: {result.error}"
            assert result.final_path is not None
            assert Path(result.final_path).exists()
            
            # Verify files are categorized correctly
            if filename.endswith('.txt'):
                assert "documents" in result.final_path
            elif filename.endswith('.pdf'):
                assert "documents" in result.final_path or "pdf" in result.final_path
            elif filename.endswith('.jpg'):
                assert "images" in result.final_path
    
    def test_archive_processing_pipeline(self, integration_config):
        """Test complete archive processing pipeline."""
        config, source_dir, dest_dir, quarantine_dir = integration_config
        
        # Create processor
        processor = create_unified_processor(config)
        
        # Create a test archive with various file types
        archive_path = source_dir / "test_archive.zip"
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("document.txt", "Archive document content")
            zf.writestr("image.png", "fake image data")
            zf.writestr("nested/subdoc.pdf", "nested document")
        
        # Process the archive
        result = processor.process_file(str(archive_path))
        
        # Verify archive processing
        assert result.success, f"Archive processing failed: {result.error}"
        assert "archives" in result.final_path or "archive" in result.final_path
        
        # Verify metadata
        if hasattr(result, 'metadata') and result.metadata:
            if "extracted_files" in result.metadata:
                assert len(result.metadata["extracted_files"]) > 0
            if "file_count" in result.metadata:
                assert result.metadata["file_count"] > 0
    
    def test_security_pipeline(self, integration_config):
        """Test security features in the pipeline."""
        config, source_dir, dest_dir, quarantine_dir = integration_config
        
        # Enable fail-closed mode for security testing
        config["security"]["fail_closed"] = True
        
        # Create processor
        processor = create_unified_processor(config)
        
        # Test 1: Create EICAR test file
        eicar_content = b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
        eicar_file = source_dir / "eicar.txt"
        eicar_file.write_bytes(eicar_content)
        
        # Process EICAR file (should be quarantined)
        result = processor.process_file(str(eicar_file))
        
        # In fail-closed mode with no AV, file should be quarantined
        assert result.success, "Quarantine should be considered successful processing"
        assert not eicar_file.exists(), "EICAR file should be moved to quarantine"
        
        # Verify quarantine
        quarantine_files = list(quarantine_dir.glob("*eicar*"))
        assert len(quarantine_files) > 0, "EICAR file should be in quarantine"
        
        # Test 2: Create archive bomb (file count)
        bomb_archive = source_dir / "bomb.zip"
        with zipfile.ZipFile(bomb_archive, 'w') as zf:
            # Create more files than the limit (50)
            for i in range(60):
                zf.writestr(f"bomb_file_{i}.txt", f"content {i}")
        
        # Process archive bomb (should be quarantined)
        result = processor.process_file(str(bomb_archive))
        
        assert result.success, "Archive bomb quarantine should be successful"
        assert not bomb_archive.exists(), "Archive bomb should be moved to quarantine"
        
        # Verify quarantine
        quarantine_files = list(quarantine_dir.glob("*bomb*"))
        assert len(quarantine_files) > 0, "Archive bomb should be in quarantine"