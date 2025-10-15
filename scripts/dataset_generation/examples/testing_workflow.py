#!/usr/bin/env python3
"""
Dataset Generation Testing Workflow

This script demonstrates how to use the generated datasets to test
different similarity algorithms and find optimal thresholds.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
import argparse


def load_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """Load a dataset from JSON file."""
    with open(dataset_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_dataset(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze dataset composition and statistics."""
    total_pairs = len(dataset)
    true_clones = sum(1 for pair in dataset if pair['clone'])
    false_clones = total_pairs - true_clones
    
    clone_ratio = true_clones / total_pairs if total_pairs > 0 else 0
    
    # Analyze function lengths
    func1_lengths = [len(pair['func1']) for pair in dataset]
    func2_lengths = [len(pair['func2']) for pair in dataset]
    
    return {
        'total_pairs': total_pairs,
        'true_clones': true_clones,
        'false_clones': false_clones,
        'clone_ratio': clone_ratio,
        'avg_func1_length': sum(func1_lengths) / len(func1_lengths) if func1_lengths else 0,
        'avg_func2_length': sum(func2_lengths) / len(func2_lengths) if func2_lengths else 0,
        'min_func_length': min(func1_lengths + func2_lengths) if func1_lengths or func2_lengths else 0,
        'max_func_length': max(func1_lengths + func2_lengths) if func1_lengths or func2_lengths else 0,
    }


