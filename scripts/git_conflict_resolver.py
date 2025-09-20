#!/usr/bin/env python3
"""
Git Conflict Resolution Helper for SecureDownloadsOrchestrator 2.0

This script helps identify and resolve common Git conflicts, particularly:
- Embedded repository detection and cleanup
- Merge conflict resolution assistance
- Branch synchronization guidance
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional


class GitConflictResolver:
    """Helper class for resolving Git conflicts and issues."""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.issues = []
        self.warnings = []
        self.fixes_applied = []
    
    def print_status(self, message: str, status: str = "INFO"):
        """Print colored status message."""
        colors = {
            "SUCCESS": "\033[92m",  # Green
            "WARNING": "\033[93m",  # Yellow  
            "ERROR": "\033[91m",    # Red
            "INFO": "\033[94m",     # Blue
        }
        reset = "\033[0m"
        print(f"[{colors.get(status, '')}{status}{reset}] {message}")
    
    def run_git_command(self, cmd: List[str]) -> Tuple[bool, str, str]:
        """Run a git command and return success status and output."""
        try:
            result = subprocess.run(
                ["git"] + cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def check_embedded_repositories(self) -> bool:
        """Check for embedded git repositories."""
        self.print_status("Checking for embedded git repositories...", "INFO")
        
        embedded_repos = []
        for git_dir in self.repo_path.rglob(".git"):
            if git_dir.is_dir() and git_dir != self.repo_path / ".git":
                embedded_repos.append(git_dir)
        
        if embedded_repos:
            self.print_status(f"Found {len(embedded_repos)} embedded repositories:", "WARNING")
            for repo in embedded_repos:
                rel_path = repo.relative_to(self.repo_path)
                self.print_status(f"  - {rel_path}", "WARNING")
                self.warnings.append(f"Embedded repository: {rel_path}")
            return False
        else:
            self.print_status("No embedded repositories found ✓", "SUCCESS")
            return True
    
    def clean_embedded_repositories(self, auto_fix: bool = False) -> bool:
        """Remove embedded git repositories."""
        embedded_repos = []
        for git_dir in self.repo_path.rglob(".git"):
            if git_dir.is_dir() and git_dir != self.repo_path / ".git":
                embedded_repos.append(git_dir)
        
        if not embedded_repos:
            return True
            
        if not auto_fix:
            self.print_status("Found embedded repositories. Use --auto-fix to remove them.", "WARNING")
            return False
        
        self.print_status("Removing embedded repositories...", "INFO")
        for repo in embedded_repos:
            try:
                import shutil
                parent_dir = repo.parent
                self.print_status(f"Removing {repo.relative_to(self.repo_path)}", "INFO")
                shutil.rmtree(repo)
                
                # If the parent directory is now empty (except for hidden files), consider removing it
                if not any(f for f in parent_dir.iterdir() if not f.name.startswith('.')):
                    self.print_status(f"Removing empty directory {parent_dir.relative_to(self.repo_path)}", "INFO")
                    parent_dir.rmdir()
                
                self.fixes_applied.append(f"Removed embedded repository: {repo.relative_to(self.repo_path)}")
            except Exception as e:
                self.print_status(f"Failed to remove {repo}: {e}", "ERROR")
                return False
        
        return True
    
    def check_merge_conflicts(self) -> bool:
        """Check for active merge conflicts."""
        self.print_status("Checking for merge conflicts...", "INFO")
        
        # Check git status for merge conflicts
        success, stdout, stderr = self.run_git_command(["status", "--porcelain"])
        if not success:
            self.print_status(f"Failed to check git status: {stderr}", "ERROR")
            return False
        
        conflict_files = []
        unmerged_files = []
        
        for line in stdout.split('\n'):
            if line.startswith('UU ') or line.startswith('AA '):
                conflict_files.append(line[3:])
            elif line.startswith('UD ') or line.startswith('DU ') or line.startswith('AU ') or line.startswith('UA '):
                unmerged_files.append(line[3:])
        
        if conflict_files:
            self.print_status(f"Found {len(conflict_files)} files with merge conflicts:", "ERROR")
            for file in conflict_files:
                self.print_status(f"  - {file}", "ERROR")
                self.issues.append(f"Merge conflict in: {file}")
            return False
        
        if unmerged_files:
            self.print_status(f"Found {len(unmerged_files)} unmerged files:", "WARNING")
            for file in unmerged_files:
                self.print_status(f"  - {file}", "WARNING")
                self.warnings.append(f"Unmerged file: {file}")
        
        if not conflict_files and not unmerged_files:
            self.print_status("No merge conflicts found ✓", "SUCCESS")
        
        return len(conflict_files) == 0
    
    def check_for_conflict_markers(self, files: Optional[List[str]] = None) -> bool:
        """Check for conflict markers in specified files or common config files."""
        if files is None:
            files = ["config.yaml", "requirements.txt", "requirements-dev.txt"]
        
        self.print_status("Checking for conflict markers in files...", "INFO")
        
        found_markers = []
        for file_path in files:
            full_path = self.repo_path / file_path
            if not full_path.exists():
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                conflict_markers = ['<<<<<<<', '=======', '>>>>>>>']
                for i, line in enumerate(content.split('\n'), 1):
                    for marker in conflict_markers:
                        if marker in line:
                            found_markers.append(f"{file_path}:{i} - {marker}")
                            self.issues.append(f"Conflict marker in {file_path} at line {i}")
            except Exception as e:
                self.print_status(f"Could not read {file_path}: {e}", "WARNING")
        
        if found_markers:
            self.print_status(f"Found {len(found_markers)} conflict markers:", "ERROR")
            for marker in found_markers:
                self.print_status(f"  - {marker}", "ERROR")
            return False
        else:
            self.print_status("No conflict markers found ✓", "SUCCESS")
            return True
    
    def check_branch_status(self) -> bool:
        """Check git branch status and remote sync."""
        self.print_status("Checking branch status...", "INFO")
        
        # Get current branch
        success, stdout, stderr = self.run_git_command(["branch", "--show-current"])
        if not success:
            self.print_status(f"Failed to get current branch: {stderr}", "ERROR")
            return False
        
        current_branch = stdout.strip()
        self.print_status(f"Current branch: {current_branch}", "INFO")
        
        # Check if we're ahead/behind remote
        success, stdout, stderr = self.run_git_command(["status", "-b", "--porcelain"])
        if success and stdout:
            first_line = stdout.split('\n')[0]
            if 'ahead' in first_line or 'behind' in first_line:
                self.print_status(f"Branch status: {first_line}", "WARNING")
                self.warnings.append(f"Branch sync issue: {first_line}")
        
        return True
    
    def suggest_conflict_resolution(self):
        """Provide suggestions for resolving detected issues."""
        if not self.issues and not self.warnings:
            self.print_status("No issues detected! Repository is in good state.", "SUCCESS")
            return
        
        self.print_status("=== CONFLICT RESOLUTION SUGGESTIONS ===", "INFO")
        
        if any("Embedded repository" in issue for issue in self.warnings):
            print("\n🔧 EMBEDDED REPOSITORY CLEANUP:")
            print("   Run this script with --auto-fix to remove embedded repositories")
            print("   Or manually remove with: rm -rf path/to/embedded/.git")
        
        if any("Merge conflict" in issue for issue in self.issues):
            print("\n🔧 MERGE CONFLICT RESOLUTION:")
            print("   1. Edit conflicted files to resolve conflicts")
            print("   2. Remove conflict markers (<<<<<<<, =======, >>>>>>>)")
            print("   3. Stage resolved files: git add <file>")
            print("   4. Complete merge: git commit")
        
        if any("Conflict marker" in issue for issue in self.issues):
            print("\n🔧 CONFLICT MARKER CLEANUP:")
            print("   Edit the affected files and remove all conflict markers")
            print("   Choose the correct version of each conflicted section")
        
        if any("Branch sync" in warning for warning in self.warnings):
            print("\n🔧 BRANCH SYNCHRONIZATION:")
            print("   Fetch latest: git fetch origin")
            print("   Merge changes: git merge origin/main")  
            print("   Or rebase: git rebase origin/main")
            print("   Then push: git push origin <branch>")
    
    def run_full_check(self, auto_fix: bool = False) -> bool:
        """Run all checks and return overall health status."""
        self.print_status("=== Git Repository Health Check ===", "INFO")
        
        all_good = True
        
        # Check for embedded repositories
        if not self.check_embedded_repositories():
            if not self.clean_embedded_repositories(auto_fix):
                all_good = False
        
        # Check for merge conflicts
        if not self.check_merge_conflicts():
            all_good = False
        
        # Check for conflict markers
        if not self.check_for_conflict_markers():
            all_good = False
        
        # Check branch status
        self.check_branch_status()
        
        # Summary
        print("\n" + "="*50)
        if self.fixes_applied:
            self.print_status("🔧 Fixes Applied:", "SUCCESS")
            for fix in self.fixes_applied:
                print(f"   ✓ {fix}")
        
        if self.issues:
            self.print_status(f"❌ Issues Found: {len(self.issues)}", "ERROR")
            for issue in self.issues:
                print(f"   • {issue}")
        
        if self.warnings:
            self.print_status(f"⚠️  Warnings: {len(self.warnings)}", "WARNING")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if all_good and not self.warnings:
            self.print_status("🎉 Repository is healthy!", "SUCCESS")
        
        # Provide suggestions
        self.suggest_conflict_resolution()
        
        return all_good


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Git Conflict Resolution Helper for SecureDownloadsOrchestrator 2.0"
    )
    parser.add_argument(
        "--auto-fix", 
        action="store_true",
        help="Automatically fix issues where possible (like removing embedded repos)"
    )
    parser.add_argument(
        "--check-files",
        nargs="+",
        help="Specific files to check for conflict markers"
    )
    parser.add_argument(
        "--repo-path",
        default=".",
        help="Path to the git repository (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Verify we're in a git repository
    repo_path = Path(args.repo_path).resolve()
    if not (repo_path / ".git").exists():
        print("[ERROR] Not a git repository or .git directory not found")
        sys.exit(1)
    
    resolver = GitConflictResolver(args.repo_path)
    
    if args.check_files:
        # Just check specific files for conflict markers
        success = resolver.check_for_conflict_markers(args.check_files)
        sys.exit(0 if success else 1)
    else:
        # Run full health check
        success = resolver.run_full_check(args.auto_fix)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()