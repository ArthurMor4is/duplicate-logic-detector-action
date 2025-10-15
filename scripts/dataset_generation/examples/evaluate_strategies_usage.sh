#!/bin/bash
# Similarity Strategy Evaluation Examples
# This script demonstrates different ways to use the evaluate-strategies command

set -euo pipefail

echo "🚀 Similarity Strategy Evaluation Examples"
echo "=========================================="

# Configuration
DATASET_FILE="scripts/dataset.json"
OUTPUT_CSV="strategy_evaluation_results.csv"

# Check if dataset file exists
if [ ! -f "$DATASET_FILE" ]; then
    echo "❌ Error: Dataset file '$DATASET_FILE' not found"
    echo "Please ensure you have a dataset JSON file with 'func1', 'func2', and 'clone' columns"
    exit 1
fi

echo "📂 Dataset file: $DATASET_FILE"
echo ""

# Example 1: Basic evaluation
echo "📋 Example 1: Basic evaluation"
echo "------------------------------"
echo "Command: uv run evaluate-strategies --dataset $DATASET_FILE"
echo ""
uv run evaluate-strategies --dataset "$DATASET_FILE"
echo ""

# Example 2: Verbose output with CSV export
echo "📋 Example 2: Verbose output with CSV export"
echo "--------------------------------------------"
echo "Command: uv run evaluate-strategies --dataset $DATASET_FILE --output-csv $OUTPUT_CSV --verbose"
echo ""
uv run evaluate-strategies --dataset "$DATASET_FILE" --output-csv "$OUTPUT_CSV" --verbose

if [ -f "$OUTPUT_CSV" ]; then
    echo ""
    echo "✅ CSV results saved to: $OUTPUT_CSV"
    echo "📊 CSV contents:"
    head -5 "$OUTPUT_CSV"
    echo ""
fi

# Example 3: Using with custom dataset
echo "📋 Example 3: Usage patterns"
echo "----------------------------"
echo "# For balanced datasets:"
echo "uv run evaluate-strategies --dataset balanced_clone_pairs.json"
echo ""
echo "# For unbalanced datasets with detailed output:"
echo "uv run evaluate-strategies --dataset unbalanced_dataset.json --verbose --output-csv detailed_results.csv"
echo ""
echo "# Quick evaluation without verbose output:"
echo "uv run evaluate-strategies --dataset my_dataset.json"
echo ""

echo "🎉 Examples completed!"
echo ""
echo "💡 Tips:"
echo "• The command evaluates jaccard_tokens, sequence_matcher, and levenshtein_norm strategies"
echo "• Results are sorted by F1 score (primary), then PR-AUC, then ROC-AUC"
echo "• The best strategy is highlighted at the end with recommendations"
echo "• Use --output-csv to save detailed metrics for further analysis"
echo "• Use --verbose for detailed progress information"
