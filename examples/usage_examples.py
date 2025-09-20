#!/usr/bin/env python3
"""
Usage Examples for Enhanced AI Multi-Skill File Classification

This file demonstrates how to use the new multi-skill AI functionality
in SecureDownloadsOrchestrator 2.0.

Requirements:
- Set OPENAI_API_KEY environment variable
- Enable AI classification in config.yaml
- Configure desired AI skills in ai_classification.skills section
"""

import os
import sys
from pathlib import Path

# Add the project to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.classifier import FileClassifier, analyze_file_with_ai
from orchestrator.config_loader import load_config


def example_basic_classification():
    """Example 1: Basic file classification (traditional + AI enhanced)"""
    print("Example 1: Basic File Classification")
    print("=" * 40)
    
    # Load configuration
    config = load_config("config.yaml")
    
    # Create a classifier instance
    classifier = FileClassifier(config)
    
    # Classify a Python file
    python_file = "examples/sample_script.py"
    if os.path.exists(python_file):
        category = classifier.classify_file(python_file)
        print(f"Classification: {python_file} -> {category}")
    else:
        print("Note: Create examples/sample_script.py to test this example")
    
    print()


def example_multi_skill_analysis():
    """Example 2: Comprehensive AI analysis with multiple skills"""
    print("Example 2: Multi-Skill AI Analysis")
    print("=" * 40)
    
    # Load configuration and enable multiple skills
    config = load_config("config.yaml")
    
    # Enable AI classification in processing settings
    config["processing"]["enable_ai_classification"] = True
    
    # Enable additional AI skills for this example
    ai_skills = config["ai_classification"]["skills"]
    ai_skills["summarization"]["enabled"] = True
    ai_skills["sensitive_detection"]["enabled"] = True
    ai_skills["metadata_extraction"]["enabled"] = True
    
    # Create classifier
    classifier = FileClassifier(config)
    
    # Analyze a document with all skills
    document_file = "examples/sample_document.txt"
    if os.path.exists(document_file):
        results = classifier.analyze_file_with_ai(document_file)
        
        print(f"Comprehensive analysis of: {document_file}")
        for skill, result in results.items():
            print(f"\n{skill.upper()}:")
            if "error" in result:
                print(f"  Error: {result['error']}")
            else:
                for key, value in result.items():
                    print(f"  {key}: {value}")
    else:
        print("Note: Create examples/sample_document.txt to test this example")
    
    print()


def example_specific_skills():
    """Example 3: Using specific AI skills selectively"""
    print("Example 3: Selective AI Skill Usage")
    print("=" * 40)
    
    config = load_config("config.yaml")
    
    # Enable AI classification
    config["processing"]["enable_ai_classification"] = True
    
    test_file = "examples/test_code.py"
    if os.path.exists(test_file):
        # Use only classification and summarization
        results = analyze_file_with_ai(
            test_file, 
            skills=["classification", "summarization"],
            config=config
        )
        
        print(f"Selective analysis of: {test_file}")
        print(f"Requested skills: classification, summarization")
        print(f"Results received: {list(results.keys())}")
        
        # Display classification result
        if "classification" in results:
            classification = results["classification"]
            print(f"\nClassification:")
            print(f"  Category: {classification.get('category', 'unknown')}")
            print(f"  Confidence: {classification.get('confidence', 'unknown')}")
            print(f"  Reasoning: {classification.get('reasoning', 'N/A')}")
    else:
        print("Note: Create examples/test_code.py to test this example")
    
    print()


def example_configuration_customization():
    """Example 4: Customizing AI configuration for specific use cases"""
    print("Example 4: Configuration Customization")
    print("=" * 40)
    
    config = load_config("config.yaml")
    
    # Customize AI settings for this session
    ai_config = config["ai_classification"]
    
    # Use a different model for higher accuracy
    ai_config["model"] = "gpt-4"
    
    # Increase timeout for complex analysis
    ai_config["timeout"] = 60
    
    # Customize skill parameters
    classification_skill = ai_config["skills"]["classification"]
    classification_skill["max_tokens"] = 300  # More detailed responses
    classification_skill["temperature"] = 0.0  # More deterministic
    
    print("Customized configuration:")
    print(f"  Model: {ai_config['model']}")
    print(f"  Timeout: {ai_config['timeout']}s")
    print(f"  Classification max_tokens: {classification_skill['max_tokens']}")
    print(f"  Classification temperature: {classification_skill['temperature']}")
    
    # Use customized configuration
    classifier = FileClassifier(config)
    print(f"  AI enabled: {classifier._ai_enabled}")
    
    print()