def test_similarity_method(
    dataset_path: str,
    similarity_method: str,
    threshold: float,
    output_dir: str = "./test_results"
) -> Dict[str, Any]:
    """Test a similarity method with the duplicate logic detector."""
    
    # Create a temporary test file with the dataset functions
    test_file = Path(output_dir) / f"test_{similarity_method}_{threshold}.py"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load dataset
    dataset = load_dataset(dataset_path)
    
    # Create test file with all functions
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("# Generated test file for similarity testing\n\n")
        
        for i, pair in enumerate(dataset):
            # Write both functions with unique names
            func1_name = f"test_func1_{i}"
            func2_name = f"test_func2_{i}"
            
            # Modify function names in the source code
            func1_code = pair['func1'].replace(
                f"def {pair['func1_name']}", f"def {func1_name}", 1
            )
            func2_code = pair['func2'].replace(
                f"def {pair['func2_name']}", f"def {func2_name}", 1
            )
            
            f.write(f"{func1_code}\n\n")
            f.write(f"{func2_code}\n\n")
    
    # Run duplicate logic detector
    try:
        result = subprocess.run([
            'python', '-m', 'scripts.duplicate_detector.main',
            '--similarity-method', similarity_method,
            '--global-threshold', str(threshold),
            '--target-files', str(test_file),
            '--output-format', 'json'
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent.parent)
        
        if result.returncode != 0:
            print(f"Error running detector: {result.stderr}")
            return {'error': result.stderr}
        
        # Parse results (this would need to be adapted based on actual output format)
        # For now, return basic metrics
        return {
            'method': similarity_method,
            'threshold': threshold,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': True
        }
        
    except Exception as e:
        return {'error': str(e), 'success': False}
    
    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()


def run_threshold_sweep(
    dataset_path: str,
    similarity_method: str,
    threshold_range: Tuple[float, float, float] = (0.1, 0.9, 0.1),
    output_dir: str = "./threshold_sweep"
) -> List[Dict[str, Any]]:
    """Run threshold sweep for a similarity method."""
    
    start, end, step = threshold_range
    thresholds = []
    current = start
    while current <= end:
        thresholds.append(round(current, 2))
        current += step
    
    results = []
    for threshold in thresholds:
        print(f"Testing {similarity_method} with threshold {threshold}...")
        result = test_similarity_method(
            dataset_path, similarity_method, threshold, output_dir
        )
        results.append(result)
    
    return results


def compare_similarity_methods(
    dataset_path: str,
    methods: List[str],
    threshold: float = 0.7,
    output_dir: str = "./method_comparison"
) -> Dict[str, Any]:
    """Compare different similarity methods."""
    
    results = {}
    for method in methods:
        print(f"Testing similarity method: {method}")
        result = test_similarity_method(dataset_path, method, threshold, output_dir)
        results[method] = result
    
    return results


def generate_test_report(
    dataset_path: str,
    results: Dict[str, Any],
    output_path: str = "./test_report.md"
) -> None:
    """Generate a markdown test report."""
    
    dataset = load_dataset(dataset_path)
    stats = analyze_dataset(dataset)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Dataset Testing Report\n\n")
        
        f.write("## Dataset Statistics\n\n")
        f.write(f"- **Total pairs**: {stats['total_pairs']}\n")
        f.write(f"- **True clones**: {stats['true_clones']} ({stats['clone_ratio']:.1%})\n")
        f.write(f"- **False clones**: {stats['false_clones']} ({1-stats['clone_ratio']:.1%})\n")
        f.write(f"- **Average function length**: {stats['avg_func1_length']:.0f} characters\n")
        f.write(f"- **Function length range**: {stats['min_func_length']} - {stats['max_func_length']} characters\n\n")
        
        f.write("## Test Results\n\n")
        for method, result in results.items():
            f.write(f"### {method}\n\n")
            if result.get('success'):
                f.write("✅ **Status**: Success\n\n")
                f.write("**Output**:\n```\n")
                f.write(result.get('stdout', 'No output'))
                f.write("\n```\n\n")
            else:
                f.write("❌ **Status**: Failed\n\n")
                f.write("**Error**:\n```\n")
                f.write(result.get('error', 'Unknown error'))
                f.write("\n```\n\n")
        
        f.write("## Recommendations\n\n")
        f.write("Based on the test results:\n\n")
        f.write("1. Review the performance of each similarity method\n")
        f.write("2. Adjust thresholds based on your precision/recall requirements\n")
        f.write("3. Consider the computational cost of each method\n")
        f.write("4. Test with your specific codebase patterns\n\n")


def main():
    """Main function for the testing workflow."""
    parser = argparse.ArgumentParser(
        description="Test similarity algorithms using generated datasets"
    )
    
    parser.add_argument(
        "--dataset", 
        required=True, 
        help="Path to the dataset JSON file"
    )
    parser.add_argument(
        "--methods", 
        nargs='+',
        default=["jaccard_tokens", "levenshtein_norm", "sequence_matcher"],
        help="Similarity methods to test"
    )
    parser.add_argument(
        "--threshold", 
        type=float, 
        default=0.7,
        help="Threshold for similarity testing (default: 0.7)"
    )
    parser.add_argument(
        "--sweep", 
        action="store_true",
        help="Run threshold sweep instead of single test"
    )
    parser.add_argument(
        "--output-dir", 
        default="./test_results",
        help="Output directory for test results"
    )
    parser.add_argument(
        "--report", 
        default="./test_report.md",
        help="Path for the test report"
    )
    
    args = parser.parse_args()
    
    # Validate dataset file
    if not os.path.exists(args.dataset):
        print(f"Error: Dataset file '{args.dataset}' does not exist")
        sys.exit(1)
    
    print(f"🧪 Testing dataset: {args.dataset}")
    
    # Analyze dataset
    dataset = load_dataset(args.dataset)
    stats = analyze_dataset(dataset)
    
    print(f"📊 Dataset contains {stats['total_pairs']} pairs")
    print(f"   - True clones: {stats['true_clones']} ({stats['clone_ratio']:.1%})")
    print(f"   - False clones: {stats['false_clones']} ({1-stats['clone_ratio']:.1%})")
    print()
    
    # Run tests
    if args.sweep:
        print("🔄 Running threshold sweep...")
        all_results = {}
        for method in args.methods:
            results = run_threshold_sweep(
                args.dataset, method, output_dir=args.output_dir
            )
            all_results[method] = results
    else:
        print("🔄 Running method comparison...")
        all_results = compare_similarity_methods(
            args.dataset, args.methods, args.threshold, args.output_dir
        )
    
    # Generate report
    print(f"📝 Generating test report: {args.report}")
    generate_test_report(args.dataset, all_results, args.report)
    
    print("✅ Testing workflow completed!")
    print(f"📊 Results saved to: {args.output_dir}")
    print(f"📄 Report saved to: {args.report}")


if __name__ == "__main__":
    main()
