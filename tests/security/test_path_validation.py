"""
Security tests for path validation and sanitization.

This module tests path validation functionality to ensure protection
against path traversal attacks and unauthorized file access.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from orchestrator.pipeline import UnifiedFileProcessor, PathValidationError


class TestPathValidation:
    """Test path validation and sanitization mechanisms."""
    
    @pytest.fixture
    def processor_config(self):
        """Create processor configuration for testing."""
        return {
            "directories": {
                "source": "/tmp/test_source",
                "destination": "/tmp/test_dest",
                "quarantine": "/tmp/test_quarantine"
            },
            "categories": {
                "documents": {"extensions": [".txt", ".pdf"]}
            },
            "security": {
                "fail_closed": True
            },
            "logging": {
                "console": {"enabled": True, "level": "DEBUG"},
                "file": {"enabled": False}
            }
        }
    
    @pytest.fixture
    def processor(self, processor_config):
        """Create processor instance with test configuration."""
        processor = UnifiedFileProcessor(processor_config)
        # Ensure test directories exist
        Path(processor_config["directories"]["source"]).mkdir(parents=True, exist_ok=True)
        Path(processor_config["directories"]["destination"]).mkdir(parents=True, exist_ok=True)
        Path(processor_config["directories"]["quarantine"]).mkdir(parents=True, exist_ok=True)
        return processor
    
    def test_valid_file_path_in_source(self, processor):
        """Test that valid file paths within source directory are accepted."""
        # Create a test file in the source directory
        source_dir = Path(processor.config["directories"]["source"])
        test_file = source_dir / "valid_file.txt"
        test_file.write_text("valid content")
        
        try:
            # Should not raise any exception
            processor._validate_file_path(str(test_file))
            
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
    
    def test_path_traversal_with_double_dots(self, processor):
        """Test detection of path traversal attempts with '..'."""
        # Create a test file but try to access it with path traversal
        source_dir = Path(processor.config["directories"]["source"])
        test_file = source_dir / "test.txt"
        test_file.write_text("content")
        
        try:
            # Try path traversal
            malicious_path = str(source_dir / ".." / ".." / "etc" / "passwd")
            
            with pytest.raises(PathValidationError) as exc_info:
                processor._validate_file_path(malicious_path)
            
            assert "Path traversal detected" in str(exc_info.value)
            
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
    
    def test_path_traversal_with_tilde(self, processor):
        """Test detection of path traversal attempts with '~'."""
        with pytest.raises(PathValidationError) as exc_info:
            processor._validate_file_path("~/../../etc/passwd")
        
        assert "Path traversal detected" in str(exc_info.value)
    
    def test_nonexistent_file_rejection(self, processor):
        """Test that nonexistent files are rejected."""
        nonexistent_path = "/tmp/test_source/nonexistent_file.txt"
        
        with pytest.raises(PathValidationError) as exc_info:
            processor._validate_file_path(nonexistent_path)
        
        assert "File does not exist" in str(exc_info.value)
    
    def test_directory_path_rejection(self, processor):
        """Test that directory paths are rejected (only files allowed)."""
        source_dir = Path(processor.config["directories"]["source"])
        
        with pytest.raises(PathValidationError) as exc_info:
            processor._validate_file_path(str(source_dir))
        
        assert "Path is not a regular file" in str(exc_info.value)
    
    def test_file_outside_allowed_directories(self, processor):
        """Test that files outside allowed directories are rejected."""
        # Create a file outside both source and temp directories
        # Use /var/tmp which is not typically the same as temp directory
        outside_dir = Path("/var/tmp/test_outside")
        outside_dir.mkdir(exist_ok=True)
        outside_file = outside_dir / "outside_file.txt"
        
        try:
            outside_file.write_text("content")
            
            with pytest.raises(PathValidationError) as exc_info:
                processor._validate_file_path(str(outside_file))
            
            assert "File path outside allowed directories" in str(exc_info.value)
            
        finally:
            # Cleanup
            if outside_file.exists():
                outside_file.unlink()
            if outside_dir.exists():
                outside_dir.rmdir()
    
    def test_file_in_temp_directory_allowed(self, processor):
        """Test that files in temp directory are allowed (for archive extraction)."""
        # Create a file in temp directory
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp_file:
            tmp_file.write(b"content")
            tmp_file.flush()
            
            try:
                # Should not raise exception for temp files
                processor._validate_file_path(tmp_file.name)
                
            finally:
                # Cleanup
                os.unlink(tmp_file.name)
    
    def test_symlink_path_validation(self, processor):
        """Test handling of symbolic links."""
        source_dir = Path(processor.config["directories"]["source"])
        
        # Create a real file
        real_file = source_dir / "real_file.txt"
        real_file.write_text("real content")
        
        # Create a symlink to it
        symlink_file = source_dir / "symlink_file.txt"
        
        try:
            symlink_file.symlink_to(real_file)
            
            # Symlink within source directory should be allowed
            processor._validate_file_path(str(symlink_file))
            
        except OSError:
            # Skip if symlinks not supported
            pytest.skip("Symlinks not supported on this system")
        finally:
            # Cleanup
            if symlink_file.exists():
                symlink_file.unlink()
            if real_file.exists():
                real_file.unlink()
    
    def test_path_validation_in_process_file(self, processor):
        """Test that path validation is called during file processing."""
        # Create a file that attempts path traversal using a symlink  
        source_dir = Path(processor.config["directories"]["source"])
        
        # Create a malicious filename that looks like path traversal
        malicious_file = source_dir / "..%2F..%2F..%2Fetc%2Fpasswd"  # URL encoded
        
        try:
            # Create the file with malicious name
            malicious_file.write_text("malicious content")
            
            # This should result in quarantine due to path validation failure
            result = processor.process_file(str(malicious_file))
            
            # Processing should "succeed" (quarantine is successful)
            assert result.success is True
            
            # Original file should be moved to quarantine
            assert not malicious_file.exists()
            
            # Check that file was quarantined
            quarantine_dir = Path(processor.config["directories"]["quarantine"])
            quarantine_files = list(quarantine_dir.glob("*"))
            assert len(quarantine_files) > 0, "File should be quarantined"
            
        except OSError:
            # If we can't create file with that name, create a normal file 
            # and test with a non-existent path
            test_file = source_dir / "test.txt"
            test_file.write_text("content")
            
            try:
                # Try to process non-existent path with traversal
                result = processor.process_file("/tmp/test_source/../nonexistent.txt")
                
                # Should fail due to path validation
                assert result.success is False
                assert "Path validation failed" in result.error or "File does not exist" in result.error
                
            finally:
                if test_file.exists():
                    test_file.unlink()
        finally:
            # Cleanup quarantine
            quarantine_dir = Path(processor.config["directories"]["quarantine"])
            for file in quarantine_dir.glob("*"):
                if file.is_file():
                    file.unlink()
    
    def test_absolute_path_normalization(self, processor):
        """Test that paths are properly normalized."""
        source_dir = Path(processor.config["directories"]["source"])
        
        # Create test file
        test_file = source_dir / "test.txt"
        test_file.write_text("content")
        
        try:
            # Test with relative path elements
            relative_path = str(source_dir / "." / "test.txt")
            
            # Should normalize and validate successfully
            processor._validate_file_path(relative_path)
            
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
    
    def test_empty_or_invalid_path_strings(self, processor):
        """Test handling of empty or invalid path strings."""
        invalid_paths = ["", None, "/", "//", "..."]
        
        for invalid_path in invalid_paths:
            if invalid_path is None:
                continue
            
            with pytest.raises(PathValidationError):
                processor._validate_file_path(invalid_path)