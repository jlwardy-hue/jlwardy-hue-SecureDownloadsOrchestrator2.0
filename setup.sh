#!/bin/bash
# Quick setup script for SecureDownloadsOrchestrator 2.0
# Usage: ./setup.sh [clean|venv|verify]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BOLD}${BLUE}🚀 SecureDownloadsOrchestrator 2.0 Setup${NC}"
    echo -e "${BLUE}===========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        if ! command -v python &> /dev/null; then
            print_error "Python not found. Please install Python 3.8 or higher."
            exit 1
        else
            PYTHON_CMD="python"
        fi
    else
        PYTHON_CMD="python3"
    fi
    
    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    REQUIRED_VERSION="3.8"
    
    if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        print_error "Python $REQUIRED_VERSION or higher required. Found: $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION found"
}

main() {
    print_header
    
    # Check if we're in the right directory
    if [[ ! -f "scripts/setup.py" ]]; then
        print_error "Please run this script from the repository root directory"
        print_info "Expected to find: scripts/setup.py"
        exit 1
    fi
    
    check_python
    
    # Determine action based on argument
    ACTION=${1:-"setup"}
    
    case $ACTION in
        "clean")
            print_info "Running cleanup and setup..."
            $PYTHON_CMD scripts/setup.py --clean
            ;;
        "venv")
            print_info "Setting up virtual environment..."
            $PYTHON_CMD scripts/setup.py --venv
            print_info "To activate virtual environment, run:"
            print_info "  source venv/bin/activate"
            ;;
        "verify")
            print_info "Verifying current setup..."
            $PYTHON_CMD scripts/setup.py --verify
            ;;
        "setup"|"")
            print_info "Running full setup..."
            $PYTHON_CMD scripts/setup.py
            ;;
        *)
            echo "Usage: $0 [setup|clean|venv|verify]"
            echo ""
            echo "Commands:"
            echo "  setup   - Full setup (default)"
            echo "  clean   - Clean and setup"
            echo "  venv    - Setup with virtual environment"
            echo "  verify  - Verify current setup"
            exit 1
            ;;
    esac
    
    if [[ $? -eq 0 ]]; then
        echo ""
        print_success "Setup completed successfully!"
        
        if [[ $ACTION != "verify" ]]; then
            echo ""
            print_info "Next steps:"
            print_info "1. Edit config.yaml to set your directories"
            print_info "2. Run: $PYTHON_CMD -m orchestrator.main"
        fi
        
        echo ""
        print_info "For help, see: https://github.com/jlwardy-hue/jlwardy-hue-SecureDownloadsOrchestrator2.0#readme"
    else
        print_error "Setup failed. Check the output above for details."
        echo ""
        print_info "Common solutions:"
        print_info "• For Git conflict markers: python scripts/git_conflict_resolver.py"
        print_info "• For permission issues: Check directory write permissions"
        print_info "• For dependency issues: Try: pip install --upgrade pip"
        print_info "• For complete help: see TROUBLESHOOTING.md"
        exit 1
    fi
}

main "$@"