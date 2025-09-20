#!/usr/bin/env python3
"""
Example script demonstrating GPT-powered file classification.

This script shows how to use the new OpenAI GPT integration for enhanced
file classification in SecureDownloadsOrchestrator 2.0.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.classifier import FileClassifier, classify_file
from orchestrator.config_loader import load_config


def create_sample_files():
    """Create sample files for testing classification."""
    files = {}
    
    # Python script
    python_content = """#!/usr/bin/env python3
import requests
import json
from typing import Dict, List

def fetch_user_data(api_key: str, user_id: int) -> Dict:
    \"\"\"Fetch user data from the API.\"\"\"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(f"https://api.example.com/users/{user_id}", headers=headers)
    return response.json()

def main():
    api_key = "sk-1234567890abcdef"  # API key
    users = [1, 2, 3]
    
    for user_id in users:
        data = fetch_user_data(api_key, user_id)
        print(f"User {user_id}: {data['name']}")

if __name__ == "__main__":
    main()
"""
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(python_content)
        files["python_script"] = f.name
    
    # JSON configuration
    config_content = {
        "database": {
            "host": "db.example.com",
            "port": 5432,
            "username": "admin",
            "password": "secret123",
            "ssl": True
        },
        "api": {
            "base_url": "https://api.example.com/v1",
            "timeout": 30,
            "rate_limit": 1000
        },
        "features": {
            "caching": True,
            "logging": True,
            "metrics": True
        }
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_content, f, indent=2)
        files["json_config"] = f.name
    
    # HTML document
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Dashboard</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>User Dashboard</h1>
        <nav>
            <a href="#users">Users</a>
            <a href="#settings">Settings</a>
        </nav>
    </header>
    
    <main>
        <section id="users">
            <h2>User Management</h2>
            <div class="user-grid">
                <!-- User cards will be populated by JavaScript -->
            </div>
        </section>
    </main>
    
    <script src="app.js"></script>
</body>
</html>"""
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(html_content)
        files["html_document"] = f.name
    
    return files


def demo_rule_based_classification(sample_files):
    """Demonstrate traditional rule-based classification."""
    print("🔧 Rule-Based Classification (Traditional)")
    print("-" * 50)
    
    for file_type, filepath in sample_files.items():
        result = classify_file(filepath)
        filename = Path(filepath).name
        print(f"  📄 {filename:<20} → {result}")
    
    print()


