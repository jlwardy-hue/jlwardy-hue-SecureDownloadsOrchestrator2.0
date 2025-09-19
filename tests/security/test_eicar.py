"""
Security tests for EICAR test case validation.

This module provides tests to validate that antivirus scanning functionality
correctly identifies and handles the EICAR test file, which is a standard
test file used to verify antivirus software functionality.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from orchestrator.pipeline import UnifiedFileProcessor, SecurityScanResult


class TestEICAR:
    """Test EICAR test file handling and antivirus validation."""
    
    # EICAR standard test file - safe test pattern recognized by all AV engines
    EICAR_TEST_STRING = (
        b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
    )
    
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
                "documents": {"extensions": [".pdf", ".txt"]},
                "test": {"extensions": [".eicar"]}
            },
            "security": {
                "enable_av_scan": True,
                "fail_closed": True  # New feature: fail-closed behavior
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
    
    def test_eicar_file_creation(self):
        """Test creation of EICAR test file for validation."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.eicar') as tmp_file:
            tmp_file.write(self.EICAR_TEST_STRING)
            tmp_file.flush()
            
            # Verify file was created correctly
            assert Path(tmp_file.name).exists()
            assert Path(tmp_file.name).read_bytes() == self.EICAR_TEST_STRING
            
            # Cleanup
            os.unlink(tmp_file.name)
    
    @patch('subprocess.run')
    def test_eicar_detection_with_clamav(self, mock_subprocess, processor):
        """Test EICAR detection when ClamAV is available."""
        # Set ClamAV as available
        processor.clamav_available = True
        
        # Mock ClamAV detecting EICAR
        mock_result = MagicMock()
        mock_result.returncode = 1  # ClamAV returns 1 for infected files
        mock_result.stdout = "test.eicar: Eicar-Test-Signature FOUND"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        # Create EICAR test file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.eicar') as tmp_file:
            tmp_file.write(self.EICAR_TEST_STRING)
            tmp_file.flush()
            
            try:
                # Test security scan
                scan_result = processor._scan_file_security(tmp_file.name)
                
                # Verify threat was detected
                assert scan_result.is_clean is False
                assert "Eicar-Test-Signature" in scan_result.threat_name
                assert scan_result.scan_output is not None
                
                # Verify ClamAV was called correctly
                mock_subprocess.assert_called_once()
                call_args = mock_subprocess.call_args[0][0]
                assert "clamscan" in call_args
                assert tmp_file.name in call_args
                
            finally:
                # Cleanup
                os.unlink(tmp_file.name)


def create_eicar_test_file(file_path: str) -> None:
    """
    Create EICAR test file for CI/CD validation.
    
    This utility function creates the standard EICAR test file used by
    antivirus engines for testing purposes. The EICAR file is safe and
    contains no actual malicious code.
    
    Args:
        file_path: Path where to create the EICAR test file
    """
    eicar_content = (
        b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
    )
    
    with open(file_path, 'wb') as f:
        f.write(eicar_content)


if __name__ == "__main__":
    # Allow running this module to create EICAR test file for CI
    import sys
    if len(sys.argv) > 1:
        create_eicar_test_file(sys.argv[1])
        print(f"EICAR test file created at: {sys.argv[1]}")
    else:
        print("Usage: python test_eicar.py <output_file_path>")