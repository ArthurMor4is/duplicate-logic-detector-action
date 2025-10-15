# Dataset Generation for Duplicate Logic Detection

This module provides tools to generate datasets of function clones, helping users test and choose the best strategies for duplicate detection in their codebase.

## 🎯 Overview

The dataset generation process consists of two main steps:

1. **Clone Generation** (`generate_clones.py`): Creates function clones using LLM (Large Language Models)
2. **Dataset Building** (`build_dataset.py`): Builds balanced datasets from generated clones

## 📦 Installation

Install the dataset generation dependencies:

```bash
# Install dataset generation dependencies
uv pip install -e ".[dataset]"

# Or with pip
pip install -e ".[dataset]"
```

## 🚀 Quick Start

### Step 1: Generate Function Clones

Generate clones from your Python codebase:

```bash
# Basic usage
uv run generate-clones --source-code "./src" --dest-folder="clones_output" --n-clones=3

# Advanced usage with multiple source folders
uv run generate-clones \
  --source-code "./src/shared/validators" "./lib/utils" \
  --dest-folder="generated_clones" \
  --n-clones=2 \
  --n-modules=10 \
  --seed=42 \
  --model="gpt-4-turbo" \
  --verbose
```

### Step 2: Build Dataset

Create a balanced dataset from generated clones:

```bash
# Basic usage
build-dataset --clones-folder="clones_output" --dataset-name="functions_clone_pairs.json"

# Advanced usage with custom balance
build-dataset \
  --clones-folder="generated_clones" \
  --dataset-name="balanced_dataset.json" \
  --clone-ratio=0.3 \
  --format=json \
  --seed=42 \
  --verbose
```

## 📋 Detailed Usage

### Generate Clones (`generate_clones.py`)

Creates function clones using OpenAI's GPT models.

#### Required Arguments
- `--source-code`: Path(s) to folder(s) containing Python source code
- `--dest-folder`: Destination folder for generated clone files

#### Optional Arguments
- `--n-clones`: Number of clones per function (default: 2)
- `--seed`: Random seed for reproducible results (default: 42)
- `--model`: OpenAI model to use (default: "gpt-4-turbo")
- `--api-key`: OpenAI API key (set via environment variable recommended)
- `--n-modules`: Number of random modules to select (default: use all)
- `--verbose`: Enable verbose output
- `--dry-run`: Show what would be done without creating files

#### Environment Variables
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

#### Example Output
```
clones_output/
├── calculate_total_dataset.py    # Original + clones for calculate_total
├── validate_email_dataset.py     # Original + clones for validate_email
└── process_data_dataset.py       # Original + clones for process_data
```

### Build Dataset (`build_dataset.py`)

Creates balanced datasets from generated clone files.

#### Required Arguments
- `--clones-folder`: Path to folder containing generated clone files
- `--dataset-name`: Name of the output dataset file

#### Optional Arguments
- `--seed`: Random seed for reproducible sampling (default: 42)
- `--format`: Output format - 'json', 'parquet', or 'csv' (default: 'json')
- `--clone-ratio`: Ratio of true clones in dataset (default: 0.5)
- `--verbose`: Enable verbose output

#### Dataset Format
The generated dataset contains pairs of functions with the following structure:

```json
[
  {
    "func1": "def original_function(x):\n    return x * 2",
    "func2": "def cloned_function(value):\n    result = value * 2\n    return result",
    "func1_name": "original_function",
    "func2_name": "cloned_function", 
    "clone": true,
    "source_module1": "module1_dataset.py",
    "source_module2": "module1_dataset.py"
  },
  {
    "func1": "def function_a(data):\n    return len(data)",
    "func2": "def function_b(items):\n    return sum(items)",
    "func1_name": "function_a",
    "func2_name": "function_b",
    "clone": false,
    "source_module1": "module1_dataset.py",
    "source_module2": "module2_dataset.py"
  }
]
```

## 🔧 Configuration

### Clone Generation Configuration

The clone generation process can be customized through various parameters:

- **Model Selection**: Choose between different OpenAI models
  - `gpt-4-turbo`: Best quality, higher cost
  - `gpt-3.5-turbo`: Good quality, lower cost
  
- **Clone Diversity**: Control the number and variety of clones
  - Higher `n-clones` values create more diverse datasets
  - Different `seed` values produce different random selections

### Dataset Balance Configuration

Control the balance between true clones and false clones:

- `--clone-ratio=0.5`: 50% true clones, 50% false clones (balanced)
- `--clone-ratio=0.3`: 30% true clones, 70% false clones (unbalanced)
- `--clone-ratio=1.0`: Only true clones
- `--clone-ratio=0.0`: Only false clones

## 📊 Use Cases

### 1. Testing Similarity Algorithms

Generate datasets to test different similarity detection methods:

