# Enhanced AI Multi-Skill Integration Guide

This document describes the enhanced AI capabilities in SecureDownloadsOrchestrator 2.0, including multi-skill analysis, configurable prompts, and advanced file processing.

## Overview

The enhanced AI system provides four distinct capabilities:

1. **File Classification** - Intelligent categorization with confidence scoring
2. **Content Summarization** - Automated content analysis and summary generation
3. **Sensitive Information Detection** - Security-focused content scanning
4. **Metadata Extraction** - Structured information extraction

## Configuration

### Basic AI Setup

1. **Set API Key**: Export your OpenAI API key as an environment variable:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

2. **Enable AI Processing**: In `config.yaml`, set:
   ```yaml
   processing:
     enable_ai_classification: true
   ```

3. **Configure Skills**: Enable desired AI skills:
   ```yaml
   ai_classification:
     skills:
       classification:
         enabled: true
       summarization:
         enabled: true
       sensitive_detection:
         enabled: true
       metadata_extraction:
         enabled: true
   ```

### Advanced Configuration

#### Model Settings
```yaml
ai_classification:
  provider: "openai"
  model: "gpt-3.5-turbo"  # or "gpt-4" for higher accuracy
  endpoint: "https://api.openai.com/v1"
  max_content_length: 2048
  timeout: 30
```

#### Skill-Specific Settings
Each skill can be customized individually:

```yaml
ai_classification:
  skills:
    classification:
      enabled: true
      max_tokens: 200      # Response length limit
      temperature: 0.1     # Creativity/randomness (0.0-2.0)
      prompt_template: |   # Custom prompt template
        Analyze the file content and classify it...
    
    summarization:
      enabled: true
      max_tokens: 300
      temperature: 0.3
    
    sensitive_detection:
      enabled: true
      max_tokens: 250
      temperature: 0.1
    
    metadata_extraction:
      enabled: true
      max_tokens: 400
      temperature: 0.2
```

## Usage Examples

### Basic File Classification

```python
from orchestrator.classifier import FileClassifier
from orchestrator.config_loader import load_config

# Load configuration
config = load_config("config.yaml")

# Create classifier
classifier = FileClassifier(config)

# Classify a file
category = classifier.classify_file("document.pdf")
print(f"File category: {category}")
```

### Multi-Skill Analysis

```python
from orchestrator.classifier import analyze_file_with_ai

# Analyze with all enabled skills
results = analyze_file_with_ai("document.txt", config=config)

for skill, result in results.items():
    print(f"{skill}: {result}")
```

### Selective Skill Usage

```python
# Use specific skills only
results = analyze_file_with_ai(
    "document.txt",
    skills=["classification", "summarization"],
    config=config
)
```

### Custom Configuration

```python
# Customize settings programmatically
config = load_config("config.yaml")

# Use GPT-4 for higher accuracy
config["ai_classification"]["model"] = "gpt-4"

# Increase timeout for complex documents
config["ai_classification"]["timeout"] = 60

# Create classifier with custom settings
classifier = FileClassifier(config)
```

## Response Formats

### Classification Response
```json
{
  "category": "document",
  "confidence": "high",
  "reasoning": "Contains structured text with headings and paragraphs",
  "file_type": "Text document",
  "content_type": "text"
}
```

### Summarization Response
```json
{
  "summary": "Technical documentation for file processing system",
  "key_topics": ["file management", "AI classification", "automation"],
  "content_length": "approximately 500 words",
  "language": "English",
  "document_type": "technical documentation"
}
```

### Sensitive Detection Response
```json
{
  "has_sensitive_info": true,
  "sensitivity_level": "medium",
  "detected_types": ["email", "phone"],
  "risk_assessment": "Contains contact information",
  "recommended_action": "Review before sharing"
}
```

### Metadata Extraction Response
```json
{
  "title": "System Architecture Document",
  "author": "Development Team",
  "creation_date": "2024-01-15",
  "keywords": ["architecture", "system", "design"],
  "description": "Comprehensive system design documentation",
  "structure": "Well-organized with clear sections",
  "quality": "High - detailed and professional"
}
```

