# Usage Guide

## Quick Start

### 1. Basic Setup

Add this workflow to `.github/workflows/duplicate-logic.yml`:

```yaml
name: Duplicate Logic Detection

on:
  pull_request:
    paths: ['**/*.py']

jobs:
  check-duplicates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - uses: your-org/duplicate-logic-detector-action@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### 2. Custom Configuration

Create `.duplicate-logic-config.yml` in your repository:

```yaml
thresholds:
  high_similarity: 0.80
  moderate_similarity: 0.60

include_patterns:
  - "src/**/*.py"
  - "lib/**/*.py"

exclude_patterns:
  - "tests/**"
  - "migrations/**"
  - "generated/**"

reporting:
  max_pr_comment_matches: 3
  pr_comment_min_confidence: "high"
```

## Configuration Options

### Similarity Thresholds

- `exact_match`: 0.90 (90%+ similarity)
- `high_similarity`: 0.70 (70%+ similarity) 
- `moderate_similarity`: 0.50 (50%+ similarity)

### File Patterns

Use glob patterns to include/exclude files:

```yaml
include_patterns:
  - "src/**/*.py"     # All Python files in src/
  - "app/**/*.py"     # All Python files in app/
  - "*.py"            # Python files in root

exclude_patterns:
  - "tests/**"        # Exclude all test files
  - "migrations/**"   # Exclude database migrations
  - "**/test_*.py"    # Exclude files starting with test_
  - "**/*_test.py"    # Exclude files ending with _test.py
```

## Examples

See the `examples/` directory for complete workflow examples:

- `basic-usage.yml` - Simple setup
- `reusable-workflow.yml` - Using the reusable workflow
- `django-project.yml` - Django-specific configuration

## Outputs

The action provides these outputs:

- `duplicates-found`: boolean - Whether duplicates were detected
- `match-count`: number - Total number of matches found
- `high-confidence-count`: number - High-confidence matches
- `report-path`: string - Path to detailed report

Use outputs in subsequent steps:

```yaml
- name: Check results
  if: steps.duplicates.outputs.duplicates-found == 'true'
  run: |
    echo "Found ${{ steps.duplicates.outputs.high-confidence-count }} duplicates"
```

## Troubleshooting

### Common Issues

1. **No duplicates detected**: Lower similarity threshold
2. **Too many false positives**: Increase threshold or add exclusions
3. **Action fails**: Check token permissions and file patterns

### Debug Mode

Enable debug logging:

```yaml
env:
  ACTIONS_STEP_DEBUG: true
```
