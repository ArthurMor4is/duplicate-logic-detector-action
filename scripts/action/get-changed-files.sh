#!/bin/bash
set -euo pipefail

# Get changed Python files in the PR or push event
# Sets GitHub outputs: changed_files, base_sha, head_sha

echo "🔍 Getting changed Python files..."

# Get list of changed Python files
if [ "$GITHUB_EVENT_NAME" = "pull_request" ]; then
    echo "Analyzing pull request changes..."
    git fetch origin "$BASE_REF"
    changed_files=$(git diff --name-only "origin/$BASE_REF...HEAD" -- '*.py' | head -50)
    
    # Get commit SHAs for PR
    base_sha=$(git rev-parse "origin/$BASE_REF")
    head_sha=$(git rev-parse HEAD)
else
    echo "Analyzing push event changes..."
    # For push events, compare with previous commit
    changed_files=$(git diff --name-only HEAD~1 HEAD -- '*.py' | head -50)
    
    # Get commit SHAs for push
    base_sha=$(git rev-parse HEAD~1)
    head_sha=$(git rev-parse HEAD)
fi

# Set GitHub outputs
echo "changed_files<<EOF" >> "$GITHUB_OUTPUT"
echo "$changed_files" >> "$GITHUB_OUTPUT"
echo "EOF" >> "$GITHUB_OUTPUT"

echo "base_sha=$base_sha" >> "$GITHUB_OUTPUT"
echo "head_sha=$head_sha" >> "$GITHUB_OUTPUT"

# Log results
echo "Changed files:"
echo "$changed_files"
echo "Base SHA: $base_sha"
echo "Head SHA: $head_sha"

if [ -z "$changed_files" ]; then
    echo "⚠️ No Python files changed"
else
    file_count=$(echo "$changed_files" | wc -l)
    echo "✅ Found $file_count changed Python file(s)"
fi
