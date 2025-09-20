#!/usr/bin/env python3
"""
Configuration Validator for SecureDownloadsOrchestrator 2.0

This script helps users validate and fix their config.yaml file.
Run this script to diagnose and resolve configuration issues.

Usage:
    python scripts/validate_config.py [config_file]
    
If no config file is specified, it will check config.yaml in the current directory.
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional


class ConfigValidator:
    """Validates SecureDownloadsOrchestrator configuration files."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
    
    def validate_config_file(self, config_path: str) -> Dict[str, Any]:
        """Load and validate a configuration file."""
        config_file = Path(config_path)
        
        if not config_file.exists():
            self.errors.append(f"Configuration file not found: {config_path}")
            self._suggest_config_creation()
            return {}
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            if config is None:
                self.errors.append("Configuration file is empty or contains only comments")
                self._suggest_basic_config()
                return {}
                
            return config
            
        except yaml.YAMLError as e:
            self.errors.append(f"YAML syntax error: {e}")
            self._suggest_yaml_fixes()
            return {}
        except Exception as e:
            self.errors.append(f"Error reading configuration file: {e}")
            return {}
    
    def validate_structure(self, config: Dict[str, Any]) -> bool:
        """Validate the overall structure of the configuration."""
        if not isinstance(config, dict):
            self.errors.append("Configuration must be a dictionary/object")
            return False
        
        # Check required sections
        required_sections = ["directories", "categories", "logging", "application"]
        missing_sections = [section for section in required_sections if section not in config]
        
        if missing_sections:
            for section in missing_sections:
                self.errors.append(f"Missing required section: {section}")
            self._suggest_missing_sections(missing_sections)
            return False
        
        return True
    
    def validate_directories(self, config: Dict[str, Any]) -> bool:
        """Validate the directories configuration section."""
        directories = config.get("directories", {})
        is_valid = True
        
        if not directories:
            self.errors.append("The 'directories' section is empty or missing")
            self._suggest_directories_config()
            return False
        
        # Check source directory
        source = directories.get("source")
        if not source:
            if "source" not in directories:
                self.errors.append("Missing 'source' directory configuration")
            else:
                self.errors.append("Source directory is empty or null")
            is_valid = False
        elif not isinstance(source, str):
            self.errors.append(f"Source directory must be a string, got {type(source).__name__}")
            is_valid = False
        else:
            # Check if path looks reasonable
            if not source.strip():
                self.errors.append("Source directory is empty string")
                is_valid = False
            elif len(source) < 2:
                self.warnings.append("Source directory path seems very short")
        
        # Check destination directory
        destination = directories.get("destination")
        if not destination:
            if "destination" not in directories:
                self.errors.append("Missing 'destination' directory configuration")
            else:
                self.errors.append("Destination directory is empty or null")
            is_valid = False
        elif not isinstance(destination, str):
            self.errors.append(f"Destination directory must be a string, got {type(destination).__name__}")
            is_valid = False
        else:
            # Check if path looks reasonable
            if not destination.strip():
                self.errors.append("Destination directory is empty string")
                is_valid = False
            elif len(destination) < 2:
                self.warnings.append("Destination directory path seems very short")
        
        # Check if source and destination are the same
        if source and destination and source == destination:
            self.errors.append("Source and destination directories cannot be the same")
            is_valid = False
        
        return is_valid
    
    def validate_categories(self, config: Dict[str, Any]) -> bool:
        """Validate the categories configuration section."""
        categories = config.get("categories", {})
        
        if not categories:
            self.warnings.append("No file categories defined")
            return True
        
        for category_name, category_config in categories.items():
            if not isinstance(category_config, dict):
                self.errors.append(f"Category '{category_name}' must be a dictionary")
                continue
            
            # Check extensions
            extensions = category_config.get("extensions", [])
            if not extensions:
                self.warnings.append(f"Category '{category_name}' has no file extensions defined")
            elif not isinstance(extensions, list):
                self.errors.append(f"Extensions for category '{category_name}' must be a list")
            
            # Check destination
            dest = category_config.get("destination")
            if not dest:
                self.warnings.append(f"Category '{category_name}' has no destination directory")
            elif not isinstance(dest, str):
                self.errors.append(f"Destination for category '{category_name}' must be a string")
        
        return True
    
    def validate_logging(self, config: Dict[str, Any]) -> bool:
        """Validate the logging configuration section."""
        logging_config = config.get("logging", {})
        
        if not logging_config:
            self.warnings.append("No logging configuration defined, will use defaults")
            return True
        
        # Validate console logging
        console = logging_config.get("console", {})
        if console and not isinstance(console, dict):
            self.errors.append("Console logging configuration must be a dictionary")
        
        # Validate file logging  
        file_config = logging_config.get("file", {})
        if file_config and not isinstance(file_config, dict):
            self.errors.append("File logging configuration must be a dictionary")
        
        return True
    
    def validate_application(self, config: Dict[str, Any]) -> bool:
        """Validate the application configuration section."""
        app_config = config.get("application", {})
        
        if not app_config:
            self.errors.append("Application configuration section is missing")
            return False
        
        # Check required application fields
        required_fields = ["name", "version"]
        for field in required_fields:
            if field not in app_config:
                self.warnings.append(f"Application {field} not specified")
        
        return True
    
    def _suggest_config_creation(self):
        """Suggest creating a basic configuration file."""
        self.suggestions.append("Create a config.yaml file with this basic structure:")
        self.suggestions.append("""
directories:
  source: "/path/to/source/directory"
  destination: "/path/to/destination/directory"

categories:
  documents:
    extensions: [".pdf", ".doc", ".docx", ".txt"]
    destination: "documents"

logging:
  console:
    enabled: true
    level: "INFO"

application:
  name: "SecureDownloadsOrchestrator"
  version: "2.0"
""")
    
    def _suggest_missing_sections(self, missing_sections: List[str]):
        """Suggest adding missing configuration sections."""
        self.suggestions.append("Add these missing sections to your config.yaml:")
        for section in missing_sections:
            if section == "directories":
                self.suggestions.append("""
directories:
  source: "/path/to/source/directory"
  destination: "/path/to/destination/directory"
""")
            elif section == "categories":
                self.suggestions.append("""
categories:
  documents:
    extensions: [".pdf", ".doc", ".txt"]
    destination: "documents"
""")
            elif section == "logging":
                self.suggestions.append("""
logging:
  console:
    enabled: true
    level: "INFO"
""")
            elif section == "application":
                self.suggestions.append("""
application:
  name: "SecureDownloadsOrchestrator"
  version: "2.0"
""")
    
    def _suggest_directories_config(self):
        """Suggest proper directories configuration."""
        self.suggestions.append("Add a directories section like this:")
        self.suggestions.append("""
directories:
  source: "/tmp/test_watch"        # Directory to monitor for new files
  destination: "/tmp/test_dest"     # Where to organize files

# Or for real use:
# directories:
#   source: "/home/user/Downloads"
#   destination: "/home/user/Organized"
""")
    
    def _suggest_yaml_fixes(self):
        """Suggest common YAML syntax fixes."""
        self.suggestions.append("Check for these common YAML syntax issues:")
        self.suggestions.append("• Make sure all keys have colons followed by spaces")
        self.suggestions.append("• Use consistent indentation (spaces, not tabs)")
        self.suggestions.append("• Check for unclosed quotes or brackets")
        self.suggestions.append("• Ensure list items start with '- '")
        self.suggestions.append("\nValidate YAML syntax with:")
        self.suggestions.append("python -c \"import yaml; yaml.safe_load(open('config.yaml'))\"")
    
    def _suggest_basic_config(self):
        """Suggest creating a basic configuration."""
        self.suggestions.append("Your config.yaml file appears to be empty.")
        self.suggestions.append("Here's a minimal working configuration:")
        self.suggestions.append("""
directories:
  source: "/tmp/test_watch"
  destination: "/tmp/test_dest"

categories:
  documents:
    extensions: [".pdf", ".txt"]
    destination: "documents"

logging:
  console:
    enabled: true
    level: "INFO"

application:
  name: "SecureDownloadsOrchestrator"
  version: "2.0"
""")
    
    def validate(self, config_path: str) -> bool:
        """Perform complete validation of a configuration file."""
        print(f"🔍 Validating configuration file: {config_path}")
        print("=" * 60)
        
        # Reset state
        self.errors.clear()
        self.warnings.clear()
        self.suggestions.clear()
        
        # Load and parse the config file
        config = self.validate_config_file(config_path)
        if not config:
            self._print_results()
            return False
        
        # Validate structure and sections
        if not self.validate_structure(config):
            self._print_results()
            return False
        
        # Validate individual sections
        self.validate_directories(config)
        self.validate_categories(config)
        self.validate_logging(config)
        self.validate_application(config)
        
        # Print results
        self._print_results()
        
        return len(self.errors) == 0
    
    def _print_results(self):
        """Print validation results with formatting."""
        # Print errors
        if self.errors:
            print("\n❌ ERRORS FOUND:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        # Print warnings
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        # Print suggestions
        if self.suggestions:
            print("\n💡 SUGGESTIONS:")
            for suggestion in self.suggestions:
                if suggestion.startswith(("directories:", "categories:", "logging:", "application:")):
                    print(f"\n{suggestion}")
                else:
                    print(f"   {suggestion}")
        
        # Print summary
        print("\n" + "=" * 60)
        if not self.errors and not self.warnings:
            print("✅ Configuration is valid!")
        elif not self.errors:
            print("✅ Configuration is valid (with warnings)")
        else:
            print("❌ Configuration has errors that need to be fixed")
            print("\nAfter fixing the errors, run this script again to validate.")


def main():
    """Main entry point for the configuration validator."""
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "config.yaml"
    
    validator = ConfigValidator()
    is_valid = validator.validate(config_path)
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()