#!/usr/bin/env python3
"""
Compatibility entry point for SecureDownloadsOrchestrator 2.0
This redirects to the official orchestrator main module.
"""

import sys
import os

# Add the current directory to Python path to find orchestrator module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the official main function
from orchestrator.main import main

if __name__ == "__main__":
    main()