## Error Handling

The system provides comprehensive error handling:

### Common Scenarios

1. **Missing API Key**: AI features are disabled, traditional classification continues
2. **Invalid JSON Response**: Falls back to legacy classification
3. **API Rate Limits**: Logged as errors, processing continues without AI
4. **Network Timeouts**: Configurable timeout with graceful degradation
5. **Binary Files**: OCR hooks for image/PDF processing (if enabled)

### Logging

AI operations are logged with different levels:

- **INFO**: Successful operations, classifications
- **DEBUG**: Request details, response times, prompt structure
- **WARNING**: Non-critical issues, fallbacks
- **ERROR**: API failures, configuration problems

Example log output:
```
INFO:classifier:OpenAI client initialized (endpoint: https://api.openai.com/v1, API key: sk-proj1234...abcd)
DEBUG:classifier:Sending AI classification request for document.txt (skill=classification, model=gpt-3.5-turbo, max_tokens=200, temp=0.1)
DEBUG:classifier:AI classification response received for document.txt (response_time=1.23s, response_length=156chars)
INFO:classifier:AI classification completed successfully for document.txt (response keys: ['category', 'confidence', 'reasoning', 'file_type', 'content_type'])
```

## Security Features

### API Key Protection
- API keys are never logged in full
- Displayed as `sk-proj1234...abcd` in logs
- Environment variable usage prevents accidental commits

### Content Sanitization
- File content is not logged by default
- Only prompt structure and response metadata are logged
- Sensitive detection results are handled carefully

### OCR Integration
- Non-text files can be processed via OCR
- Configurable per processing settings
- Graceful handling when OCR is unavailable

## Performance Considerations

### Optimization Tips

1. **Content Length**: Limit `max_content_length` for faster processing
2. **Selective Skills**: Only enable needed skills to reduce API calls
3. **Timeout Settings**: Balance accuracy vs. responsiveness
4. **Temperature**: Lower values (0.0-0.3) for consistent results

### Monitoring

The system provides performance metrics:
- Response times for each AI call
- Success/failure rates per skill
- Content processing statistics

## Troubleshooting

### Common Issues

1. **AI Not Working**
   - Check `OPENAI_API_KEY` environment variable
   - Verify `enable_ai_classification: true` in config
   - Check network connectivity to OpenAI API

2. **Poor Classification Results**
   - Increase `max_tokens` for more detailed responses
   - Try different models (gpt-4 vs gpt-3.5-turbo)
   - Adjust `temperature` for consistency

3. **Timeout Errors**
   - Increase `timeout` value in configuration
   - Reduce `max_content_length` for faster processing

4. **JSON Parsing Errors**
   - Check prompt templates for proper JSON structure
   - Verify `temperature` isn't too high (causes unpredictable output)

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now run classification with detailed logs
classifier = FileClassifier(config)
result = classifier.classify_file("test.txt")
```

## Integration Examples

See `examples/usage_examples.py` for comprehensive examples including:
- Basic classification workflow
- Multi-skill analysis pipeline
- Error handling patterns
- Configuration customization
- Performance monitoring

## API Reference

### Main Classes

- `FileClassifier`: Primary classification engine
- `analyze_file_with_ai()`: Convenience function for multi-skill analysis

### Key Methods

- `classify_file(filepath)`: Traditional + AI classification
- `analyze_file_with_ai(filepath, skills=None)`: Multi-skill analysis
- `_call_ai_skill(skill, filepath, content)`: Individual skill execution

### Configuration Structure

```yaml
ai_classification:
  provider: string
  model: string
  endpoint: string
  max_content_length: integer
  timeout: integer
  skills:
    classification:
      enabled: boolean
      prompt_template: string
      max_tokens: integer
      temperature: float
    # ... other skills
```

This enhanced AI system provides powerful, configurable file analysis capabilities while maintaining backward compatibility and robust error handling.