```bash
# Generate diverse clones for algorithm testing
generate-clones --source-code "./src" --dest-folder="test_clones" --n-clones=5
build-dataset --clones-folder="test_clones" --dataset-name="similarity_test.json" --clone-ratio=0.5
```

### 2. Threshold Tuning

Create datasets with different balance ratios to tune detection thresholds:

```bash
# Create unbalanced dataset (more false positives)
build-dataset --clones-folder="clones" --dataset-name="unbalanced.json" --clone-ratio=0.2

# Create balanced dataset
build-dataset --clones-folder="clones" --dataset-name="balanced.json" --clone-ratio=0.5
```

### 3. Model Evaluation

Generate consistent datasets for reproducible model evaluation:

```bash
# Use fixed seed for reproducible results
generate-clones --source-code "./src" --dest-folder="eval_clones" --seed=12345
build-dataset --clones-folder="eval_clones" --dataset-name="evaluation.json" --seed=12345
```

## ⚠️ Known Limitations

### Duplicate Function/Method Names

**Important**: If your source code contains multiple functions or methods with the **same name** in a single module (e.g., method overloading across different classes), only **one** of them will be selected for clone generation.

**Example of the limitation**:
```python
# module.py
class UserValidator:
    def validate(self, user):  # Only this validate OR the one below will be selected
        return user.is_active

class AdminValidator:
    def validate(self, admin):  # This might be skipped if the above is chosen
        return admin.has_permissions
```

**Why this happens**: 
- The clone generation randomly selects one function/method name from each module
- When extracting the source code, if multiple functions share the same name, only the first match found by `ast.walk()` will be used
- This is because the selection is based on function names, not full qualified names (e.g., `ClassName.method_name`)

**Workaround**:
1. Ensure unique function/method names across your source code when generating datasets
2. Manually select specific modules with unique names
3. Or accept that some methods may be skipped in the random selection

**Future Enhancement**: This could be improved by using fully qualified names (class.method) instead of just method names for selection.

## 🔍 Quality Control

### Manual Review Process

1. **Generated Clones Review**: After running `generate-clones`, manually review the generated files:
   - Check for syntax errors
   - Verify functional equivalence
   - Remove or fix problematic clones

2. **Dataset Validation**: After running `build-dataset`:
   - Verify dataset balance matches expectations
   - Check for duplicate pairs
   - Validate JSON structure

### Automated Quality Checks

The scripts include built-in quality checks:
- Syntax validation for generated clones
- Duplicate pair detection
- Balance ratio verification
- Output format validation

## 🐛 Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   ```bash
   Error calling OpenAI API: Invalid API key
   ```
   **Solution**: Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

2. **No Functions Found**
   ```bash
   Error: No functions found to clone
   ```
   **Solution**: Ensure your source code contains top-level Python functions.

3. **Syntax Errors in Generated Clones**
   ```bash
   WARNING: Clone 1 for function_name has syntax errors
   ```
   **Solution**: Review and manually fix the generated clones before building the dataset.

### Debug Mode

Enable verbose output for detailed debugging:

```bash
generate-clones --source-code "./src" --dest-folder="debug_clones" --verbose
build-dataset --clones-folder="debug_clones" --dataset-name="debug.json" --verbose
```

## 🤝 Integration with Main Action

The generated datasets can be used to:

1. **Test Similarity Methods**: Evaluate different similarity algorithms available in the main action
2. **Tune Thresholds**: Find optimal threshold values for your codebase
3. **Validate Detection**: Ensure the action works correctly on your specific code patterns

Example workflow:
```bash
# 1. Generate test dataset
generate-clones --source-code "./your-project/src" --dest-folder="test_data"
build-dataset --clones-folder="test_data" --dataset-name="validation.json"

# 2. Test with different similarity methods
duplicate-logic-detector --similarity-method="jaccard_tokens" --global-threshold=0.7
duplicate-logic-detector --similarity-method="levenshtein_norm" --global-threshold=0.8

# 3. Compare results against your validation dataset
```

## 📚 API Reference

For programmatic usage, import the functions directly:

```python
from scripts.dataset_generation import (
    create_clones_dataset_for_methods,
    build_function_clone_dataset,
    extract_function_names,
    select_random_modules_with_functions,
)

# Generate clones programmatically
methods = [("def example():\n    pass", "example")]
create_clones_dataset_for_methods(
    methods=methods,
    n_clones=3,
    output_folder="./output",
    openai_api_key="your-key",
    gpt_model="gpt-4-turbo"
)

# Build dataset programmatically  
build_function_clone_dataset(
    folder_path="./output",
    output_path="dataset.json",
    seed=42,
    format="json",
    clone_ratio=0.5
)
```

## 📄 License

This module is part of the duplicate-logic-detector-action project and is licensed under the MIT License.
