#!/usr/bin/env python3
"""
Test script to simulate and validate Git conflict resolution scenarios.

This script creates controlled conflict scenarios to test the git_conflict_resolver.py
and validate that our solutions work properly.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import sys


class GitConflictTester:
    """Test class for Git conflict scenarios."""
    
    def __init__(self):
        self.test_dir = None
        self.passed_tests = []
        self.failed_tests = []
    
    def setup_test_repo(self):
        """Create a temporary git repository for testing."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="git_conflict_test_"))
        os.chdir(self.test_dir)
        
        # Initialize git repo
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
        
        # Create initial config.yaml
        config_content = """directories:
  source: "/tmp/test_watch"
  destination: "/tmp/test_dest"

categories:
  documents:
    extensions: [".pdf", ".doc", ".docx", ".txt"]
    destination: "documents"

logging:
  console:
    enabled: true
    level: "INFO"
"""
        
        with open("config.yaml", "w") as f:
            f.write(config_content)
        
        # Create initial requirements.txt
        req_content = """watchdog>=3.0.0
PyYAML>=6.0.1
python-magic>=0.4.27"""
        
        with open("requirements.txt", "w") as f:
            f.write(req_content)
        
        # Initial commit
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
        
        print(f"✓ Test repository created at: {self.test_dir}")
    
    def test_embedded_repository_detection(self):
        """Test detection and cleanup of embedded repositories."""
        print("\n🧪 Testing embedded repository detection...")
        
        try:
            # Create an embedded repository
            embedded_dir = self.test_dir / "SecureDownloadsOrchestrator2.0"
            embedded_dir.mkdir()
            
            # Create a .git directory inside
            embedded_git = embedded_dir / ".git"
            embedded_git.mkdir()
            (embedded_git / "config").write_text("[core]\nrepositoryformatversion = 0")
            
            # Test the resolver
            script_path = Path(__file__).parent / "git_conflict_resolver.py"
            result = subprocess.run([
                sys.executable, str(script_path), "--repo-path", str(self.test_dir)
            ], capture_output=True, text=True)
            
            # Should detect embedded repo
            if "embedded repositories" in result.stdout.lower():
                print("✓ Embedded repository detection works")
                
                # Test auto-fix
                result2 = subprocess.run([
                    sys.executable, str(script_path), "--repo-path", str(self.test_dir), "--auto-fix"
                ], capture_output=True, text=True)
                
                if not embedded_git.exists():
                    print("✓ Auto-fix successfully removed embedded repository")
                    self.passed_tests.append("embedded_repository_cleanup")
                else:
                    print("❌ Auto-fix failed to remove embedded repository")
                    self.failed_tests.append("embedded_repository_cleanup")
            else:
                print("❌ Failed to detect embedded repository")
                self.failed_tests.append("embedded_repository_detection")
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            self.failed_tests.append("embedded_repository_test")
    
    def test_conflict_marker_detection(self):
        """Test detection of merge conflict markers."""
        print("\n🧪 Testing conflict marker detection...")
        
        try:
            # Create a file with conflict markers
            conflicted_config = """directories:
  source: "/tmp/test_watch"
<<<<<<< HEAD
  destination: "/tmp/test_dest_old"
=======
  destination: "/tmp/test_dest_new"
>>>>>>> feature-branch

categories:
  documents:
    extensions: [".pdf", ".doc", ".docx", ".txt"]
    destination: "documents"
"""
            
            with open("config.yaml", "w") as f:
                f.write(conflicted_config)
            
            # Test the resolver
            script_path = Path(__file__).parent / "git_conflict_resolver.py"
            result = subprocess.run([
                sys.executable, str(script_path), "--repo-path", str(self.test_dir)
            ], capture_output=True, text=True)
            
            if "conflict markers" in result.stdout.lower() and result.returncode != 0:
                print("✓ Conflict marker detection works")
                self.passed_tests.append("conflict_marker_detection")
            else:
                print("❌ Failed to detect conflict markers")
                self.failed_tests.append("conflict_marker_detection")
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            self.failed_tests.append("conflict_marker_test")
    
    def test_clean_repository_validation(self):
        """Test that clean repositories pass validation."""
        print("\n🧪 Testing clean repository validation...")
        
        try:
            # Reset to clean state
            clean_config = """directories:
  source: "/tmp/test_watch"
  destination: "/tmp/test_dest"

categories:
  documents:
    extensions: [".pdf", ".doc", ".docx", ".txt"]
    destination: "documents"

logging:
  console:
    enabled: true
    level: "INFO"
"""
            
            with open("config.yaml", "w") as f:
                f.write(clean_config)
            
            # Test the resolver
            script_path = Path(__file__).parent / "git_conflict_resolver.py"
            result = subprocess.run([
                sys.executable, str(script_path), "--repo-path", str(self.test_dir)
            ], capture_output=True, text=True)
            
            if "repository is healthy" in result.stdout.lower() and result.returncode == 0:
                print("✓ Clean repository validation works")
                self.passed_tests.append("clean_repository_validation")
            else:
                print("❌ Clean repository validation failed")
                print(f"Output: {result.stdout}")
                print(f"Error: {result.stderr}")
                self.failed_tests.append("clean_repository_validation")
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            self.failed_tests.append("clean_repository_test")
    
    def cleanup(self):
        """Clean up test directory."""
        if self.test_dir and self.test_dir.exists():
            os.chdir("/")
            shutil.rmtree(self.test_dir)
            print(f"✓ Cleaned up test directory: {self.test_dir}")
    
    def run_all_tests(self):
        """Run all tests and report results."""
        print("🚀 Starting Git Conflict Resolution Tests...")
        
        try:
            self.setup_test_repo()
            self.test_embedded_repository_detection()
            self.test_conflict_marker_detection()
            self.test_clean_repository_validation()
            
        finally:
            self.cleanup()
        
        # Report results
        print("\n" + "="*60)
        print("📊 TEST RESULTS")
        print("="*60)
        
        if self.passed_tests:
            print(f"✅ PASSED ({len(self.passed_tests)}):")
            for test in self.passed_tests:
                print(f"   ✓ {test}")
        
        if self.failed_tests:
            print(f"\n❌ FAILED ({len(self.failed_tests)}):")
            for test in self.failed_tests:
                print(f"   ✗ {test}")
        
        total_tests = len(self.passed_tests) + len(self.failed_tests)
        success_rate = len(self.passed_tests) / total_tests * 100 if total_tests > 0 else 0
        
        print(f"\n📈 Success Rate: {success_rate:.1f}% ({len(self.passed_tests)}/{total_tests})")
        
        return len(self.failed_tests) == 0


def main():
    """Main entry point."""
    tester = GitConflictTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()