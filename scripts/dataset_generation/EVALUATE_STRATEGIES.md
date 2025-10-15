# Similarity Strategy Evaluation

This document describes how to use the `evaluate-strategies` command to evaluate different similarity strategies for duplicate code detection.

## 🎯 Overview

The `evaluate-strategies` command analyzes a dataset of function pairs and evaluates the performance of different similarity methods:

- **Jaccard Tokens**: Token-based Jaccard similarity coefficient
- **Sequence Matcher**: Python's difflib.SequenceMatcher algorithm  
- **Levenshtein Normalized**: Normalized Levenshtein distance similarity

The evaluation uses machine learning metrics to determine which strategy performs best on your specific dataset.

## 📦 Installation

Install the evaluation dependencies:

```bash
# Install evaluation dependencies
uv pip install -e ".[evaluation]"

# Or with pip
pip install -e ".[evaluation]"
```

## 🚀 Quick Start

### Basic Usage

```bash
# Evaluate strategies on a dataset
uv run evaluate-strategies --dataset dataset.json
```

### Advanced Usage

```bash
# Verbose output with CSV export
uv run evaluate-strategies --dataset my_dataset.json --output-csv results.csv --verbose
```

## 📋 Command Reference

### Required Arguments

- `--dataset`: Path to JSON dataset file containing function pairs with `func1`, `func2`, and `clone` columns

### Optional Arguments

- `--output-csv`: Path to save detailed results as CSV file
- `--verbose`: Enable verbose output with progress information

## 📊 Dataset Format

The dataset should be a JSON file with the following structure:

```json
[
    {
        "func1": "def example_function():\n    return True",
        "func2": "def another_function():\n    return True", 
        "clone": true
    },
    {
        "func1": "def different_function():\n    return False",
        "func2": "def unrelated_function():\n    print('hello')",
        "clone": false
    }
]
```

### Required Columns

- `func1`: Source code of the first function (string)
- `func2`: Source code of the second function (string) 
- `clone`: Whether the functions are clones/duplicates (boolean)

## 📈 Output Metrics

The command evaluates each strategy using the following metrics:

### Primary Metrics
- **F1 Score**: Harmonic mean of precision and recall (primary ranking metric)
- **ROC-AUC**: Area under the ROC curve
- **PR-AUC**: Area under the Precision-Recall curve

### Secondary Metrics
- **Best Threshold**: Optimal similarity threshold for F1 score
- **Accuracy**: Overall classification accuracy at best threshold
- **Precision**: Precision at best F1 threshold
- **Recall**: Recall at best F1 threshold

## 🏆 Results Interpretation

### Strategy Recommendations

Based on the evaluation results, you'll receive recommendations:

**Levenshtein Distance** - Best for:
- Highest precision requirements
- Catching subtle duplicates
- Strict duplicate detection

**Jaccard Tokens** - Best for:
- Balanced speed and accuracy
- General-purpose duplicate detection
- Production environments

**Sequence Matcher** - Best for:
- Structural similarity detection
- Pattern-based matching
- Code structure analysis

### Example Output

```
================================================================================
🏆 BEST STRATEGY: LEVENSHTEIN_NORM
================================================================================
📊 F1 Score: 0.7755
📊 ROC-AUC: 0.9916
📊 PR-AUC: 0.7176
📊 Best Threshold: 0.3734
📊 Accuracy: 0.9948
📊 Precision: 0.6786
📊 Recall: 0.8962

💡 RECOMMENDATIONS:
• Use Levenshtein Distance for highest precision
• Best for catching subtle duplicates  
• Set similarity threshold to 0.3734
• Expected to achieve 77.6% F1 score on similar data
```

## 🔧 Integration with Duplicate Detector

Use the evaluation results to configure your duplicate detection:

```bash
# Use the recommended strategy and threshold
export SIMILARITY_METHOD="levenshtein_norm"
export GLOBAL_THRESHOLD="0.3734"

# Run duplicate detection
uv run duplicate-logic-detector --similarity-method levenshtein_norm --global-threshold 0.3734
```

## 📝 Examples

### Example 1: Basic Evaluation

```bash
# Evaluate strategies on your dataset
uv run evaluate-strategies --dataset my_clone_pairs.json
```

### Example 2: Detailed Analysis

```bash
# Get verbose output and save results
uv run evaluate-strategies \
  --dataset balanced_dataset.json \
  --output-csv detailed_metrics.csv \
  --verbose
```

### Example 3: Batch Processing

```bash
# Evaluate multiple datasets
for dataset in datasets/*.json; do
    echo "Evaluating $dataset..."
    uv run evaluate-strategies \
      --dataset "$dataset" \
      --output-csv "results/$(basename "$dataset" .json)_results.csv"
done
```

## 🧪 Creating Test Datasets

You can create datasets using the dataset generation tools:

```bash
# Step 1: Generate clones
uv run generate-clones --source-code ./src --dest-folder clones --n-clones 3

# Step 2: Build balanced dataset  
uv run build-dataset --clones-folder clones --dataset-name test_dataset.json --clone-ratio 0.5

# Step 3: Evaluate strategies
uv run evaluate-strategies --dataset test_dataset.json --verbose
```

## 🚨 Troubleshooting

### Common Issues

**Dataset format errors:**
- Ensure JSON is valid and contains required columns
- Check that `func1` and `func2` contain valid Python code
- Verify `clone` column contains boolean values

**Performance issues:**
- Large datasets (>50K pairs) may take several minutes
- Use `--verbose` to monitor progress
- Consider sampling large datasets for faster evaluation

**Memory issues:**
- For very large datasets, consider splitting into smaller chunks
- Monitor system memory usage during evaluation

### Error Messages

- `Missing required columns`: Dataset missing `func1`, `func2`, or `clone` columns
- `No valid scores`: All similarity calculations failed (check code syntax)
- `Dataset file not found`: Verify the dataset path is correct

## 📚 Related Commands

- `generate-clones`: Generate function clones for dataset creation
- `build-dataset`: Build balanced datasets from generated clones  
- `duplicate-logic-detector`: Run duplicate detection with chosen strategy

## 🤝 Contributing

When adding new similarity strategies:

1. Add the strategy to `SimilarityEvaluator` class
2. Update the methods dictionary in `evaluate_all_strategies()`
3. Add strategy description in the recommendations section
4. Update this documentation

For questions or issues, please refer to the main project documentation.