def demo_gpt_classification(sample_files):
    """Demonstrate GPT-powered classification with mocked responses."""
    print("🤖 GPT-Powered Classification (Enhanced)")
    print("-" * 50)
    
    # Configuration for GPT classification
    config = {
        "ai_classification": {
            "enabled": True,
            "model": "gpt-3.5-turbo",
            "max_tokens": 1000,
            "temperature": 0.1,
            "supported_mime_types": [
                "text/x-script.python",
                "text/plain",
                "application/json",
                "text/html"
            ],
            "fallback_to_rule_based": True,
            "log_errors": True
        }
    }
    
    # Mock GPT responses for demonstration
    gpt_responses = {
        "python_script": {
            "category": "code",
            "subcategory": "python_script",
            "programming_language": "python",
            "summary": "API client script that fetches user data with authentication",
            "key_technologies": ["requests", "json", "typing"],
            "sensitive_data_indicators": ["api_keys", "hardcoded_credentials"],
            "confidence_score": 0.94,
            "metadata": {
                "functions": ["fetch_user_data", "main"],
                "imports": ["requests", "json", "typing"],
                "security_concerns": ["hardcoded_api_key"],
                "complexity": "medium"
            }
        },
        "json_config": {
            "category": "config",
            "subcategory": "application_config",
            "programming_language": None,
            "summary": "Application configuration with database and API settings",
            "key_technologies": ["JSON", "Database", "API"],
            "sensitive_data_indicators": ["database_credentials", "connection_strings"],
            "confidence_score": 0.89,
            "metadata": {
                "config_sections": ["database", "api", "features"],
                "has_credentials": True,
                "security_level": "high"
            }
        },
        "html_document": {
            "category": "document",
            "subcategory": "web_page",
            "programming_language": "html",
            "summary": "User dashboard web page with navigation and user management section",
            "key_technologies": ["HTML5", "CSS", "JavaScript"],
            "sensitive_data_indicators": [],
            "confidence_score": 0.91,
            "metadata": {
                "page_type": "dashboard",
                "has_navigation": True,
                "external_resources": ["styles.css", "app.js"]
            }
        }
    }
    
    # Mock OpenAI for demonstration
    with patch.dict(os.environ, {"OPENAI_API_KEY": "demo-key"}):
        with patch("orchestrator.classifier.openai.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            for file_type, filepath in sample_files.items():
                # Set up mock response
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = json.dumps(
                    gpt_responses.get(file_type, {"category": "unknown", "confidence_score": 0.5})
                )
                mock_client.chat.completions.create.return_value = mock_response
                
                # Classify with GPT
                result = classify_file(filepath, config=config)
                filename = Path(filepath).name
                
                if isinstance(result, dict):
                    print(f"  📄 {filename}")
                    print(f"     Category: {result.get('category', 'unknown')}")
                    print(f"     Subcategory: {result.get('subcategory', 'N/A')}")
                    print(f"     Language: {result.get('programming_language', 'N/A')}")
                    print(f"     Summary: {result.get('summary', 'N/A')}")
                    print(f"     Confidence: {result.get('confidence_score', 0):.2f}")
                    
                    if result.get('sensitive_data_indicators'):
                        print(f"     ⚠️  Sensitive data: {', '.join(result['sensitive_data_indicators'])}")
                    
                    if result.get('key_technologies'):
                        print(f"     🔧 Technologies: {', '.join(result['key_technologies'])}")
                    
                    print()
                else:
                    print(f"  📄 {filename:<20} → {result} (fallback)")
    
    print()


def demo_configuration_examples():
    """Show configuration examples."""
    print("⚙️ Configuration Examples")
    print("-" * 30)
    
    print("📝 Basic Configuration:")
    print("""
ai_classification:
  enabled: true
  model: "gpt-3.5-turbo"
  max_tokens: 1000
  temperature: 0.1
  fallback_to_rule_based: true
""")
    
    print("📝 Advanced Configuration:")
    print("""
ai_classification:
  enabled: true
  model: "gpt-4"
  max_tokens: 2000
  temperature: 0.1
  max_file_size_bytes: 1048576
  max_content_length: 8000
  
  supported_mime_types:
    - "text/x-python"
    - "text/x-script.python"
    - "application/json"
    - "text/html"
    - "text/css"
    - "text/javascript"
  
  log_prompts: false
  log_responses: false
  log_errors: true
  
  prompt_template: |
    Analyze this file and provide classification:
    File: {filename} ({file_extension})
    Type: {mime_type}
    Content: {file_content}
    
    Respond with JSON containing category, summary, and confidence_score.
""")


def demo_usage_patterns():
    """Show different usage patterns."""
    print("💡 Usage Patterns")
    print("-" * 20)
    
    print("""
1. Basic File Classification:
   ```python
   from orchestrator.classifier import classify_file
   
   result = classify_file("/path/to/file.py", config=config)
   if isinstance(result, dict):
       print(f"GPT: {result['category']} - {result['summary']}")
   else:
       print(f"Rule-based: {result}")
   ```

2. Batch Processing:
   ```python
   from orchestrator.classifier import FileClassifier
   
   classifier = FileClassifier(config=config)
   for file_path in file_list:
       result = classifier.classify_file(file_path)
       process_result(result)
   ```

3. Conditional GPT Usage:
   ```python
   if file_size < MAX_SIZE and is_text_file(file_path):
       # Use GPT for detailed analysis
       result = classify_file(file_path, config=gpt_config)
   else:
       # Use rule-based for large/binary files
       result = classify_file(file_path)
   ```
""")


def main():
    """Run the demonstration."""
    print("🚀 SecureDownloadsOrchestrator 2.0")
    print("   OpenAI GPT Classification Demo")
    print("=" * 50)
    print()
    
    # Create sample files
    print("📁 Creating sample files...")
    sample_files = create_sample_files()
    print(f"   Created {len(sample_files)} sample files")
    print()
    
    try:
        # Demonstrate rule-based classification
        demo_rule_based_classification(sample_files)
        
        # Demonstrate GPT classification
        demo_gpt_classification(sample_files)
        
        # Show configuration examples
        demo_configuration_examples()
        
        # Show usage patterns
        demo_usage_patterns()
        
        print("✨ Demo completed successfully!")
        print()
        print("To use GPT classification in your environment:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Enable ai_classification in config.yaml")
        print("3. Customize prompt template as needed")
        print("4. See docs/gpt_classification_guide.md for details")
        
    finally:
        # Clean up sample files
        for filepath in sample_files.values():
            try:
                os.unlink(filepath)
            except OSError:
                pass


if __name__ == "__main__":
    main()