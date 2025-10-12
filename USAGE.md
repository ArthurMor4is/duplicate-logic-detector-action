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
      
      - uses: ArthurMor4is/duplicate-logic-detector-action@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### 2. Advanced Usage

```yaml
- name: Detect Duplicate Logic with Custom Settings
  uses: ArthurMor4is/duplicate-logic-detector-action@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    post-comment: true
    fail-on-duplicates: false
```

## Input Parameters

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `github-token` | GitHub token for API access | ✅ | `${{ github.token }}` |
| `pr-number` | Pull request number | ❌ | `${{ github.event.number }}` |
| `repository` | Repository name (owner/repo) | ❌ | `${{ github.repository }}` |
| `base-ref` | Base reference for comparison | ❌ | `${{ github.base_ref }}` |
| `head-ref` | Head reference for comparison | ❌ | `${{ github.head_ref }}` |
| `post-comment` | Post findings as PR comment | ❌ | `true` |
| `fail-on-duplicates` | Fail if high-confidence duplicates found | ❌ | `false` |

## Detection Process

The action automatically:

1. **Detects Changed Files**: Identifies Python files modified in the PR
2. **Extracts Functions**: Parses functions from changed files using AST analysis
3. **Compares Against Existing Code**: Uses token-based Jaccard similarity
4. **Reports Findings**: Creates detailed reports and optional PR comments
5. **Uploads Artifacts**: Stores analysis results for review

## Examples

See the `examples/` directory for complete workflow examples:

- `basic-usage.yml` - Simple setup
- `reusable-workflow.yml` - Using the reusable workflow
- `django-project.yml` - Django-specific configuration

## Outputs

The action provides these outputs:

- `duplicates-found`: boolean - Whether duplicates were detected
- `match-count`: number - Total number of matches found
- `report-path`: string - Path to detailed report

Use outputs in subsequent steps:

```yaml
- name: Check results
  if: steps.duplicates.outputs.duplicates-found == 'true'
  run: |
    echo "Found ${{ steps.duplicates.outputs.match-count }} duplicates"
```

## Troubleshooting

### Common Issues

1. **No duplicates detected**: The action uses conservative similarity thresholds by default
2. **Action fails**: Check that your repository has Python files and proper token permissions
3. **Missing PR comments**: Ensure `post-comment` is set to `true` and the token has write permissions

### Debug Mode

Enable debug logging:

```yaml
env:
  ACTIONS_STEP_DEBUG: true
```

### Report Artifacts

The action uploads analysis results as GitHub Actions artifacts:
- `duplicate-logic-report.json` - Detailed JSON report
- `duplicate-logic-report.md` - Human-readable Markdown report

Access these from the Actions run page under "Artifacts".
