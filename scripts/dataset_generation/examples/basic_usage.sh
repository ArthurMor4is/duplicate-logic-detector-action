#!/bin/bash
# Basic Dataset Generation Example
# This script demonstrates the most common use case for dataset generation

set -euo pipefail

echo "🚀 Basic Dataset Generation Example"
echo "=================================="

# Configuration
SOURCE_FOLDER="./src"
OUTPUT_FOLDER="./clones_basic"
DATASET_NAME="basic_clone_dataset.json"
N_CLONES=2
CLONE_RATIO=0.5

# Check if source folder exists
if [ ! -d "$SOURCE_FOLDER" ]; then
    echo "❌ Error: Source folder '$SOURCE_FOLDER' does not exist"
    echo "Please create a 'src' folder with Python files, or modify SOURCE_FOLDER variable"
    exit 1
fi

# Check if OpenAI API key is set
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "❌ Error: OPENAI_API_KEY environment variable is not set"
    echo "Please set your OpenAI API key:"
    echo "export OPENAI_API_KEY='your-openai-api-key-here'"
    exit 1
fi

echo "📂 Source folder: $SOURCE_FOLDER"
echo "📁 Output folder: $OUTPUT_FOLDER"
echo "📄 Dataset name: $DATASET_NAME"
echo "🔢 Clones per function: $N_CLONES"
echo "⚖️  Clone ratio: $CLONE_RATIO"
echo ""

# Step 1: Generate function clones
echo "🔄 Step 1: Generating function clones..."
generate-clones \
    --source-code "$SOURCE_FOLDER" \
    --dest-folder "$OUTPUT_FOLDER" \
    --n-clones "$N_CLONES" \
    --seed 42 \
    --verbose

if [ $? -ne 0 ]; then
    echo "❌ Error: Clone generation failed"
    exit 1
fi

echo "✅ Clone generation completed"
echo ""

# Step 2: Build dataset
echo "🔄 Step 2: Building dataset..."
build-dataset \
    --clones-folder "$OUTPUT_FOLDER" \
    --dataset-name "$DATASET_NAME" \
    --clone-ratio "$CLONE_RATIO" \
    --format json \
    --seed 42 \
    --verbose

if [ $? -ne 0 ]; then
    echo "❌ Error: Dataset building failed"
    exit 1
fi

echo "✅ Dataset building completed"
echo ""

# Summary
echo "🎉 Dataset generation completed successfully!"
echo "📊 Generated files:"
echo "   - Clone modules: $OUTPUT_FOLDER/"
echo "   - Dataset file: $DATASET_NAME"
echo ""
echo "📋 Next steps:"
echo "   1. Review the generated clones in '$OUTPUT_FOLDER/'"
echo "   2. Check the dataset file '$DATASET_NAME'"
echo "   3. Use the dataset to test similarity algorithms"
echo ""
echo "💡 Example usage with duplicate-logic-detector:"
echo "   duplicate-logic-detector --similarity-method=jaccard_tokens --global-threshold=0.7"