def example_error_handling():
    """Example 5: Proper error handling and logging"""
    print("Example 5: Error Handling and Logging")
    print("=" * 40)
    
    import logging
    
    # Set up detailed logging
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    logger = logging.getLogger("example")
    
    config = load_config("config.yaml")
    
    # Create classifier with custom logger
    classifier = FileClassifier(config, logger)
    
    # Try to analyze a non-existent file
    non_existent_file = "non_existent_file.txt"
    results = classifier.analyze_file_with_ai(non_existent_file)
    
    print(f"Analysis of non-existent file: {results}")
    
    # Try to classify a binary file (should handle gracefully)
    binary_file = "examples/sample_image.jpg"
    if os.path.exists(binary_file):
        results = classifier.analyze_file_with_ai(binary_file)
        print(f"Analysis of binary file: {list(results.keys()) if results else 'No results'}")
    else:
        print("Note: Create examples/sample_image.jpg to test binary file handling")
    
    print()


def create_sample_files():
    """Helper function to create sample files for testing"""
    examples_dir = Path("examples")
    examples_dir.mkdir(exist_ok=True)
    
    # Create sample Python script
    sample_script = examples_dir / "sample_script.py"
    if not sample_script.exists():
        sample_script.write_text('''#!/usr/bin/env python3
"""
Sample Python script for AI classification testing.
"""

def fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    """Main function to demonstrate Fibonacci calculation."""
    for i in range(10):
        print(f"F({i}) = {fibonacci(i)}")

if __name__ == "__main__":
    main()
''')
    
    # Create sample document
    sample_doc = examples_dir / "sample_document.txt"
    if not sample_doc.exists():
        sample_doc.write_text('''Project Proposal: AI-Enhanced File Management System

Overview:
This document outlines the development of an advanced file management system
that leverages artificial intelligence to automatically classify, organize,
and analyze files based on their content and metadata.

Objectives:
1. Implement intelligent file classification using machine learning
2. Provide automated content summarization capabilities
3. Detect sensitive information in documents
4. Extract and index metadata for enhanced search functionality

Technical Requirements:
- Python 3.8+ runtime environment
- OpenAI API integration for natural language processing
- Support for multiple file formats (PDF, DOC, TXT, images)
- Configurable security scanning and quarantine capabilities

Timeline:
Phase 1: Core classification engine (4 weeks)
Phase 2: AI integration and testing (3 weeks)  
Phase 3: Security features and deployment (2 weeks)

Expected Benefits:
- Reduced manual file organization effort by 80%
- Improved document searchability and retrieval
- Enhanced security through automatic sensitive data detection
- Streamlined workflow for content management teams
''')
    
    # Create sample test code
    test_code = examples_dir / "test_code.py"
    if not test_code.exists():
        test_code.write_text('''import unittest
from datetime import datetime

class TestStringMethods(unittest.TestCase):
    """Test cases for string manipulation functions."""
    
    def test_upper(self):
        """Test string upper() method."""
        self.assertEqual('foo'.upper(), 'FOO')
        
    def test_isupper(self):
        """Test string isupper() method."""
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())
        
    def test_split(self):
        """Test string split() method."""
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        
    def setUp(self):
        """Set up test fixtures."""
        self.test_string = "Hello, World!"
        self.timestamp = datetime.now()

if __name__ == '__main__':
    unittest.main()
''')
    
    print(f"Sample files created in {examples_dir}/")


def main():
    """Run all examples"""
    print("AI Multi-Skill File Classification Examples")
    print("=" * 50)
    print()
    
    # Create sample files if they don't exist
    create_sample_files()
    print()
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Note: OPENAI_API_KEY environment variable not set.")
        print("   AI features will be disabled, but examples will still run.")
        print()
    
    # Run examples
    example_basic_classification()
    example_multi_skill_analysis()
    example_specific_skills()
    example_configuration_customization()
    example_error_handling()
    
    print("All examples completed!")
    print()
    print("Next steps:")
    print("1. Set OPENAI_API_KEY environment variable to test AI features")
    print("2. Enable AI skills in config.yaml")
    print("3. Run: python examples/usage_examples.py")


if __name__ == "__main__":
    main()