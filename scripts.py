#!/usr/bin/env python3
"""
Simple script runner for common development tasks.
A lightweight alternative to the more complex run_tests.py.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_cmd(cmd, description=""):
    """Run a command and return the exit code."""
    if description:
        print(f"🔄 {description}")
    print(f"Running: {' '.join(cmd)}")
    return subprocess.call(cmd)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts.py <command>")
        print("Commands:")
        print("  install     - Install dependencies")
        print("  test        - Run unit tests")
        print("  test-cov    - Run tests with coverage")
        print("  sample      - Run sample analysis")
        print("  lint        - Run linting")
        print("  format      - Format code")
        print("  clean       - Clean temporary files")
        sys.exit(1)

    command = sys.argv[1]
    
    if command == "install":
        exit_code = run_cmd(["uv", "sync", "--all-extras"], "Installing dependencies")
        if exit_code == 0:
            run_cmd(["uv", "run", "python", "-c", 
                    "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)"],
                   "Setting up NLTK data")
        sys.exit(exit_code)
        
    elif command == "test":
        sys.exit(run_cmd(["uv", "run", "pytest", "tests/", "-v"], "Running unit tests"))
        
    elif command == "test-cov":
        sys.exit(run_cmd(["uv", "run", "pytest", "tests/", "--cov=scripts", "--cov-report=html", "--cov-report=term"], 
                        "Running tests with coverage"))
        
    elif command == "sample":
        # Simple sample analysis
        script = """
import sys, os
sys.path.insert(0, 'scripts')
try:
    from duplicate_logic_detector import DuplicateLogicDetector
    detector = DuplicateLogicDetector('.')
    matches = detector.analyze_pr_changes(['test_samples/duplicate_code.py'], 'base', 'head')
    print(f'\\n📊 Found {len(matches)} potential duplicates')
    for i, match in enumerate(matches, 1):
        print(f'  {i}. {match.new_function.name} vs {match.existing_function.name}')
        print(f'     Similarity: {match.similarity_score:.2%} | Confidence: {match.confidence}')
    if not matches:
        print('✅ No duplicates detected in sample files')
except Exception as e:
    print(f'❌ Error: {e}')
"""
        sys.exit(run_cmd(["uv", "run", "python", "-c", script], "Running sample analysis"))
        
    elif command == "lint":
        sys.exit(run_cmd(["uv", "run", "flake8", "scripts/", "tests/", "--max-line-length=88"], "Running linting"))
        
    elif command == "format":
        run_cmd(["uv", "run", "black", "scripts/", "tests/"], "Formatting with black")
        sys.exit(run_cmd(["uv", "run", "isort", "scripts/", "tests/"], "Sorting imports"))
        
    elif command == "clean":
        print("🧹 Cleaning temporary files...")
        os.system("find . -type f -name '*.pyc' -delete")
        os.system("find . -type d -name '__pycache__' -delete")
        os.system("rm -rf htmlcov/ .coverage .pytest_cache/ .mypy_cache/")
        os.system("rm -f duplicate-logic-report.json duplicate-logic-report.md")
        print("✅ Cleanup complete")
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
