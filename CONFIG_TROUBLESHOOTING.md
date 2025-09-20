# Configuration Troubleshooting Guide

This guide helps you resolve the "Config missing source or destination directory" error and other configuration issues.

## Quick Fix

If you see the error "Config missing source or destination directory", the most common causes are:

### 1. Missing `directories` section entirely

Your `config.yaml` is missing the directories configuration. Add this:

```yaml
directories:
  source: "/path/to/source/directory"      # Directory to monitor
  destination: "/path/to/destination"      # Where to organize files
```

### 2. Empty or missing `source` or `destination`

Check that both `source` and `destination` are properly specified:

```yaml
# ❌ Wrong - empty values
directories:
  source: ""
  destination: 

# ❌ Wrong - missing keys  
directories:
  # source is missing
  destination: "/tmp/test_dest"

# ✅ Correct
directories:
  source: "/tmp/test_watch"
  destination: "/tmp/test_dest"
```

### 3. Invalid YAML syntax

Common YAML syntax errors that break configuration loading:

```yaml
# ❌ Wrong - missing colon
directories
  source: "/tmp/test_watch"

# ❌ Wrong - inconsistent indentation
directories:
  source: "/tmp/test_watch"
   destination: "/tmp/test_dest"  # Extra space

# ❌ Wrong - missing space after colon
directories:
  source:"/tmp/test_watch"

# ✅ Correct
directories:
  source: "/tmp/test_watch"
  destination: "/tmp/test_dest"
```

## Validation Tools

### 1. Use the Configuration Validator

Run the built-in configuration validator to check your config:

```bash
python scripts/validate_config.py
```

This will provide detailed error messages and suggestions for fixing issues.

### 2. Use Setup Verification

Run the setup verification to check your entire environment:

```bash
python scripts/setup.py --verify
```

### 3. Manual YAML Validation

Check for YAML syntax errors:

```bash
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

## Example Working Configuration

Here's a minimal working `config.yaml`:

```yaml
directories:
  source: "/tmp/test_watch"        # For testing
  destination: "/tmp/test_dest"    # For testing
  # OR for real use:
  # source: "/home/user/Downloads"
  # destination: "/home/user/Organized"

categories:
  documents:
    extensions: [".pdf", ".doc", ".docx", ".txt"]
    destination: "documents"
  images:
    extensions: [".jpg", ".jpeg", ".png", ".gif"]
    destination: "images"

logging:
  console:
    enabled: true
    level: "INFO"
  file:
    enabled: false

application:
  name: "SecureDownloadsOrchestrator"
  version: "2.0"
  startup:
    validate_config: true
    create_missing_dirs: true
```

## Common Error Scenarios

### Error: "Config missing sections: directories"

**Cause**: The `directories` section is completely missing from your config.yaml.

**Fix**: Add the directories section:
```yaml
directories:
  source: "/path/to/source"
  destination: "/path/to/destination"
```

### Error: "Missing 'source' directory in directories section"

**Cause**: The directories section exists but is missing the `source` key.

**Fix**: Add the source directory:
```yaml
directories:
  source: "/tmp/test_watch"        # Add this line
  destination: "/tmp/test_dest"
```

### Error: "The 'source' directory is empty or null"

**Cause**: The source key exists but has an empty or null value.

**Fix**: Provide a valid path:
```yaml
directories:
  source: "/tmp/test_watch"        # Was: source: "" or source: null
  destination: "/tmp/test_dest"
```

### Error: "Configuration error: 'NoneType' object has no attribute 'get'"

**Cause**: The YAML file is empty or contains only comments.

**Fix**: Add a complete configuration or check for YAML syntax errors.

## Path Configuration Tips

### Use Absolute Paths

Always use absolute paths for better reliability:

```yaml
# ✅ Good - absolute paths
directories:
  source: "/home/user/Downloads"
  destination: "/home/user/Organized"

# ⚠️ Risky - relative paths may cause issues
directories:
  source: "./incoming"
  destination: "./organized"
```

### Test with Simple Paths First

For initial testing, use simple temporary directories:

```yaml
directories:
  source: "/tmp/test_watch"
  destination: "/tmp/test_dest"
```

### Ensure Directories Exist or Can Be Created

The application will try to create directories, but ensure the parent directories exist and you have write permissions.

## Getting Help

1. **Run the validator**: `python scripts/validate_config.py`
2. **Check the full setup**: `python scripts/setup.py --verify`
3. **Validate YAML syntax**: `python -c "import yaml; yaml.safe_load(open('config.yaml'))"`
4. **Check the troubleshooting guide**: See `TROUBLESHOOTING.md`
5. **Review examples**: Look at working configurations in the repository

## Validation Checklist

Before running the application, ensure:

- [ ] `config.yaml` file exists in the project root
- [ ] All required sections are present: `directories`, `categories`, `logging`, `application`
- [ ] `source` directory is specified and not empty
- [ ] `destination` directory is specified and not empty  
- [ ] Source and destination are different paths
- [ ] YAML syntax is valid (no syntax errors)
- [ ] File extensions in categories are properly formatted as lists
- [ ] All paths use forward slashes or proper OS path separators

Run `python scripts/validate_config.py` to automatically check all these items.