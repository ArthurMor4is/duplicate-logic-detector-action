# Action Scripts

This directory contains modular scripts that power the GitHub Action. This refactoring improves maintainability and testability by separating concerns into focused, reusable scripts.

## 📁 Script Overview

### 🔧 `install-dependencies.sh`
**Purpose**: Install runtime dependencies for the action
- Installs `uv` package manager for fast dependency management
- Installs only runtime dependencies (`rich`) to minimize footprint
- Includes error handling and progress feedback

### 📂 `get-changed-files.sh`
**Purpose**: Identify changed Python files in PR or push events
- Handles both pull request and push event scenarios
- Extracts base/head commit SHAs for comparison
- Sets GitHub outputs for downstream steps
- Includes file count reporting and validation

### 🔍 `run-detection.sh`
**Purpose**: Execute duplicate logic detection and process results
- Runs the main duplicate detection algorithm
- Processes JSON results to extract metrics
- Sets GitHub outputs for duplicates found, match count, and report path
- Includes comprehensive error handling and progress reporting

### 💬 `post-comment.js`
**Purpose**: Post analysis results as PR comments
- Reads generated markdown reports
- Posts formatted comments to GitHub PRs
- Includes error handling to prevent action failures
- Uses modern GitHub API integration

## 🎯 Benefits of This Structure

### ✅ **Maintainability**
- **Separation of Concerns**: Each script has a single, focused responsibility
- **Easier Debugging**: Issues can be isolated to specific functionality
- **Independent Testing**: Scripts can be tested individually
- **Clear Documentation**: Each script is self-documenting with clear purpose

### ✅ **Reusability** 
- **Modular Design**: Scripts can be reused in different contexts
- **Consistent Interface**: All scripts follow similar patterns
- **Environment Variables**: Clean parameter passing via environment variables
- **Standard Error Handling**: Consistent error handling across all scripts

### ✅ **Performance**
- **Faster Development**: Smaller, focused files are easier to work with
- **Better Caching**: GitHub Actions can cache individual script results
- **Selective Execution**: Scripts only run when needed
- **Optimized Dependencies**: Each script loads only what it needs

## 🔧 Usage

### In GitHub Actions
```yaml
# Install dependencies
- name: Install dependencies
  shell: bash
  run: ${{ github.action_path }}/scripts/action/install-dependencies.sh

# Get changed files  
- name: Get changed files
  shell: bash
  env:
    BASE_REF: ${{ inputs.base-ref }}
    GITHUB_EVENT_NAME: ${{ github.event_name }}
  run: ${{ github.action_path }}/scripts/action/get-changed-files.sh
```

### Local Testing
```bash
# Test dependency installation
./scripts/action/install-dependencies.sh

# Test file detection (requires git repo)
export BASE_REF=main
export GITHUB_EVENT_NAME=pull_request
./scripts/action/get-changed-files.sh

# Test detection (requires changed files)
export CHANGED_FILES="src/test.py"
export BASE_SHA="abc123"
export HEAD_SHA="def456"
./scripts/action/run-detection.sh
```

## 🛠️ Development

### Adding New Scripts
1. Create script in this directory
2. Make it executable: `chmod +x script-name.sh`
3. Follow existing patterns for error handling and logging
4. Update this README with script documentation
5. Add corresponding step in `action.yml`

### Script Standards
- **Error Handling**: Use `set -euo pipefail` for bash scripts
- **Logging**: Include progress feedback with emojis
- **Environment**: Use environment variables for parameters
- **Outputs**: Set GitHub outputs using `$GITHUB_OUTPUT`
- **Documentation**: Include purpose and usage comments

## 📊 Before vs After

### Before (214 lines in action.yml)
```yaml
- name: Install dependencies
  run: |
    # 20+ lines of inline shell script
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    uv pip install --system -e ".[runtime]"
```

### After (clean action.yml)
```yaml
- name: Install dependencies
  run: ${{ github.action_path }}/scripts/action/install-dependencies.sh
```

**Result**: 214 lines → 130 lines (39% reduction) with better organization and maintainability!
