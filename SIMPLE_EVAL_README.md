¬# Simple Evaluation for Duplicate Logic Detection


This is a simplified evaluation tool to benchmark your current duplicate logic detection implementation and understand why it takes 5 minutes on large codebases.

## Quick Start

### 1. Install dependencies
```bash
pip install -r eval_requirements.txt
```

### 2. Run the evaluation
```bash
python eval_simple.py
```

### 3. View results
The script will show real-time progress and generate a summary with performance metrics.

## What it does

The evaluation:

1. **Creates test datasets** with known duplicates:
   - Small: 10 files, 200 functions
   - Medium: 50 files, 1,000 functions  
   - Large: 100 files, 2,500 functions

2. **Runs your current implementation** on each dataset

3. **Measures performance**:
   - Execution time
   - Memory usage
   - Functions processed per second
   - Scalability (how performance changes with size)

4. **Provides insights**:
   - Identifies performance bottlenecks
   - Projects time for different codebase sizes
   - Shows where the 5-minute issue comes from

## Sample Output

```
🚀 Running Simple Duplicate Detection Evaluation
==================================================

📁 Creating small dataset (10 files, 20 functions each)...
  ✅ Created dataset at eval_datasets/small
  Running benchmark on small...
  ✅ Completed in 12.3s
     Memory: 45.2 MB
     Functions/sec: 16.3
     Duplicates found: 12

📁 Creating medium dataset (50 files, 20 functions each)...
  ✅ Created dataset at eval_datasets/medium
  Running benchmark on medium...
  ✅ Completed in 67.8s
     Memory: 156.7 MB
     Functions/sec: 14.7
     Duplicates found: 58

📁 Creating large dataset (100 files, 25 functions each)...
  ✅ Created dataset at eval_datasets/large
  Running benchmark on large...
  ✅ Completed in 284.5s
     Memory: 312.4 MB
     Functions/sec: 8.8
     Duplicates found: 125

============================================================
EVALUATION SUMMARY
============================================================
✅ Successful runs: 3
❌ Failed runs: 0

Performance Results:
Dataset    Time     Memory     Functions  Throughput   Duplicates
----------------------------------------------------------------------
small        12.3s     45.2MB       200       16.3/s         12
medium       67.8s    156.7MB      1000       14.7/s         58
large       284.5s    312.4MB      2500        8.8/s        125

📈 Scalability Analysis:
   Dataset size increased 12.5x
   Execution time increased 23.1x
   Efficiency: 0.54 (1.0 = linear scaling)
   Projected time for 5000 functions: 9.5 minutes

🎯 Key Insights:
   Average processing speed: 13.3 functions/second
   Estimated time for 5000 functions: 6.3 minutes
   ⚠️  Performance issue confirmed: 6.3 min > 5 min target
   💡 Consider optimizations like:
      - Reducing similarity threshold
      - Limiting file patterns
      - Using incremental analysis
```

## Understanding the Results

### Performance Metrics

- **Execution Time**: How long the analysis takes
- **Memory Usage**: Peak memory consumption
- **Throughput**: Functions analyzed per second
- **Scalability**: How performance degrades with larger codebases

### Key Insights

The evaluation will show you:

1. **Where the bottleneck is**: Processing speed (functions/second)
2. **How it scales**: Linear vs exponential time growth
3. **Memory impact**: Whether memory is a limiting factor
4. **Projected performance**: Time estimates for your actual codebase size

### Typical Issues Found

**If you see:**
- **Low throughput** (< 10 functions/sec): Algorithm is inefficient
- **Poor scalability** (efficiency < 0.8): Quadratic time complexity
- **High memory usage**: TF-IDF vectors consuming too much RAM
- **Exponential time growth**: Full codebase indexing is the bottleneck

## Quick Options

```bash
# Quick test (skip large dataset)
python eval_simple.py --skip-large

# Save results to custom file
python eval_simple.py --output my_results.json

# View detailed JSON results
cat eval_results.json | python -m json.tool
```

## Next Steps Based on Results

### If throughput is < 10 functions/second:
- Consider reducing similarity thresholds
- Limit file patterns in configuration
- Profile the TF-IDF vectorization step

### If scalability efficiency is < 0.7:
- The algorithm has quadratic complexity
- Consider incremental analysis (only new functions vs existing)
- Implement early termination for obvious non-matches

### If memory usage is high (> 500MB):
- TF-IDF vectors are too large
- Consider using simpler similarity metrics
- Implement function filtering before analysis

## Files Generated

- `eval_datasets/`: Test datasets with ground truth
- `eval_results.json`: Detailed performance data
- Individual result files in dataset directories

## Troubleshooting

**Script not found error:**
```bash
# Make sure you're in the project root
ls scripts/duplicate_logic_detector.py
```

**Import errors:**
```bash
# Install dependencies
pip install -r eval_requirements.txt
```

**Timeout issues:**
```bash
# Test with smaller dataset first
python eval_simple.py --skip-large
```

This simple evaluation will give you concrete data about why your current implementation takes 5 minutes and help identify the specific bottlenecks to address.
