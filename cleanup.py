#!/usr/bin/env python3
"""
Cleanup script to remove temporary files and cache directories.

This script removes:
- API capture files (api_interactions_*.jsonl, api_capture_*.log)
- Batch review results (batch_review_results*.json)
- Fine-tuning datasets (fine_tuning_dataset.jsonl)
- Python cache directories (__pycache__, .pytest_cache)
- Compiled Python files (*.pyc, *.pyo)
- IDE cache (.claude)
"""

import os
import shutil
import glob
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent


def cleanup():
    """Remove temporary files and cache directories."""
    
    print("\n" + "="*70)
    print("CLEANUP: Removing Temporary Files and Cache")
    print("="*70 + "\n")
    
    # Files to remove (glob patterns)
    file_patterns = [
        "api_interactions_*.jsonl",
        "api_capture_*.log",
        "batch_review_results*.json",
        "fine_tuning_dataset.jsonl",
        "*.pyc",
        "*.pyo",
        "*.pyd",
    ]
    
    # Directories to remove
    dirs_to_remove = [
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".claude",
        ".venv/__pycache__",
    ]
    
    # Track what was removed
    removed_files = 0
    removed_dirs = 0
    total_size = 0
    
    # Remove files
    print("Removing temporary files...")
    for pattern in file_patterns:
        for filepath in glob.glob(str(PROJECT_ROOT / pattern)):
            try:
                file_size = os.path.getsize(filepath)
                os.remove(filepath)
                removed_files += 1
                total_size += file_size
                print(f"  [REMOVED] {Path(filepath).name}")
            except Exception as e:
                print(f"  [ERROR] {Path(filepath).name}: {e}")
    
    # Remove directories
    print("\nRemoving cache directories...")
    for dir_pattern in dirs_to_remove:
        for dirpath in glob.glob(str(PROJECT_ROOT / "**" / dir_pattern), recursive=True):
            if os.path.isdir(dirpath):
                try:
                    # Calculate directory size
                    dir_size = sum(
                        f.stat().st_size 
                        for f in Path(dirpath).rglob('*') 
                        if f.is_file()
                    )
                    shutil.rmtree(dirpath)
                    removed_dirs += 1
                    total_size += dir_size
                    rel_path = os.path.relpath(dirpath, PROJECT_ROOT)
                    print(f"  [REMOVED] {rel_path}/")
                except Exception as e:
                    print(f"  [ERROR] {dirpath}: {e}")
    
    # Print summary
    print("\n" + "="*70)
    print("CLEANUP SUMMARY")
    print("="*70)
    print(f"Files removed: {removed_files}")
    print(f"Directories removed: {removed_dirs}")
    print(f"Space freed: {total_size / (1024*1024):.2f} MB")
    print("="*70 + "\n")
    
    if removed_files == 0 and removed_dirs == 0:
        print("No temporary files or cache directories found.\n")
    else:
        print("Cleanup complete!\n")


if __name__ == "__main__":
    cleanup()
