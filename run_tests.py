#!/usr/bin/env python3
"""
Test runner for duplicate logic detection.
This script provides easy ways to test the duplicate detection functionality.
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional


def run_unit_tests(verbose: bool = False, coverage: bool = False) -> int:
    """
    Run the pytest unit tests.
    
    Args:
        verbose: Enable verbose output
        coverage: Generate coverage report
        
    Returns:
        Exit code from pytest
    """
    cmd = ["uv", "run", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=scripts", "--cov-report=html", "--cov-report=term"])
    
    print("Running unit tests...")
    return subprocess.call(cmd)


def run_integration_test(repository_path: str = None, changed_files: List[str] = None) -> Dict:
    """
    Run integration test using the sample files.
    
    Args:
        repository_path: Path to repository (defaults to current directory)
        changed_files: List of changed files to analyze
        
    Returns:
        Test results dictionary
    """
    if repository_path is None:
        repository_path = os.getcwd()
    
    if changed_files is None:
        changed_files = ["test_samples/duplicate_code.py"]
    
    # Add scripts directory to Python path
    scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
    sys.path.insert(0, scripts_dir)
    
    try:
        from duplicate_logic_detector import DuplicateLogicDetector
        
        # Load default configuration
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'default-config.yml')
        if os.path.exists(config_path):
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        else:
            # Fallback configuration
            config = {
                'thresholds': {
                    'exact_match': 0.95,
                    'high_similarity': 0.80,
                    'moderate_similarity': 0.60
                },
                'similarity_weights': {
                    'signature': 0.30,
                    'semantic': 0.40,
                    'ast_structure': 0.20,
                    'function_calls': 0.10
                },
                'min_complexity': 1,
                'min_function_lines': 3,
                'include_patterns': ['**/*.py'],
                'exclude_patterns': ['**/test_*.py', '**/tests/**']
            }
        
        print(f"Analyzing repository: {repository_path}")
        print(f"Changed files: {changed_files}")
        
        # Initialize detector
        detector = DuplicateLogicDetector(
            repository_path=repository_path
        )
        
        # Run analysis
        matches = detector.analyze_pr_changes(changed_files, "base_sha", "head_sha")
        
        # Prepare results
        results = {
            'total_matches': len(matches),
            'high_confidence_matches': len([m for m in matches if m.confidence in ['high', 'very_high']]),
            'matches': []
        }
        
        for match in matches:
            results['matches'].append({
                'original_function': {
                    'name': match.existing_function.name,
                    'file': match.existing_function.file_path,
                    'line_start': match.existing_function.line_start,
                    'line_end': match.existing_function.line_end
                },
                'duplicate_function': {
                    'name': match.new_function.name,
                    'file': match.new_function.file_path,
                    'line_start': match.new_function.line_start,
                    'line_end': match.new_function.line_end
                },
                'similarity_score': match.similarity_score,
                'confidence_level': match.confidence,
                'suggestions': [match.suggestion]
            })
        
        return results
        
    except ImportError as e:
        print(f"Error importing duplicate_logic_detector: {e}")
        print("Make sure the scripts/duplicate_logic_detector.py file exists and dependencies are installed.")
        return {'error': str(e)}
    except Exception as e:
        print(f"Error running integration test: {e}")
        return {'error': str(e)}


def run_sample_analysis() -> None:
    """
    Run analysis on the sample files and display results.
    """
    print("=" * 60)
    print("DUPLICATE LOGIC DETECTION - SAMPLE ANALYSIS")
    print("=" * 60)
    
    results = run_integration_test()
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        return
    
    print(f"\n📊 ANALYSIS RESULTS:")
    print(f"   Total matches found: {results['total_matches']}")
    print(f"   High-confidence matches: {results['high_confidence_matches']}")
    
    if results['matches']:
        print(f"\n🔍 DETAILED MATCHES:")
        for i, match in enumerate(results['matches'], 1):
            print(f"\n   Match #{i}:")
            print(f"   ├── Original: {match['original_function']['name']} ({match['original_function']['file']}:{match['original_function']['line_start']})")
            print(f"   ├── Duplicate: {match['duplicate_function']['name']} ({match['duplicate_function']['file']}:{match['duplicate_function']['line_start']})")
            print(f"   ├── Similarity: {match['similarity_score']:.2%}")
            print(f"   ├── Confidence: {match['confidence_level']}")
            
            if match['suggestions']:
                print(f"   └── Suggestions:")
                for suggestion in match['suggestions']:
                    print(f"       • {suggestion}")
    else:
        print("\n✅ No duplicate logic detected in the sample files.")


def install_dependencies() -> int:
    """
    Install required dependencies for testing using uv.
    
    Returns:
        Exit code from uv install
    """
    print("Installing dependencies with uv...")
    
    # Install all dependencies including test dependencies
    cmd = ["uv", "sync", "--all-extras"]
    result = subprocess.call(cmd)
    
    return result


def setup_nltk_data() -> None:
    """
    Download required NLTK data.
    """
    print("Setting up NLTK data...")
    try:
        cmd = ["uv", "run", "python", "-c", """
import nltk
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    print('NLTK data already available')
except LookupError:
    print('Downloading NLTK data...')
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    print('NLTK data download complete')
"""]
        subprocess.call(cmd)
        print("✅ NLTK data setup complete")
    except Exception as e:
        print(f"⚠️  Error setting up NLTK data: {e}")


def main():
    """Main function to handle command line arguments and run tests."""
    parser = argparse.ArgumentParser(description="Test runner for duplicate logic detection")
    
    parser.add_argument(
        'command',
        choices=['unit', 'integration', 'sample', 'install', 'all'],
        help='Test command to run'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Generate coverage report (unit tests only)'
    )
    
    parser.add_argument(
        '--repository-path',
        help='Path to repository for integration tests'
    )
    
    parser.add_argument(
        '--changed-files',
        nargs='+',
        help='List of changed files to analyze'
    )
    
    args = parser.parse_args()
    
    if args.command == 'install':
        exit_code = install_dependencies()
        setup_nltk_data()
        sys.exit(exit_code)
    
    elif args.command == 'unit':
        exit_code = run_unit_tests(verbose=args.verbose, coverage=args.coverage)
        sys.exit(exit_code)
    
    elif args.command == 'integration':
        results = run_integration_test(
            repository_path=args.repository_path,
            changed_files=args.changed_files
        )
        
        if 'error' in results:
            print(f"Integration test failed: {results['error']}")
            sys.exit(1)
        else:
            print(f"Integration test completed: {results['total_matches']} matches found")
            sys.exit(0)
    
    elif args.command == 'sample':
        run_sample_analysis()
    
    elif args.command == 'all':
        print("Running all tests...")
        
        # Install dependencies
        print("\n1. Installing dependencies...")
        install_exit_code = install_dependencies()
        setup_nltk_data()
        
        if install_exit_code != 0:
            print("❌ Dependency installation failed")
            sys.exit(install_exit_code)
        
        # Run unit tests
        print("\n2. Running unit tests...")
        unit_exit_code = run_unit_tests(verbose=args.verbose, coverage=args.coverage)
        
        if unit_exit_code != 0:
            print("❌ Unit tests failed")
        else:
            print("✅ Unit tests passed")
        
        # Run sample analysis
        print("\n3. Running sample analysis...")
        run_sample_analysis()
        
        sys.exit(unit_exit_code)


if __name__ == "__main__":
    main()
