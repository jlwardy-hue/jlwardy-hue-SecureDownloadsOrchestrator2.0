#!/usr/bin/env python3
"""
Compatibility entry point for SecureDownloadsOrchestrator 2.0
This redirects to the official orchestrator main module.
"""

import os
import sys

# Add the current directory to Python path to find orchestrator module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main_wrapper():
    """Wrapper to avoid module-level import issues."""
    from orchestrator.main import main
    main()


if __name__ == "__main__":
    main_wrapper()
