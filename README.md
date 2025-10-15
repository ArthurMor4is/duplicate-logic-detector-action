# 🔍 Duplicate Logic Detector Action

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Duplicate%20Logic%20Detector-blue.svg?colorA=24292e&colorB=0366d6&style=flat&longCache=true&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAM6wAADOsB5dZE0gAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAERSURBVCiRhZG/SsMxFEZPfsVJ61jbxaF0cRQRcRJ9hlYn30IHN/+9iquDCOIsblIrOjqKgy5aKoJQj4n3EX8DzMMmdU3ruAQfOQlee/XrgHdogK0aaQq6gRSFq2y2+fEdMQPMfnNwlWpWJYbBfC3QRGGYHrPr/TlZjPb7NNM02P9M3s2BNb/uuEOPiN1vUoJ+3Pqz1rvqg1XvFINL4KmNXFMaSID2G7yyHSWqMXpSXEMhNRDOBOb2g3xE6F2nQfMnUNSvDEwHiQeKq8l8o+zJW0FGJHZiJSJ6jH1qmHVYOTiCsXzxnmBFYt8y5Yb1CzWjZGZq7/dkb8+PrNrBdWMHyoJgvjJnxBSoUQSdNjLgxfbGSr5aBvXGNvQFHxzJVRqxJb5EJg9dn8AQqTwP2JQoqQAAAABJRU5ErkJggg==)](https://github.com/marketplace/actions/duplicate-logic-detector)
[![Tests](https://github.com/ArthurMor4is/duplicate-logic-detector-action/workflows/Test%20Action/badge.svg)](https://github.com/ArthurMor4is/duplicate-logic-detector-action/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Automatically detect duplicate logic in Python code changes using advanced AST analysis and semantic similarity.**

Prevent code duplication, improve code quality, and maintain cleaner codebases with intelligent duplicate detection that goes beyond simple text matching.

## ✨ Key Features

- 🧠 **Multi-Strategy Detection**: AST analysis, semantic similarity, and function signature matching
- 🎯 **Smart Pattern Recognition**: Detects business logic patterns and common code structures
- 💬 **Actionable PR Comments**: Provides suggestions and refactoring recommendations
- ⚙️ **Highly Configurable**: Adjustable similarity thresholds and file patterns
- 📊 **Comprehensive Reports**: JSON and Markdown reports with detailed analysis
- 🚀 **Fast & Efficient**: Uses uv package manager for lightning-fast dependency installation
- 💬 **Feedback Collection**: Automatically collects user reactions to improve detection quality

## 🚀 Quick Start

Add this workflow to `.github/workflows/duplicate-detection.yml`:

```yaml
name: Duplicate Logic Detection

on:
  pull_request:
    paths: ['**/*.py']

jobs:
  detect-duplicates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - name: Detect Duplicate Logic
        uses: ArthurMor4is/duplicate-logic-detector-action@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## 📋 Input Parameters

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `github-token` | GitHub token for API access | ✅ | `${{ github.token }}` |
| `pr-number` | Pull request number | ❌ | `${{ github.event.number }}` |
| `repository` | Repository name (owner/repo) | ❌ | `${{ github.repository }}` |
| `base-ref` | Base reference for comparison | ❌ | `${{ github.base_ref }}` |
| `head-ref` | Head reference for comparison | ❌ | `${{ github.head_ref }}` |
| `post-comment` | Post findings as PR comment | ❌ | `true` |
| `fail-on-duplicates` | Fail if high-confidence duplicates found | ❌ | `false` |
| `similarity-method` | Similarity method to use (`jaccard_tokens`, `sequence_matcher`, `levenshtein_norm`) | ❌ | `jaccard_tokens` |
| `global-threshold` | Global similarity threshold (0.0-1.0) for all methods | ❌ | `0.7` |
| `folder-thresholds` | Per-folder thresholds as JSON (e.g., `{"src/shared": 0.1, "src/tests": 0.9}`) | ❌ | `{}` |

## 📊 Outputs

| Output | Description |
|--------|-------------|
| `duplicates-found` | Whether any duplicates were detected |
| `match-count` | Total number of matches found |
| `report-path` | Path to the generated report file |

## ⚙️ Usage Examples

### Basic Usage
```yaml
- name: Detect Duplicate Logic
  uses: ArthurMor4is/duplicate-logic-detector-action@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Strict Mode (Fail on Duplicates)
```yaml
- name: Detect Duplicate Logic
  uses: ArthurMor4is/duplicate-logic-detector-action@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    fail-on-duplicates: true
```

### Silent Mode (No PR Comments)
```yaml
- name: Detect Duplicate Logic
  uses: ArthurMor4is/duplicate-logic-detector-action@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    post-comment: false
```

### Custom Similarity Method
```yaml
- name: Detect Duplicate Logic (High Precision)
  uses: ArthurMor4is/duplicate-logic-detector-action@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    similarity-method: levenshtein_norm  # More thorough analysis
    fail-on-duplicates: true
```

### Custom Threshold Configuration
```yaml
- name: Detect Duplicate Logic (Custom Thresholds)
  uses: ArthurMor4is/duplicate-logic-detector-action@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    global-threshold: 0.8  # Higher threshold for stricter detection
    folder-thresholds: '{"src/shared": 0.1, "src/tests": 0.9}'
```

### Per-Folder Threshold Configuration
```yaml
- name: Detect Duplicate Logic (Folder-Specific Thresholds)
  uses: ArthurMor4is/duplicate-logic-detector-action@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    similarity-method: jaccard_tokens
    folder-thresholds: '{"src/shared": 0.1, "src/core": 0.8, "tests": 0.9}'
```

## 🔍 Detection Strategies

The action uses configurable similarity analysis to detect duplicate logic patterns:

### 1. AST Analysis
- Parses Python files to extract function definitions
- Analyzes function signatures and structure
- Identifies code patterns and complexity

### 2. Similarity Methods
Choose from three different similarity algorithms:

#### `jaccard_tokens` (Default)
- **Best for**: General purpose, fast analysis
- **Method**: Token-based Jaccard similarity coefficient
- **Strengths**: Fast, good balance of precision/recall
- **Use when**: You want reliable results with good performance

#### `sequence_matcher`
- **Best for**: Balanced approach between speed and accuracy
- **Method**: Python's difflib.SequenceMatcher
- **Strengths**: Good at detecting structural similarities
- **Use when**: You need more nuanced similarity detection

#### `levenshtein_norm`
- **Best for**: High precision, strict duplicate detection
- **Method**: Normalized Levenshtein distance
- **Strengths**: Most thorough analysis, best precision
- **Use when**: You want to catch even subtle duplicates

### 3. Smart Filtering
- Excludes very small functions (< 5 lines)
- Filters out test files and common patterns
- Prioritizes business logic and complex functions

### 4. Configurable Thresholds
Control when functions are considered duplicates with flexible threshold settings:

#### Global Threshold
- **Default**: `0.7` (70% similarity)
- **Usage**: Applies to all files when no folder-specific threshold is set
- **Range**: `0.0` to `1.0` (0% to 100% similarity)

#### Per-Folder Thresholds
- **Format**: JSON object with folder paths as keys
- **Example**: `{"src/shared": 0.1, "src/tests": 0.9}`
- **Priority**: Folder-specific thresholds override global threshold
- **Matching**: Uses most specific (longest) matching folder path
- **Dual Path Logic**: Considers both the new function's path AND existing function's path
- **Threshold Selection**: Uses the **more strict (higher)** threshold between the two paths
- **Fallback**: If no folder threshold matches, uses global threshold

#### Threshold Examples
```yaml
# Strict detection globally
global-threshold: 0.85

# Lenient detection globally
global-threshold: 0.5

# Mixed approach (lenient for shared code, strict for tests)
folder-thresholds: '{"src/shared": 0.1, "tests": 0.9, "src/core": 0.8}'
```

#### How Dual Path Logic Works
When comparing functions from different folders, the system:
1. Gets threshold for new function's folder (or global if no match)
2. Gets threshold for existing function's folder (or global if no match)  
3. Uses the **higher (more strict)** threshold of the two

**Example**:
```yaml
global-threshold: 0.3
folder-thresholds: '{"src/shared": 0.3, "src/projects/integrations": 0.4}'
```

- `test.py` vs `src/shared/utils.py`: Uses `max(0.3, 0.3) = 0.3` threshold → 34.2% > 30% ✅ **Reported**
- `test.py` vs `src/projects/integrations/service.py`: Uses `max(0.3, 0.4) = 0.4` threshold → 30.9% < 40% ❌ **Not Reported**
- `main.py` vs `src/core/logic.py`: Uses `max(0.3, 0.3) = 0.3` threshold (both use global)

#### Real-World Use Cases
- **Shared Libraries**: Low threshold (0.1-0.3) to catch even minor duplications
- **Test Files**: High threshold (0.8-0.9) to avoid false positives on similar test patterns
- **Core Business Logic**: Medium-high threshold (0.6-0.8) for important code quality
- **Utilities**: Medium threshold (0.5-0.7) for general utility functions

## 📈 Example Output

```markdown
## 🔍 Duplicate Logic Detection Results

Found 2 potential duplicates with high confidence:

### Match 1: Email Validation
- **New Function**: `check_email_format` (src/utils.py:15)
- **Existing Function**: `validate_email` (src/validators.py:8)  
- **Similarity**: 92%
- **Suggestion**: Consider using the existing `validate_email` function instead

### Match 2: Data Processing
- **New Function**: `process_user_data` (src/handlers.py:25)
- **Existing Function**: `handle_user_info` (src/services.py:45)
- **Similarity**: 87%
- **Suggestion**: Extract common logic into a shared utility function
```

## 📦 Dependencies

### Runtime Dependencies
The action has minimal runtime dependencies for fast execution:
- **[rich](https://github.com/Textualize/rich) v14.1.0** - Console output and progress bars

### Development Dependencies
For development, testing, and research, additional dependencies are available:
- **Testing**: pytest, pytest-mock, pytest-cov, pytest-xdist
- **Code Quality**: black, isort, flake8, mypy, pre-commit
- **Research**: GitPython, PyGithub, scikit-learn, nltk, numpy, pandas, pyyaml

### Dependency Management
The action uses modern Python packaging with `pyproject.toml` and [uv](https://github.com/astral-sh/uv) for fast dependency management:

```toml
# Clean core dependencies
dependencies = []

# Runtime dependencies (action execution)
[project.optional-dependencies]
runtime = ["rich==14.1.0"]

# Dataset generation dependencies
dataset = ["openai>=1.0.0", "pandas>=2.0.0", "numpy>=1.24.0"]

# Research dependencies (experiments)
research = ["GitPython", "PyGithub", "scikit-learn", ...]

# Development dependencies
dev = ["black>=23.0.0", "isort>=5.12.0", ...]
test = ["pytest>=7.0.0", "pytest-mock>=3.10.0", ...]
```

## 🛠️ Development

```bash
# Clone the repository
git clone https://github.com/ArthurMor4is/duplicate-logic-detector-action.git

# Install dependencies using uv (recommended)
uv sync --all-extras

# Or using traditional pip
pip install -e ".[dev,test]"

# Run tests
make test
# or
uv run pytest

# Run sample analysis
make test-sample
```

**Note**: The `config/default-config.yml` file is used for development and testing purposes only. The GitHub Action uses built-in configuration optimized for CI/CD workflows.

## 🧪 Dataset Generation

This repository includes tools to generate datasets for testing and tuning duplicate detection algorithms:

```bash
# Install dataset generation dependencies
uv pip install -e ".[dataset]"

# Generate function clones using LLM
generate-clones --source-code "./src" --dest-folder="clones_output" --n-clones=3

# Build balanced datasets
build-dataset --clones-folder="clones_output" --dataset-name="test_dataset.json" --clone-ratio=0.5
```

**Use Cases:**
- 🔬 **Algorithm Testing**: Test different similarity methods on your codebase
- 🎯 **Threshold Tuning**: Find optimal detection thresholds
- 📊 **Performance Evaluation**: Compare detection strategies with ground truth data

See the [Dataset Generation Guide](scripts/dataset_generation/README.md) for detailed instructions.

## 📡 Feedback Collector

Servidor simples para coletar reações em tempo real dos comentários da action:

- **Coleta em Tempo Real**: Monitora reações via webhook do GitHub
- **API Simples**: Endpoints para visualizar dados e estatísticas
- **Fácil Deploy**: Servidor Node.js standalone ou serverless

### Quick Setup

```bash
# 1. Instalar dependências
npm install

# 2. Configurar variáveis
export WEBHOOK_SECRET="seu-secret-aqui"
export PORT=3000

# 3. Executar servidor
npm start
```

Configure o webhook no GitHub apontando para `/webhook` e monitore as reações em tempo real!

Veja o [Guia do Feedback Collector](FEEDBACK_COLLECTOR.md) para instruções completas.

## 📚 Documentation

- [Usage Guide](USAGE.md) - Detailed usage instructions
- [Testing Guide](TESTING.md) - How to test the action
- [Feedback Collector Guide](FEEDBACK_COLLECTOR.md) - Real-time reaction collection
- [Dataset Generation Guide](scripts/dataset_generation/README.md) - Generate test datasets
- [Examples](examples/) - Complete workflow examples

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- 📖 [Documentation](https://github.com/ArthurMor4is/duplicate-logic-detector-action/wiki)
- 🐛 [Report Issues](https://github.com/ArthurMor4is/duplicate-logic-detector-action/issues)
- 💬 [Discussions](https://github.com/ArthurMor4is/duplicate-logic-detector-action/discussions)
