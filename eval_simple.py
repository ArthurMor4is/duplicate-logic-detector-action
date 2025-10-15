#!/usr/bin/env python3
"""
Simple evaluation script for the current duplicate logic detection implementation.

This script benchmarks the current implementation on different dataset sizes
to measure performance and quality metrics.
"""

import time
import json
import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import psutil
from dataclasses import dataclass
import argparse


@dataclass
class BenchmarkResult:
    """Simple benchmark result."""
    dataset_name: str
    execution_time: float
    memory_usage_mb: float
    functions_analyzed: int
    files_analyzed: int
    matches_found: int
    duplicates_detected: int
    error: str = None


class SimpleBenchmark:
    """Simple benchmark for the current implementation."""
    
    def __init__(self):
        self.results = []
        self.script_path = Path(__file__).parent / "scripts" / "duplicate_logic_detector.py"
        
    def create_test_dataset(self, name: str, num_files: int = 10, functions_per_file: int = 20) -> Path:
        """Create a simple test dataset."""
        dataset_dir = Path(f"eval_datasets/{name}")
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # Create src directory as expected by the detection script
        src_dir = dataset_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        # Create ground truth for later validation
        ground_truth = {"duplicate_pairs": []}
        
        for file_idx in range(num_files):
            file_path = src_dir / f"test_file_{file_idx:03d}.py"
            
            functions = []
            duplicate_pairs = []
            
            for func_idx in range(functions_per_file):
                if func_idx % 4 == 0 and func_idx > 0:
                    # Create a duplicate every 4th function
                    original_idx = func_idx - 4
                    functions.append(self._create_duplicate_function(f"func_{original_idx}", f"func_{func_idx}"))
                    duplicate_pairs.append((f"func_{original_idx}", f"func_{func_idx}"))
                else:
                    functions.append(self._create_original_function(f"func_{func_idx}"))
            
            # Write file
            content = self._generate_file_content(functions)
            file_path.write_text(content)
            
            # Add to ground truth
            for orig, dup in duplicate_pairs:
                ground_truth["duplicate_pairs"].append({
                    "original_function": orig,
                    "duplicate_function": dup,
                    "file": str(file_path.name),
                    "similarity_type": "high"
                })
        
        # Save ground truth
        ground_truth_path = dataset_dir / "ground_truth.json"
        ground_truth_path.write_text(json.dumps(ground_truth, indent=2))
        
        return dataset_dir
    
    def _create_original_function(self, name: str) -> str:
        """Create an original function."""
        templates = [
            f'''def {name}(data: List[Dict]) -> List[Dict]:
    """Process {name} data."""
    result = []
    for item in data:
        if item.get('active', False):
            item['processed'] = True
            result.append(item)
    return result''',
            
            f'''def {name}(email: str) -> bool:
    """Validate {name} email format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{{2,}}$'
    return re.match(pattern, email) is not None''',
            
            f'''def {name}(price: float, percentage: float) -> float:
    """Calculate {name} discount."""
    if percentage < 0 or percentage > 100:
        raise ValueError("Invalid percentage")
    return price * (percentage / 100)'''
        ]
        
        import random
        return random.choice(templates)
    
    def _create_duplicate_function(self, original_name: str, duplicate_name: str) -> str:
        """Create a duplicate function with slight modifications."""
        # Get the original function and modify it slightly
        original = self._create_original_function(original_name)
        
        # Simple modifications to create duplicates
        duplicate = original.replace(original_name, duplicate_name)
        duplicate = duplicate.replace('item', 'element')  # Variable name change
        duplicate = duplicate.replace('result', 'output')  # Variable name change
        duplicate = duplicate.replace('data', 'input_data')  # Parameter name change
        
        return duplicate
    
    def _generate_file_content(self, functions: List[str]) -> str:
        """Generate complete file content."""
        header = '''#!/usr/bin/env python3
"""Generated test file for duplicate detection evaluation."""

import re
from typing import List, Dict, Any

'''
        return header + "\n\n".join(functions) + "\n"
    
    def run_benchmark(self, dataset_path: Path) -> BenchmarkResult:
        """Run benchmark on a dataset."""
        print(f"  Running benchmark on {dataset_path.name}...")
        
        # Get all Python files in dataset src directory
        src_dir = dataset_path / "src"
        python_files = list(src_dir.glob("*.py")) if src_dir.exists() else []
        # Only mark the first half as "changed" so the second half serves as existing codebase
        changed_count = max(1, len(python_files) // 2)
        changed_files = "\n".join(str(f.relative_to(dataset_path)) for f in python_files[:changed_count])
        
        # Monitor memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        
        try:
            # Run the duplicate detection script
            cmd = [
                sys.executable, str(self.script_path),
                "--repository-path", str(dataset_path),
                "--base-sha", "HEAD~1",
                "--head-sha", "HEAD",
                "--changed-files", changed_files,
                "--output-format", "json"
            ]
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=str(Path(__file__).parent),  # Run from project root
                timeout=600  # 10 minute timeout
            )
            
            execution_time = time.time() - start_time
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = peak_memory - initial_memory
            
            if result.returncode == 0:
                # Parse results from stdout (JSON format)
                matches = []
                try:
                    if result.stdout.strip():
                        # Find the JSON part (starts with '{')
                        stdout_lines = result.stdout.split('\n')
                        json_lines = []
                        json_started = False
                        for line in stdout_lines:
                            if line.strip().startswith('{') or json_started:
                                json_started = True
                                json_lines.append(line)
                        
                        if json_lines:
                            json_str = '\n'.join(json_lines)
                            report_data = json.loads(json_str)
                            matches = report_data.get('matches', [])
                except json.JSONDecodeError as e:
                    # If JSON parsing fails, assume no matches found
                    matches = []
                
                return BenchmarkResult(
                    dataset_name=dataset_path.name,
                    execution_time=execution_time,
                    memory_usage_mb=memory_usage,
                    functions_analyzed=len(python_files) * 20,  # Approximate
                    files_analyzed=len(python_files),
                    matches_found=len(matches),
                    duplicates_detected=len(matches)  # Count all matches
                )
            else:
                return BenchmarkResult(
                    dataset_name=dataset_path.name,
                    execution_time=execution_time,
                    memory_usage_mb=memory_usage,
                    functions_analyzed=0,
                    files_analyzed=len(python_files),
                    matches_found=0,
                    duplicates_detected=0,
                    error=f"Script failed: {result.stderr}"
                )
                
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return BenchmarkResult(
                dataset_name=dataset_path.name,
                execution_time=execution_time,
                memory_usage_mb=0,
                functions_analyzed=0,
                files_analyzed=len(python_files),
                matches_found=0,
                duplicates_detected=0,
                error="Timeout (>10 minutes)"
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return BenchmarkResult(
                dataset_name=dataset_path.name,
                execution_time=execution_time,
                memory_usage_mb=0,
                functions_analyzed=0,
                files_analyzed=len(python_files),
                matches_found=0,
                duplicates_detected=0,
                error=str(e)
            )
    
    def run_full_evaluation(self) -> List[BenchmarkResult]:
        """Run evaluation on different dataset sizes."""
        print("🚀 Running Simple Duplicate Detection Evaluation")
        print("=" * 50)
        
        # Define test scenarios
        scenarios = [
            ("small", 10, 20),    # 10 files, 20 functions each = 200 functions
            ("medium", 50, 20),   # 50 files, 20 functions each = 1000 functions  
            ("large", 100, 25),   # 100 files, 25 functions each = 2500 functions
        ]
        
        results = []
        
        for name, num_files, funcs_per_file in scenarios:
            print(f"\n📁 Creating {name} dataset ({num_files} files, {funcs_per_file} functions each)...")
            
            # Create dataset
            dataset_path = self.create_test_dataset(name, num_files, funcs_per_file)
            print(f"  ✅ Created dataset at {dataset_path}")
            
            # Run benchmark
            result = self.run_benchmark(dataset_path)
            results.append(result)
            
            # Print immediate results
            if result.error:
                print(f"  ❌ Failed: {result.error}")
            else:
                print(f"  ✅ Completed in {result.execution_time:.1f}s")
                print(f"     Memory: {result.memory_usage_mb:.1f} MB")
                print(f"     Functions/sec: {result.functions_analyzed / result.execution_time:.1f}")
                print(f"     Duplicates found: {result.duplicates_detected}")
        
        return results
    
    def generate_report(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Generate a simple report."""
        successful_results = [r for r in results if r.error is None]
        
        report = {
            "summary": {
                "total_runs": len(results),
                "successful_runs": len(successful_results),
                "failed_runs": len(results) - len(successful_results)
            },
            "performance_analysis": {},
            "scalability_analysis": {},
            "results": []
        }
        
        if successful_results:
            # Performance analysis
            avg_time = sum(r.execution_time for r in successful_results) / len(successful_results)
            avg_memory = sum(r.memory_usage_mb for r in successful_results) / len(successful_results)
            avg_throughput = sum(r.functions_analyzed / r.execution_time for r in successful_results) / len(successful_results)
            
            report["performance_analysis"] = {
                "average_execution_time": avg_time,
                "average_memory_usage_mb": avg_memory,
                "average_throughput_functions_per_second": avg_throughput
            }
            
            # Scalability analysis
            if len(successful_results) >= 2:
                small_result = next((r for r in successful_results if "small" in r.dataset_name), None)
                large_result = next((r for r in successful_results if "large" in r.dataset_name), None)
                
                if small_result and large_result:
                    scale_factor = large_result.functions_analyzed / small_result.functions_analyzed
                    time_scale_factor = large_result.execution_time / small_result.execution_time
                    
                    report["scalability_analysis"] = {
                        "dataset_scale_factor": scale_factor,
                        "time_scale_factor": time_scale_factor,
                        "scalability_efficiency": scale_factor / time_scale_factor,
                        "projected_time_for_5000_functions": (large_result.execution_time / large_result.functions_analyzed) * 5000
                    }
        
        # Add detailed results
        for result in results:
            result_dict = {
                "dataset": result.dataset_name,
                "execution_time_seconds": result.execution_time,
                "memory_usage_mb": result.memory_usage_mb,
                "functions_analyzed": result.functions_analyzed,
                "files_analyzed": result.files_analyzed,
                "matches_found": result.matches_found,
                "duplicates_detected": result.duplicates_detected,
                "throughput_functions_per_second": result.functions_analyzed / result.execution_time if result.execution_time > 0 and result.error is None else 0,
                "error": result.error
            }
            report["results"].append(result_dict)
        
        return report
    
    def print_summary(self, results: List[BenchmarkResult]):
        """Print a human-readable summary."""
        print("\n" + "=" * 60)
        print("EVALUATION SUMMARY")
        print("=" * 60)
        
        successful = [r for r in results if r.error is None]
        failed = [r for r in results if r.error is not None]
        
        print(f"✅ Successful runs: {len(successful)}")
        print(f"❌ Failed runs: {len(failed)}")
        
        if failed:
            print(f"\nFailed runs:")
            for result in failed:
                print(f"  {result.dataset_name}: {result.error}")
        
        if successful:
            print(f"\nPerformance Results:")
            print(f"{'Dataset':<10} {'Time':<8} {'Memory':<10} {'Functions':<10} {'Throughput':<12} {'Duplicates':<10}")
            print("-" * 70)
            
            for result in successful:
                throughput = result.functions_analyzed / result.execution_time
                print(f"{result.dataset_name:<10} {result.execution_time:>6.1f}s {result.memory_usage_mb:>8.1f}MB "
                      f"{result.functions_analyzed:>9d} {throughput:>10.1f}/s {result.duplicates_detected:>9d}")
            
            # Scalability insight
            if len(successful) >= 2:
                small = next((r for r in successful if "small" in r.dataset_name), None)
                large = next((r for r in successful if "large" in r.dataset_name), None)
                
                if small and large:
                    scale_factor = large.functions_analyzed / small.functions_analyzed
                    time_factor = large.execution_time / small.execution_time
                    
                    print(f"\n📈 Scalability Analysis:")
                    print(f"   Dataset size increased {scale_factor:.1f}x")
                    print(f"   Execution time increased {time_factor:.1f}x")
                    print(f"   Efficiency: {scale_factor/time_factor:.2f} (1.0 = linear scaling)")
                    
                    # Project to your 5-minute scenario
                    if large.execution_time > 0:
                        projected_time = (large.execution_time / large.functions_analyzed) * 5000
                        print(f"   Projected time for 5000 functions: {projected_time/60:.1f} minutes")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Simple evaluation for duplicate logic detection")
    parser.add_argument("--output", default="eval_results.json", help="Output file for results")
    parser.add_argument("--skip-large", action="store_true", help="Skip large dataset (for quick testing)")
    
    args = parser.parse_args()
    
    # Check if the main script exists
    script_path = Path("scripts/duplicate_logic_detector.py")
    if not script_path.exists():
        print("❌ Error: scripts/duplicate_logic_detector.py not found")
        print("   Make sure you're running this from the project root directory")
        return 1
    
    benchmark = SimpleBenchmark()
    
    try:
        # Run evaluation
        results = benchmark.run_full_evaluation()
        
        # Generate and save report
        report = benchmark.generate_report(results)
        
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        benchmark.print_summary(results)
        
        print(f"\n📊 Detailed results saved to: {args.output}")
        print("\n🎯 Key Insights:")
        
        successful = [r for r in results if r.error is None]
        if successful:
            avg_throughput = sum(r.functions_analyzed / r.execution_time for r in successful) / len(successful)
            print(f"   Average processing speed: {avg_throughput:.1f} functions/second")
            
            if avg_throughput > 0:
                time_for_5000 = 5000 / avg_throughput
                print(f"   Estimated time for 5000 functions: {time_for_5000/60:.1f} minutes")
                
                if time_for_5000 > 300:  # 5 minutes
                    print(f"   ⚠️  Performance issue confirmed: {time_for_5000/60:.1f} min > 5 min target")
                    print(f"   💡 Consider optimizations like:")
                    print(f"      - Reducing similarity threshold")
                    print(f"      - Limiting file patterns")
                    print(f"      - Using incremental analysis")
                else:
                    print(f"   ✅ Performance is within acceptable range")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️  Evaluation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
