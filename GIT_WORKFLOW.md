# Git Workflow Guide

## Recommended Development Workflow for SecureDownloadsOrchestrator 2.0

This guide helps prevent common git issues and ensures smooth collaboration.

### 🚀 Getting Started

#### 1. Initial Setup
```bash
# Clone the repository
git clone https://github.com/jlwardy-hue/jlwardy-hue-SecureDownloadsOrchestrator2.0.git
cd jlwardy-hue-SecureDownloadsOrchestrator2.0

# Verify setup
python scripts/setup.py --verify

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configure Git (First Time)
```bash
# Set your name and email
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Configure line endings
git config --global core.autocrlf input  # On Linux/Mac
git config --global core.autocrlf true   # On Windows
```

### 🔀 Branch Management

#### Create Feature Branch
```bash
# Always start from latest main
git checkout main
git pull origin main

# Create and switch to feature branch
git checkout -b feature/your-feature-name

# Example branch names:
# feature/add-new-classifier
# bugfix/fix-security-scan
# docs/update-readme
```

#### Keep Branch Updated
```bash
# Regularly sync with main
git fetch origin main
git merge origin/main

# Or use rebase for cleaner history
git rebase origin/main
```

### 📝 Making Changes

#### Before You Start
```bash
# Check current status
git status

# Ensure you're on the right branch
git branch

# Pull latest changes
git pull origin main
```

#### Making Commits
```bash
# Stage specific files (preferred)
git add orchestrator/specific_file.py
git add tests/test_specific.py

# Or stage all changes (be careful)
git add .

# Check what will be committed
git diff --cached

# Commit with descriptive message
git commit -m "Add OpenAI error handling in classifier

- Add retry logic for API failures  
- Improve error messaging
- Add fallback to rule-based classification
- Update tests for error scenarios"
```

#### Good Commit Messages
```
✅ Good examples:
- "Fix path traversal vulnerability in file processor"
- "Add unit tests for AI classification error handling"
- "Update README with AI integration status"
- "Refactor classifier to improve error handling"

❌ Bad examples:
- "Fix bug"
- "Update code"
- "Changes"
- "WIP"
```

### 🔍 Before Pushing

#### Run Quality Checks
```bash
# Verify setup still works
python scripts/setup.py --verify

# Check for obvious issues
python -m orchestrator.main --help

# If available, run tests
pytest tests/test_import_orchestrator.py -v
```

#### Check Your Changes
```bash
# Review what you're about to push
git diff HEAD~1

# Check for unintended files
git status

# Ensure no secrets or sensitive data
git diff HEAD~1 | grep -i "api_key\|password\|secret"
```

### 🚀 Pushing Changes

#### Push Feature Branch
```bash
# Push to your feature branch
git push origin feature/your-feature-name

# If first push of branch
git push -u origin feature/your-feature-name
```

#### Create Pull Request
1. Go to GitHub repository
2. Click "New Pull Request"
3. Select your feature branch
4. Fill out the PR template completely
5. Link any related issues
6. Request reviews

### ⚠️ Common Issues and Solutions

#### 1. Embedded Repository Warning
```bash
# If you see: "warning: adding embedded git repository"
# Find embedded repos:
find . -name ".git" -type d

# Remove embedded .git directories:
rm -rf ./path/to/embedded/.git

# Check .gitignore includes protection:
grep -i "securedownloads" .gitignore
```

#### 2. Push Rejected (Non-Fast-Forward)
```bash
# Fetch latest changes
git fetch origin main

# Merge or rebase
git merge origin/main
# OR
git rebase origin/main

# Resolve conflicts if any, then:
git push origin feature/your-feature-name
```

#### 3. Accidentally Committed Secrets
```bash
# Remove from last commit
git reset --soft HEAD~1
git reset HEAD path/to/file/with/secret
git commit -m "Your commit message"

# Remove from history (more complex)
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch path/to/secret/file' \
--prune-empty --tag-name-filter cat -- --all
```

#### 4. Merge Conflicts
```bash
# Start merge/rebase
git merge origin/main

# If conflicts occur:
# 1. Edit conflicted files
# 2. Remove conflict markers (<<<<<<, ======, >>>>>>)
# 3. Stage resolved files
git add resolved_file.py

# Complete merge
git commit -m "Merge main into feature branch"
```

### 🛡️ Security Best Practices

#### Environment Variables
```bash
# Never commit API keys, use environment variables
export OPENAI_API_KEY="your-key-here"

# Add to .gitignore:
.env
*.key
secrets.*
```

#### Check Before Commit
```bash
# Scan for potential secrets
git diff --cached | grep -i "api_key\|password\|secret\|token"

# Use git hooks (optional)
# Create .git/hooks/pre-commit
#!/bin/bash
if git diff --cached | grep -qi "api_key\|password"; then
    echo "Warning: Potential secret detected!"
    exit 1
fi
```

### 📚 Additional Resources

- **Repository Issues**: [GitHub Issues](https://github.com/jlwardy-hue/jlwardy-hue-SecureDownloadsOrchestrator2.0/issues)
- **Troubleshooting**: See `TROUBLESHOOTING.md` section 6
- **AI Integration**: Already exists! See `README.md` AI section
- **Contributing**: See `README.md` contributing section

### 🆘 Getting Help

If you encounter git issues:

1. **Check TROUBLESHOOTING.md** section 6 for git-specific help
2. **Search existing issues** on GitHub
3. **Create a new issue** with:
   - Git command that failed
   - Error message
   - What you were trying to do
   - Your operating system

Remember: The repository already has comprehensive OpenAI integration built-in. Check existing features before adding new ones!