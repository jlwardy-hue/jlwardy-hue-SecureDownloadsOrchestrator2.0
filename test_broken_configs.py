#!/usr/bin/env python3
"""
Test script to reproduce configuration errors that users might encounter.
"""

import sys
import tempfile
import yaml
import os
from pathlib import Path

# Add repo to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

from scripts.setup import SetupManager

def test_config_scenario(name, config_content):
    """Test a specific config scenario and report results."""
    print(f"\n=== Testing: {name} ===")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        config_path = f.name
    
    try:
        # Change to temp directory to test
        old_cwd = os.getcwd()
        temp_dir = os.path.dirname(config_path)
        os.chdir(temp_dir)
        
        # Copy config to current directory as config.yaml
        with open('config.yaml', 'w') as f:
            f.write(config_content)
        
        # Test with SetupManager
        setup = SetupManager(Path(temp_dir))
        result = setup.check_configuration()
        
        if result:
            print(f"✅ {name}: Configuration PASSED")
        else:
            print(f"❌ {name}: Configuration FAILED")
            print(f"   Issues: {setup.issues}")
        
    except Exception as e:
        print(f"❌ {name}: Exception occurred: {e}")
    finally:
        os.chdir(old_cwd)
        os.unlink(config_path)
        temp_config = os.path.join(temp_dir, 'config.yaml')
        if os.path.exists(temp_config):
            os.unlink(temp_config)

# Test scenarios that could cause the error
test_scenarios = [
    # Scenario 1: Missing directories section entirely
    ("Missing directories section", """
categories:
  documents:
    extensions: [".pdf", ".doc"]
    destination: "documents"

logging:
  console:
    enabled: true
    level: "INFO"

application:
  name: "SecureDownloadsOrchestrator"
  version: "2.0"
"""),
    
    # Scenario 2: Empty directories section
    ("Empty directories section", """
directories:

categories:
  documents:
    extensions: [".pdf", ".doc"]
    destination: "documents"

logging:
  console:
    enabled: true
    level: "INFO"

application:
  name: "SecureDownloadsOrchestrator"
  version: "2.0"
"""),
    
    # Scenario 3: Missing source
    ("Missing source directory", """
directories:
  destination: "/tmp/test_dest"

categories:
  documents:
    extensions: [".pdf", ".doc"]
    destination: "documents"

logging:
  console:
    enabled: true
    level: "INFO"

application:
  name: "SecureDownloadsOrchestrator"
  version: "2.0"
"""),
    
    # Scenario 4: Missing destination
    ("Missing destination directory", """
directories:
  source: "/tmp/test_watch"

categories:
  documents:
    extensions: [".pdf", ".doc"]
    destination: "documents"

logging:
  console:
    enabled: true
    level: "INFO"

application:
  name: "SecureDownloadsOrchestrator"
  version: "2.0"
"""),
    
    # Scenario 5: Empty source
    ("Empty source directory", """
directories:
  source: ""
  destination: "/tmp/test_dest"

categories:
  documents:
    extensions: [".pdf", ".doc"]
    destination: "documents"

logging:
  console:
    enabled: true
    level: "INFO"

application:
  name: "SecureDownloadsOrchestrator"
  version: "2.0"
"""),
    
    # Scenario 6: Null source
    ("Null source directory", """
directories:
  source: null
  destination: "/tmp/test_dest"

categories:
  documents:
    extensions: [".pdf", ".doc"]
    destination: "documents"

logging:
  console:
    enabled: true
    level: "INFO"

application:
  name: "SecureDownloadsOrchestrator"
  version: "2.0"
"""),
    
    # Scenario 7: Valid config (should pass)
    ("Valid configuration", """
directories:
  source: "/tmp/test_watch"
  destination: "/tmp/test_dest"

categories:
  documents:
    extensions: [".pdf", ".doc"]
    destination: "documents"

logging:
  console:
    enabled: true
    level: "INFO"

application:
  name: "SecureDownloadsOrchestrator"
  version: "2.0"
"""),
]

if __name__ == "__main__":
    print("Testing various configuration scenarios that could cause errors...")
    
    for name, config_content in test_scenarios:
        test_config_scenario(name, config_content)
    
    print("\n" + "="*60)
    print("TEST SUMMARY:")
    print("This script demonstrates the various ways config.yaml can be")
    print("broken to cause the 'Config missing source or destination directory' error.")