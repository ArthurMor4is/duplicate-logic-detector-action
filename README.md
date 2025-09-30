# Duplicate Logic Detector Action

A GitHub Action that detects duplicate logic in Python code using AST analysis and semantic similarity.

## Usage

```yaml
- name: Detect Duplicate Logic
  uses: your-org/duplicate-logic-detector-action@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Features

- Multi-strategy detection (AST, semantic, signatures)
- Configurable thresholds  
- PR comments with suggestions
- Comprehensive reporting

## License

MIT
