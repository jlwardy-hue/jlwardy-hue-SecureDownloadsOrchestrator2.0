#!/usr/bin/env python3
"""
EICAR Test File Creator for CI/CD Pipeline

This script creates the standard EICAR test file for antivirus validation
in CI/CD environments. The EICAR file is a safe test pattern recognized
by all antivirus engines.
"""

import sys
import os
from pathlib import Path


def create_eicar_test_file(file_path: str) -> None:
    """Create EICAR test file at specified path."""
    # Standard EICAR test string
    eicar_content = (
        b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
    )
    
    try:
        with open(file_path, 'wb') as f:
            f.write(eicar_content)
        print(f"✓ EICAR test file created successfully: {file_path}")
        print(f"✓ File size: {len(eicar_content)} bytes")
        
        # Verify file was created correctly
        if Path(file_path).exists():
            actual_content = Path(file_path).read_bytes()
            if actual_content == eicar_content:
                print("✓ EICAR file content verified")
            else:
                print("✗ EICAR file content mismatch")
                sys.exit(1)
        else:
            print("✗ EICAR file was not created")
            sys.exit(1)
            
    except Exception as e:
        print(f"✗ Failed to create EICAR test file: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python create_eicar.py <output_file_path>")
        print("Example: python create_eicar.py /tmp/eicar_test.txt")
        sys.exit(1)
    
    output_path = sys.argv[1]
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    create_eicar_test_file(output_path)


if __name__ == "__main__":
    main()
