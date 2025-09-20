# GPT Classification Integration Guide

This document provides a comprehensive guide for configuring and using the OpenAI GPT-powered file classification feature in SecureDownloadsOrchestrator 2.0.

## Overview

The GPT classification feature extends the traditional rule-based file classification with AI-powered content analysis. When enabled, the system can:

- Analyze file content to provide intelligent classification
- Extract metadata and summaries from files
- Detect sensitive information patterns
- Identify programming languages and technologies
- Provide confidence scores for classifications

## Configuration

### Prerequisites

1. **OpenAI API Key**: Set the `OPENAI_API_KEY` environment variable
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

2. **OpenAI Package**: Install the OpenAI Python package
   ```bash
   pip install openai>=1.0.0
   ```

### Basic Configuration

Add the following to your `config.yaml`:

```yaml
# Enable AI-powered file classification
ai_classification:
  enabled: true
  
  # OpenAI API configuration
  model: "gpt-3.5-turbo"     # GPT model to use
  max_tokens: 1000           # Maximum tokens in response
  temperature: 0.1           # Lower = more consistent results
  
  # File processing limits
  max_file_size_bytes: 1048576  # 1MB max file size
  max_content_length: 8000      # Max characters to send to GPT
  
  # Fallback behavior
  fallback_to_rule_based: true  # Use rule-based classification if GPT fails
```

### Advanced Configuration

```yaml
ai_classification:
  enabled: true
  model: "gpt-4"            # Use more advanced model
  max_tokens: 2000
  temperature: 0.1
  
  # File type support
  supported_mime_types:
    - "text/plain"
    - "text/x-python"
    - "text/x-script.python"
    - "application/json"
    - "text/html"
    - "text/css"
    - "text/javascript"
    - "application/javascript"
    - "text/markdown"
    - "application/xml"
    - "text/xml"
    - "text/csv"
  
  # Debugging options
  log_prompts: false        # Log full prompts (for debugging)
  log_responses: false      # Log full GPT responses (for debugging)
  log_errors: true          # Always log errors
  
  # Custom prompt template (see below for details)
  prompt_template: |
    Custom prompt template here...
```

## Prompt Template Customization

The prompt template supports the following placeholders:

- `{filename}` - Name of the file
- `{file_extension}` - File extension (e.g., ".py")
- `{mime_type}` - MIME type detected by the system
- `{file_size}` - File size in bytes
- `{file_content}` - Actual file content (truncated if necessary)
- `{max_content_length}` - Maximum content length setting

### Example Custom Prompt

```yaml
ai_classification:
  prompt_template: |
    Analyze this code file and provide detailed classification:
    
    File: {filename} ({file_extension})
    Type: {mime_type}
    Size: {file_size} bytes
    
    Content:
    ```
    {file_content}
    ```
    
    Provide JSON response with:
    - category: Primary category (code, document, config, etc.)
    - subcategory: Specific type (python_script, react_component, etc.)
    - programming_language: Language if applicable
    - summary: Brief description
    - technologies: List of frameworks/libraries detected
    - security_concerns: Any potential security issues
    - confidence_score: 0-1 confidence level
    
    Respond only with valid JSON.
```

## Response Format

GPT classification returns a detailed dictionary instead of a simple string:

```python
{
    "category": "code",
    "subcategory": "python_script", 
    "programming_language": "python",
    "summary": "A web scraper that extracts product data from e-commerce sites",
    "key_technologies": ["requests", "beautifulsoup", "pandas"],
    "sensitive_data_indicators": ["api_keys", "credentials"],
    "confidence_score": 0.92,
    "metadata": {
        "functions": ["scrape_products", "save_data"],
        "imports": ["requests", "bs4", "pandas"],
        "complexity": "medium"
    },
    "source": "gpt",
    "model": "gpt-3.5-turbo",
    "filepath": "/path/to/file.py",
    "rule_based_category": "code"  # Fallback classification
}
```

## Security Considerations

### API Key Management

- **Never** store API keys in configuration files
- Use environment variables: `OPENAI_API_KEY`
- Consider using secret management systems in production
- Rotate API keys regularly

### Data Privacy

