#!/bin/bash
# Advanced Dataset Generation Example
# This script demonstrates advanced features and multiple dataset generation

set -euo pipefail

echo "🚀 Advanced Dataset Generation Example"
echo "======================================"

# Configuration
SOURCE_FOLDERS=("./src/shared/validators" "./lib/utils" "./app/core")
BASE_OUTPUT="./advanced_clones"
N_CLONES=3
N_MODULES=15
SEED=42

# Check if OpenAI API key is set
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "❌ Error: OPENAI_API_KEY environment variable is not set"
    echo "Please set your OpenAI API key:"
    echo "export OPENAI_API_KEY='your-openai-api-key-here'"
    exit 1
fi

# Verify source folders exist (create dummy ones for demo)
echo "📂 Setting up source folders..."
for folder in "${SOURCE_FOLDERS[@]}"; do
    if [ ! -d "$folder" ]; then
        echo "⚠️  Creating demo folder: $folder"
        mkdir -p "$folder"
        # Create a sample Python file
        cat > "$folder/sample_$(basename "$folder").py" << 'EOF'
def calculate_sum(numbers):
    """Calculate the sum of a list of numbers."""
    total = 0
    for num in numbers:
        total += num
    return total

def validate_email(email):
    """Basic email validation."""
    if "@" not in email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    return True

def process_data(data):
    """Process a list of data items."""
    result = []
    for item in data:
        if isinstance(item, str):
            result.append(item.upper())
        elif isinstance(item, int):
            result.append(item * 2)
    return result
EOF
    fi
done

echo ""

# Generate multiple datasets with different configurations
datasets=(
    "balanced:0.5:Balanced dataset (50% clones)"
    "unbalanced:0.3:Unbalanced dataset (30% clones)" 
    "heavy_clones:0.7:Clone-heavy dataset (70% clones)"
    "minimal_clones:0.1:Minimal clones dataset (10% clones)"
)

for dataset_config in "${datasets[@]}"; do
    IFS=':' read -r name ratio description <<< "$dataset_config"
    
    echo "🔄 Generating $description..."
    echo "   Name: $name"
    echo "   Clone ratio: $ratio"
    
    OUTPUT_FOLDER="${BASE_OUTPUT}_${name}"
    DATASET_NAME="${name}_clone_dataset.json"
    
    # Step 1: Generate clones (only once for the first dataset)
    if [ "$name" = "balanced" ]; then
        echo "   📥 Generating function clones..."
        
        # Convert array to space-separated string
        source_args=""
        for folder in "${SOURCE_FOLDERS[@]}"; do
            source_args="$source_args --source-code $folder"
        done
        
        generate-clones \
            $source_args \
            --dest-folder "$OUTPUT_FOLDER" \
            --n-clones "$N_CLONES" \
            --n-modules "$N_MODULES" \
            --seed "$SEED" \
            --model "gpt-4-turbo" \
            --verbose
        
        if [ $? -ne 0 ]; then
            echo "❌ Error: Clone generation failed for $name"
            continue
        fi
        
        # Copy clones to other output folders
        for other_config in "${datasets[@]}"; do
            IFS=':' read -r other_name _ _ <<< "$other_config"
            if [ "$other_name" != "balanced" ]; then
                OTHER_OUTPUT="${BASE_OUTPUT}_${other_name}"
                echo "   📋 Copying clones to $OTHER_OUTPUT..."
                cp -r "$OUTPUT_FOLDER" "$OTHER_OUTPUT"
            fi
        done
    fi
    
    # Step 2: Build dataset with specific ratio
    echo "   📊 Building dataset..."
    build-dataset \
        --clones-folder "$OUTPUT_FOLDER" \
        --dataset-name "$DATASET_NAME" \
        --clone-ratio "$ratio" \
        --format json \
        --seed "$SEED" \
        --verbose
    
    if [ $? -ne 0 ]; then
        echo "❌ Error: Dataset building failed for $name"
        continue
    fi
    
    echo "   ✅ $description completed"
    echo ""
done

# Generate additional format examples
echo "🔄 Generating format examples..."

# Parquet format
echo "   📦 Creating Parquet format dataset..."
build-dataset \
    --clones-folder "${BASE_OUTPUT}_balanced" \
    --dataset-name "balanced_dataset.parquet" \
    --clone-ratio 0.5 \
    --format parquet \
    --seed "$SEED" \
    --verbose

# CSV format (not recommended but available)
echo "   📄 Creating CSV format dataset..."
build-dataset \
    --clones-folder "${BASE_OUTPUT}_balanced" \
    --dataset-name "balanced_dataset.csv" \
    --clone-ratio 0.5 \
    --format csv \
    --seed "$SEED" \
    --verbose

echo ""

# Summary
echo "🎉 Advanced dataset generation completed!"
echo ""
echo "📊 Generated datasets:"
for dataset_config in "${datasets[@]}"; do
    IFS=':' read -r name ratio description <<< "$dataset_config"
    echo "   - ${name}_clone_dataset.json ($description)"
done
echo "   - balanced_dataset.parquet (Parquet format)"
echo "   - balanced_dataset.csv (CSV format)"
echo ""

echo "📁 Generated clone folders:"
for dataset_config in "${datasets[@]}"; do
    IFS=':' read -r name _ _ <<< "$dataset_config"
    echo "   - ${BASE_OUTPUT}_${name}/"
done
echo ""

echo "🧪 Testing suggestions:"
echo "   1. Use different datasets to test algorithm performance"
echo "   2. Compare results across different clone ratios"
echo "   3. Evaluate threshold sensitivity with unbalanced datasets"
echo ""

echo "💡 Example testing workflow:"
echo "   # Test with balanced dataset"
echo "   duplicate-logic-detector --similarity-method=jaccard_tokens --global-threshold=0.7"
echo ""
echo "   # Test with unbalanced dataset (more false positives expected)"
echo "   duplicate-logic-detector --similarity-method=levenshtein_norm --global-threshold=0.6"
echo ""
echo "   # Test with clone-heavy dataset (tune for precision)"
echo "   duplicate-logic-detector --similarity-method=sequence_matcher --global-threshold=0.8"
