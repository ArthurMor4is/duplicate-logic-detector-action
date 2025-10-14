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

## 🔍 Detection Strategies

The action uses token-based Jaccard similarity analysis to detect duplicate logic patterns:

### 1. AST Analysis
- Parses Python files to extract function definitions
- Analyzes function signatures and structure
- Identifies code patterns and complexity

### 2. Token-Based Similarity
- Converts functions to token representations
- Uses Jaccard similarity coefficient for comparison
- Focuses on logical structure over exact text matching

### 3. Smart Filtering
- Excludes very small functions (< 5 lines)
- Filters out test files and common patterns
- Prioritizes business logic and complex functions

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

## 📚 Documentation

- [Usage Guide](USAGE.md) - Detailed usage instructions
- [Testing Guide](TESTING.md) - How to test the action
- [Examples](examples/) - Complete workflow examples

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- 📖 [Documentation](https://github.com/ArthurMor4is/duplicate-logic-detector-action/wiki)
- 🐛 [Report Issues](https://github.com/ArthurMor4is/duplicate-logic-detector-action/issues)
- 💬 [Discussions](https://github.com/ArthurMor4is/duplicate-logic-detector-action/discussions)