- File contents are sent to OpenAI's API
- Consider data sensitivity before enabling GPT classification
- Use file size limits to prevent large file uploads
- Review OpenAI's data usage policies

### Content Filtering

```yaml
ai_classification:
  # Only process specific file types
  supported_mime_types:
    - "text/plain"
    - "application/json"
    # Add only the MIME types you want to process
  
  # Limit file sizes
  max_file_size_bytes: 524288  # 512KB limit for sensitive environments
  max_content_length: 4000     # Shorter content for faster processing
```

## Usage Examples

### Basic Usage

```python
from orchestrator.classifier import classify_file
from orchestrator.config_loader import load_config

# Load configuration with GPT enabled
config = load_config("config.yaml")

# Classify a file
result = classify_file("/path/to/script.py", config=config)

if isinstance(result, dict):
    # GPT classification successful
    print(f"Category: {result['category']}")
    print(f"Summary: {result['summary']}")
    print(f"Confidence: {result['confidence_score']}")
else:
    # Rule-based fallback
    print(f"Category: {result}")
```

### Integration with File Processing

```python
from orchestrator.classifier import FileClassifier

# Create classifier with configuration
classifier = FileClassifier(config=config)

# Process multiple files
for filepath in file_list:
    result = classifier.classify_file(filepath)
    
    if isinstance(result, dict) and result.get("source") == "gpt":
        # Enhanced GPT classification
        handle_gpt_result(result)
    else:
        # Standard rule-based classification
        handle_standard_result(result)
```

## Troubleshooting

### Common Issues

1. **GPT classification not working**
   - Check `OPENAI_API_KEY` environment variable
   - Verify OpenAI package is installed
   - Check file MIME type is in `supported_mime_types`
   - Review file size limits

2. **API errors**
   - Check API key validity
   - Verify API quota/billing
   - Check network connectivity
   - Review OpenAI API status

3. **Unexpected results**
   - Enable debug logging: `log_prompts: true` and `log_responses: true`
   - Adjust prompt template for better results
   - Fine-tune `temperature` setting

### Debug Configuration

```yaml
ai_classification:
  enabled: true
  log_prompts: true     # Enable for debugging
  log_responses: true   # Enable for debugging
  log_errors: true
  
logging:
  console:
    level: "DEBUG"      # Enable debug logging
  file:
    enabled: true
    level: "DEBUG"
```

### Performance Optimization

1. **Reduce API calls**
   - Set appropriate file size limits
   - Filter file types carefully
   - Use caching if processing same files repeatedly

2. **Improve response time**
   - Use `gpt-3.5-turbo` for faster responses
   - Reduce `max_tokens` for shorter responses
   - Keep `max_content_length` reasonable

3. **Cost management**
   - Monitor API usage in OpenAI dashboard
   - Set file size limits to control costs
   - Use rule-based classification for simple cases

## Migration from Rule-Based Classification

### Gradual Migration

1. **Start with selective enablement**
   ```yaml
   ai_classification:
     enabled: true
     supported_mime_types:
       - "text/x-python"  # Start with just Python files
   ```

2. **Monitor and adjust**
   - Enable debug logging
   - Compare GPT vs rule-based results
   - Adjust prompt template based on results

3. **Expand gradually**
   - Add more MIME types incrementally
   - Fine-tune prompts for different file types
   - Monitor API costs and performance

### Backward Compatibility

The system maintains full backward compatibility:
- Existing code continues to work unchanged
- Rule-based classification remains as fallback
- String results for rule-based, dict results for GPT
- No breaking changes to existing APIs

## Best Practices

1. **Prompt Engineering**
   - Be specific about required output format
   - Include examples in prompts for consistency
   - Test prompts with various file types
   - Keep prompts concise but comprehensive

2. **Configuration Management**
   - Use environment-specific configurations
   - Keep sensitive settings in environment variables
   - Document custom prompt templates
   - Version control configuration changes

3. **Monitoring and Logging**
   - Monitor API usage and costs
   - Log classification decisions for audit trails
   - Set up alerts for API errors
   - Review classification accuracy regularly

4. **Security**
   - Assess data sensitivity before enabling
   - Use file size limits appropriately
   - Keep API keys secure
   - Review OpenAI's data handling policies