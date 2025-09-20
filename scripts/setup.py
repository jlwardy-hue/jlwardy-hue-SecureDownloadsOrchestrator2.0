#!/usr/bin/env python3
"""
SecureDownloadsOrchestrator Setup and Verification Script

This script performs setup verification and initial configuration
for SecureDownloadsOrchestrator 2.0 after a fresh clone.

Usage:
    python scripts/setup.py [--verify] [--clean] [--venv]

Options:
    --verify    Only verify current setup without making changes
    --clean     Clean up old files and reset to fresh state
    --venv      Create and setup a virtual environment
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Color codes for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


class SetupManager:
    """Manages setup and verification of SecureDownloadsOrchestrator."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.success_items: List[str] = []

    def print_status(self, message: str, status: str = "INFO", bold: bool = False):
        """Print colored status message."""
        color_map = {
            "SUCCESS": Colors.GREEN,
            "ERROR": Colors.RED,
            "WARNING": Colors.YELLOW,
            "INFO": Colors.BLUE,
        }
        color = color_map.get(status, "")
        bold_start = Colors.BOLD if bold else ""
        bold_end = Colors.END if bold else ""
        print(f"{bold_start}{color}[{status}]{Colors.END} {message}{bold_end}")

    def check_python_version(self) -> bool:
        """Check if Python version meets requirements."""
        self.print_status("Checking Python version...", "INFO")

        if sys.version_info < (3, 8):
            self.issues.append(f"Python 3.8+ required, found {sys.version}")
            return False

        version_str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.print_status(f"Python {version_str} ✓", "SUCCESS")
        self.success_items.append(f"Python {version_str}")
        return True

    def check_required_files(self) -> bool:
        """Check that all required files are present."""
        self.print_status("Checking required files...", "INFO")

        required_files = [
            "config.yaml",
            "requirements.txt",
            "orchestrator/main.py",
            "orchestrator/__init__.py",
            "main.py",
        ]

        missing_files = []
        for file_path in required_files:
            full_path = self.repo_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)

        if missing_files:
            self.issues.append(f"Missing required files: {', '.join(missing_files)}")
            return False

        self.print_status(
            f"All {len(required_files)} required files present ✓", "SUCCESS"
        )
        self.success_items.append("Required files")
        return True

    def check_directory_structure(self) -> bool:
        """Check that required directories are present."""
        self.print_status("Checking directory structure...", "INFO")

        required_dirs = ["orchestrator", "tests", "scripts"]

        # Optional directories (warn if missing but don't fail)
        optional_dirs = [".github/workflows"]

        missing_dirs = []
        for dir_path in required_dirs:
            full_path = self.repo_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)

        missing_optional = []
        for dir_path in optional_dirs:
            full_path = self.repo_root / dir_path
            if not full_path.exists():
                missing_optional.append(dir_path)

        if missing_dirs:
            self.issues.append(
                f"Missing required directories: {', '.join(missing_dirs)}"
            )
            return False

        if missing_optional:
            self.warnings.append(
                f"Missing optional directories: {', '.join(missing_optional)}"
            )

        self.print_status(
            f"All {len(required_dirs)} required directories present ✓", "SUCCESS"
        )
        self.success_items.append("Directory structure")
        return True

    def check_dependencies(self) -> bool:
        """Check if required Python dependencies are installed."""
        self.print_status("Checking Python dependencies...", "INFO")

        try:
            with open(self.repo_root / "requirements.txt", "r") as f:
                requirements = [
                    line.strip().split(">=")[0].split("==")[0]
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]

            missing_deps = []
            for dep in requirements:
                # Handle special cases for import names
                import_name = dep.replace("-", "_")
                if dep == "python-magic":
                    import_name = "magic"
                elif dep == "PyYAML":
                    import_name = "yaml"
                elif dep == "Pillow":
                    import_name = "PIL"
                elif dep == "pdf2image":
                    import_name = "pdf2image"

                try:
                    __import__(import_name)
                except ImportError:
                    missing_deps.append(dep)

            if missing_deps:
                self.warnings.append(
                    f"Missing Python dependencies: {', '.join(missing_deps)}"
                )
                self.print_status(
                    f"Missing dependencies: {', '.join(missing_deps)}", "WARNING"
                )
                return False

            self.print_status(
                f"All {len(requirements)} Python dependencies available ✓", "SUCCESS"
            )
            self.success_items.append("Python dependencies")
            return True

        except Exception as e:
            self.issues.append(f"Error checking dependencies: {e}")
            return False

    def check_system_dependencies(self) -> bool:
        """Check optional system dependencies."""
        self.print_status("Checking optional system dependencies...", "INFO")

        optional_deps = {
            "tesseract": "tesseract --version",
            "poppler-utils": "pdftoppm -h",
        }

        missing_optional = []
        available_optional = []

        for dep_name, check_cmd in optional_deps.items():
            try:
                result = subprocess.run(
                    check_cmd.split(), capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    available_optional.append(dep_name)
                else:
                    missing_optional.append(dep_name)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                missing_optional.append(dep_name)

        if available_optional:
            self.print_status(
                f"Optional deps available: {', '.join(available_optional)} ✓", "SUCCESS"
            )

        if missing_optional:
            self.warnings.append(
                f"Optional system dependencies missing: {', '.join(missing_optional)}"
            )
            self.print_status(
                f"Optional deps missing: {', '.join(missing_optional)} (OCR/PDF features disabled)",
                "WARNING",
            )

        return True

    def check_configuration(self) -> bool:
        """Validate configuration file."""
        self.print_status("Validating configuration...", "INFO")

        try:
            # Add repo root to path for imports
            import sys

            sys.path.insert(0, str(self.repo_root))

            # Import here to avoid dependency issues during early checks
            from orchestrator.config_loader import load_config

            config = load_config("config.yaml")

            # Check required sections
            required_sections = ["directories", "categories", "logging", "application"]
            missing_sections = [s for s in required_sections if s not in config]

            if missing_sections:
                self.issues.append(
                    f"Config missing sections: {', '.join(missing_sections)}"
                )
                return False

            # Check directories configuration
            dirs = config.get("directories", {})
            if not dirs.get("source") or not dirs.get("destination"):
                self.issues.append("Config missing source or destination directory")
                return False

            self.print_status("Configuration file valid ✓", "SUCCESS")
            self.success_items.append("Configuration")
            return True

        except Exception as e:
            self.issues.append(f"Configuration error: {e}")
            return False

    def check_git_health(self) -> bool:
        """Check Git repository health for common issues."""
        self.print_status("Checking Git repository health...", "INFO")
        
        try:
            git_script = self.repo_root / "scripts" / "git_conflict_resolver.py"
            if not git_script.exists():
                self.warnings.append("Git conflict resolver script not found")
                return True  # Don't fail setup for this
            
            # Run the git health check
            result = subprocess.run(
                [sys.executable, str(git_script), "--repo-path", str(self.repo_root)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                if "repository is healthy" in result.stdout.lower():
                    self.print_status("Git repository healthy ✓", "SUCCESS")
                    self.success_items.append("Git health")
                else:
                    self.warnings.append("Git repository has warnings (see output above)")
            else:
                # Git issues detected
                if "conflict" in result.stdout.lower():
                    self.warnings.append("Git conflicts detected - use scripts/git_conflict_resolver.py to fix")
                else:
                    self.warnings.append("Git repository issues detected")
                
        except subprocess.TimeoutExpired:
            self.warnings.append("Git health check timed out")
        except Exception as e:
            self.warnings.append(f"Could not check Git health: {e}")
        
        return True  # Don't fail setup for git issues

    def create_runtime_directories(self) -> bool:
        """Create directories that should exist at runtime."""
        self.print_status("Creating runtime directories...", "INFO")

        try:
            # Create logs directory if it doesn't exist
            logs_dir = self.repo_root / "logs"
            logs_dir.mkdir(exist_ok=True)
            self.print_status(f"Logs directory ready: {logs_dir}", "INFO")

            # Create directories specified in config.yaml
            try:
                # Add repo root to path for imports
                import sys

                sys.path.insert(0, str(self.repo_root))

                from orchestrator.config_loader import load_config

                config = load_config("config.yaml")

                # Create configured directories
                directories = config.get("directories", {})
                for kind, path in directories.items():
                    if path:
                        dir_path = Path(path)
                        try:
                            dir_path.mkdir(parents=True, exist_ok=True)
                            self.print_status(
                                f"Directory ready: {kind} -> {dir_path}", "INFO"
                            )
                        except Exception as e:
                            self.issues.append(
                                f"Failed to create directory {kind} ({dir_path}): {e}"
                            )
                # After attempting all, check if any issues occurred
                if self.issues:
                    return False

                # Create category destination dirs
                categories = config.get("categories", {})
                base_dest = directories.get("destination", "")
                if base_dest:
                    for cat, cat_cfg in categories.items():
                        dest_dir = Path(base_dest) / cat_cfg.get("destination", cat)
                        try:
                            dest_dir.mkdir(parents=True, exist_ok=True)
                            self.print_status(
                                f"Category directory ready: {cat} -> {dest_dir}", "INFO"
                            )
                        except Exception as e:
                            self.warnings.append(
                                f"Failed to create category directory {cat}: {e}"
                            )

            except Exception as e:
                self.warnings.append(f"Could not create config directories: {e}")
                # Don't fail setup for this, but warn the user
                self.print_status(
                    "Config directories will be created on first run", "WARNING"
                )

            self.print_status("Runtime directories created ✓", "SUCCESS")
            self.success_items.append("Runtime directories")
            return True

        except Exception as e:
            self.issues.append(f"Failed to create runtime directories: {e}")
            return False

    def run_basic_functionality_test(self) -> bool:
        """Run a basic functionality test to ensure core features work."""
        self.print_status("Running basic functionality test...", "INFO")

        try:
            # Add repo root to path for imports
            import sys

            sys.path.insert(0, str(self.repo_root))

            # Test configuration loading
            from orchestrator.config_loader import load_config

            config = load_config("config.yaml")

            # Test file classification (this doesn't need logger)
            from orchestrator.classifier import FileClassifier

            classifier = FileClassifier(config.get("categories", {}))

            # Test with a few fake files (just check the logic, don't create files)
            test_cases = [
                ("test.pdf", "documents"),
                ("test.jpg", "images"),
                ("test.mp3", "audio"),
                ("test.zip", "archives"),
                ("test.py", "code"),
                ("test.exe", "executables"),
                ("test.mp4", "video"),
            ]

            for filename, expected in test_cases:
                result = classifier.classify_file(filename)
                if result != expected:
                    self.warnings.append(
                        f"Classification issue: {filename} -> {result} (expected {expected})"
                    )

            # Test file watcher and other imports
            from orchestrator.file_type_detector import FileTypeDetector
            from orchestrator.file_watcher import FileWatcher
            from orchestrator.logger import setup_logger

            self.print_status("Basic functionality test passed ✓", "SUCCESS")
            self.success_items.append("Functionality test")
            return True

        except Exception as e:
            import traceback

            self.issues.append(f"Functionality test failed: {e}")
            return False

    def check_for_conflict_markers_in_deps(self) -> bool:
        """Check for Git conflict markers in dependency files before installation."""
        self.print_status("Checking dependency files for conflict markers...", "INFO")
        
        dependency_files = ["requirements.txt", "requirements-dev.txt"]
        conflict_markers = ['<<<<<<<', '=======', '>>>>>>>']
        found_markers = []
        
        for file_path in dependency_files:
            full_path = self.repo_root / file_path
            if not full_path.exists():
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for i, line in enumerate(content.split('\n'), 1):
                    for marker in conflict_markers:
                        if marker in line:
                            found_markers.append(f"{file_path}:{i} - {marker}")
                            
            except Exception as e:
                self.warnings.append(f"Could not read {file_path}: {e}")
        
        if found_markers:
            self.print_status("Git conflict markers found in dependency files!", "ERROR")
            for marker in found_markers:
                self.print_status(f"  - {marker}", "ERROR")
            self.issues.append("Git conflict markers found in dependency files")
            self.print_status("", "INFO")
            self.print_status("🔧 TO FIX:", "INFO")
            self.print_status("1. Edit the affected files and remove all conflict markers", "INFO")
            self.print_status("2. Choose the correct version of each conflicted section", "INFO")
            self.print_status("3. Run the setup again", "INFO")
            self.print_status("", "INFO")
            self.print_status("For help, see: python scripts/git_conflict_resolver.py", "INFO")
            return False
        else:
            self.print_status("No conflict markers found in dependency files ✓", "SUCCESS")
            return True

    def install_dependencies(self) -> bool:
        """Install Python dependencies."""
        self.print_status("Installing Python dependencies...", "INFO")

        # First check for conflict markers
        if not self.check_for_conflict_markers_in_deps():
            return False

        try:
            cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
            result = subprocess.run(
                cmd, cwd=self.repo_root, capture_output=True, text=True
            )

            if result.returncode != 0:
                # Check if the error is due to conflict markers (common pip error)
                stderr_lower = result.stderr.lower()
                if "expected package name" in stderr_lower and ("<<<<<<" in stderr_lower or ">>>>>>>" in stderr_lower):
                    self.issues.append("Failed to install dependencies: Git conflict markers found in requirements.txt")
                    self.print_status("", "INFO")
                    self.print_status("🔧 Git conflict markers detected in requirements.txt!", "ERROR")
                    self.print_status("This usually happens when a Git merge conflict wasn't properly resolved.", "INFO")
                    self.print_status("", "INFO")
                    self.print_status("TO FIX:", "INFO")
                    self.print_status("1. Edit requirements.txt in a text editor", "INFO")
                    self.print_status("2. Look for and remove lines containing: <<<<<<<, =======, >>>>>>>", "INFO")
                    self.print_status("3. Choose the correct package versions", "INFO")
                    self.print_status("4. Run this setup script again", "INFO")
                    self.print_status("", "INFO")
                    self.print_status("For automated help: python scripts/git_conflict_resolver.py", "INFO")
                else:
                    self.issues.append(f"Failed to install dependencies: {result.stderr}")
                return False

            self.print_status("Dependencies installed ✓", "SUCCESS")
            return True

        except Exception as e:
            self.issues.append(f"Error installing dependencies: {e}")
            return False

    def clean_old_files(self) -> bool:
        """Clean up old files and directories."""
        self.print_status("Cleaning old files...", "INFO")

        try:
            # Patterns to clean
            clean_patterns = [
                "**/__pycache__",
                "**/*.pyc",
                "**/*.pyo",
                ".pytest_cache",
                "htmlcov",
                "*.egg-info",
                "dist/",
                "build/",
            ]

            cleaned_items = []
            for pattern in clean_patterns:
                for item in self.repo_root.glob(pattern):
                    if item.exists():
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                        cleaned_items.append(str(item.relative_to(self.repo_root)))

            if cleaned_items:
                self.print_status(f"Cleaned {len(cleaned_items)} items ✓", "SUCCESS")
            else:
                self.print_status("No cleanup needed ✓", "SUCCESS")

            return True

        except Exception as e:
            self.warnings.append(f"Cleanup warning: {e}")
            return True  # Don't fail setup for cleanup issues

    def setup_virtual_environment(self, venv_path: Optional[Path] = None) -> bool:
        """Create and setup a virtual environment."""
        if venv_path is None:
            venv_path = self.repo_root / "venv"

        self.print_status(f"Setting up virtual environment at {venv_path}...", "INFO")

        try:
            # Create virtual environment
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)

            # Determine activation script path
            if sys.platform == "win32":
                pip_path = venv_path / "Scripts" / "pip"
                python_path = venv_path / "Scripts" / "python"
            else:
                pip_path = venv_path / "bin" / "pip"
                python_path = venv_path / "bin" / "python"

            # Install dependencies in virtual environment
            subprocess.run(
                [str(pip_path), "install", "-r", "requirements.txt"],
                cwd=self.repo_root,
                check=True,
            )

            self.print_status("Virtual environment created ✓", "SUCCESS")
            self.print_status(f"Activate with: source {venv_path}/bin/activate", "INFO")
            return True

        except Exception as e:
            self.issues.append(f"Virtual environment setup failed: {e}")
            return False

    def run_verification(self) -> bool:
        """Run all verification checks."""
        self.print_status(
            "=== SecureDownloadsOrchestrator Setup Verification ===", "INFO", bold=True
        )

        checks = [
            self.check_python_version,
            self.check_required_files,
            self.check_directory_structure,
            self.check_dependencies,
            self.check_system_dependencies,
            self.check_configuration,
        ]
        
        # Add git health check if we're in a git repository
        if (self.repo_root / ".git").exists():
            checks.append(self.check_git_health)

        all_passed = True
        for check in checks:
            if not check():
                all_passed = False

        return all_passed

    def run_setup(self, clean: bool = False, venv: bool = False) -> bool:
        """Run full setup process."""
        self.print_status(
            "=== SecureDownloadsOrchestrator Setup ===", "INFO", bold=True
        )

        setup_steps = [
            self.check_python_version,
            self.check_required_files,
            self.check_directory_structure,
        ]

        if clean:
            setup_steps.append(self.clean_old_files)

        if venv:
            setup_steps.append(self.setup_virtual_environment)

        setup_steps.extend(
            [
                self.install_dependencies,
                self.create_runtime_directories,
                self.check_system_dependencies,
                self.check_configuration,
            ]
        )

        all_passed = True
        for step in setup_steps:
            if not step():
                all_passed = False
                # Stop on critical failures
                if self.issues:
                    break

        return all_passed

    def print_summary(self):
        """Print setup summary."""
        print("\n" + "=" * 60)

        if self.success_items:
            self.print_status("✅ Successful Items:", "SUCCESS", bold=True)
            for item in self.success_items:
                print(f"   • {item}")

        if self.warnings:
            self.print_status("⚠️  Warnings:", "WARNING", bold=True)
            for warning in self.warnings:
                print(f"   • {warning}")

        if self.issues:
            self.print_status("❌ Issues Found:", "ERROR", bold=True)
            for issue in self.issues:
                print(f"   • {issue}")
            print()
            self.print_status(
                "Setup incomplete. Please resolve the issues above.", "ERROR", bold=True
            )
        else:
            print()
            self.print_status("🎉 Setup completed successfully!", "SUCCESS", bold=True)
            self.print_status("You can now run: python -m orchestrator.main", "INFO")


def main():
    parser = argparse.ArgumentParser(
        description="Setup and verify SecureDownloadsOrchestrator"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify current setup without making changes",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean up old files and reset to fresh state",
    )
    parser.add_argument(
        "--venv", action="store_true", help="Create and setup a virtual environment"
    )

    args = parser.parse_args()

    # Find repository root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    # Verify we're in the right place
    if not (repo_root / "orchestrator").exists():
        print(
            f"{Colors.RED}[ERROR]{Colors.END} Could not find orchestrator directory. "
            f"Please run from repository root."
        )
        sys.exit(1)

    setup_manager = SetupManager(repo_root)

    try:
        if args.verify:
            success = setup_manager.run_verification()
        else:
            success = setup_manager.run_setup(clean=args.clean, venv=args.venv)

        setup_manager.print_summary()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[WARNING]{Colors.END} Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}[ERROR]{Colors.END} Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
