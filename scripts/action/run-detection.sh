#!/bin/bash
set -euo pipefail

# Run duplicate logic detection and process results
# Sets GitHub outputs: duplicates_found, match_count, report_path

echo "🔍 Running duplicate logic detection..."

# Check if there are changed files
if [ -z "$CHANGED_FILES" ]; then
    echo "⚠️ No Python files changed, skipping detection"
    echo "duplicates_found=false" >> "$GITHUB_OUTPUT"
    echo "match_count=0" >> "$GITHUB_OUTPUT"
    exit 0
fi

# Run the duplicate detection
echo "Analyzing code for duplicates..."
python -m duplicate_detector.main \
    --pr-number "$PR_NUMBER" \
    --repository "$REPOSITORY" \
    --base-sha "$BASE_SHA" \
    --head-sha "$HEAD_SHA" \
    --changed-files "$CHANGED_FILES" \
    --output-format github-actions \
    --repository-path "."

echo "✅ Detection completed"

# Process results and set outputs
if [ -f "duplicate-logic-report.json" ]; then
    echo "📊 Processing results..."
    
    # Extract match count from JSON report
    match_count=$(python -c "
import json
import sys
try:
    with open('duplicate-logic-report.json', 'r') as f:
        data = json.load(f)
    print(data.get('summary', {}).get('total_matches', 0))
except Exception as e:
    print(f'Error reading report: {e}', file=sys.stderr)
    print('0')
    ")
    
    echo "match_count=$match_count" >> "$GITHUB_OUTPUT"
    echo "report_path=duplicate-logic-report.json" >> "$GITHUB_OUTPUT"
    
    if [ "$match_count" -gt 0 ]; then
        echo "duplicates_found=true" >> "$GITHUB_OUTPUT"
        echo "⚠️ Found $match_count duplicate matches"
    else
        echo "duplicates_found=false" >> "$GITHUB_OUTPUT"
        echo "✅ No duplicates found"
    fi
else
    echo "⚠️ No report file generated"
    echo "duplicates_found=false" >> "$GITHUB_OUTPUT"
    echo "match_count=0" >> "$GITHUB_OUTPUT"
fi
