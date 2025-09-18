# SecureDownloadsOrchestrator 2.0

A modular file monitoring and intelligent classification system that watches designated directories, automatically categorizes files using AI, and organizes them based on content type and security policies.

## 🏗️ Project Architecture

```
SecureDownloadsOrchestrator2.0/
├── orchestrator/              # Core package
│   ├── __init__.py           # Package initialization
│   ├── main.py               # Application entry point
│   ├── config_loader.py      # Configuration management
│   ├── logger.py             # Logging utilities
│   ├── file_watcher.py       # File monitoring (future)
│   ├── ai_classifier.py      # AI classification (future)
│   └── file_organizer.py     # File organization (future)
├── logs/                     # Application logs
├── config.yaml               # Configuration file
├── requirements.txt          # Python dependencies
└── README.md                # Project documentation
```

### Core Components

- **Config Loader**: Centralized configuration management with YAML support
- **Logger**: Structured logging with configurable levels and file output
- **File Watcher**: Real-time directory monitoring (planned)
- **AI Classifier**: GPT-powered file content analysis (planned)
- **File Organizer**: Automated file categorization and movement (planned)

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jlwardy-hue/jlwardy-hue-SecureDownloadsOrchestrator2.0.git
   cd jlwardy-hue-SecureDownloadsOrchestrator2.0
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the application:**
   Edit `config.yaml` to set your directory paths, GPT API settings, and preferences.

4. **Run the application:**
   ```bash
   python -m orchestrator.main
   ```

### Configuration

The `config.yaml` file contains all application settings:

- **Directory paths**: Source and destination directories for file monitoring
- **File categories**: Classification rules and destination mappings
- **GPT settings**: API configuration for AI classification
- **Logging**: Log levels and output preferences

## 🗺️ Development Roadmap

### Phase 1: Foundation (Current)
- [x] Project structure and packaging
- [x] Configuration management system
- [x] Logging infrastructure
- [x] Basic application entry point

### Phase 2: File Monitoring
- [ ] Real-time directory watching with `watchdog`
- [ ] File type detection and filtering
- [ ] Event-driven file processing pipeline

### Phase 3: AI Classification
- [ ] Integration with OpenAI GPT API
- [ ] Document content analysis (PDF, DOCX, images)
- [ ] Custom classification rules and categories
- [ ] Confidence scoring and manual review queue

### Phase 4: File Organization
- [ ] Automated file movement and categorization
- [ ] Duplicate detection and handling
- [ ] Archive and backup functionality
- [ ] Security scanning integration

### Phase 5: Advanced Features
- [ ] Web dashboard for monitoring and management
- [ ] Custom AI model training
- [ ] Plugin system for extensibility
- [ ] Performance optimization and scaling

## 🔧 Technology Stack

- **Python 3.8+**: Core runtime
- **watchdog**: File system monitoring
- **PyYAML**: Configuration management
- **OpenAI**: AI classification
- **python-magic**: File type detection
- **Pillow**: Image processing
- **PyPDF2**: PDF content extraction
- **python-docx**: Word document processing

## 📝 Contributing

This project is designed for modular expansion. Each component is self-contained and can be developed independently. Follow the established patterns for configuration, logging, and error handling.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.