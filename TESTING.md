# Testing Guide for Duplicate Logic Detector

This guide explains how to test the duplicate logic detection functionality both locally and as part of your development workflow.

## Quick Start

### 1. Install Dependencies

```bash
# Install main dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r test_requirements.txt

# Or use the test runner to install everything
python run_tests.py install
```

### 2. Run All Tests

```bash
# Run complete test suite
python run_tests.py all

# Or run specific test types
python run_tests.py unit      # Unit tests only
python run_tests.py sample    # Sample analysis
```

## Test Types

### Unit Tests

Located in `tests/test_duplicate_detector.py`, these tests verify individual components:

- **CodeFunction class**: Tests function data structure
- **DuplicateMatch class**: Tests match result structure  
- **DuplicateLogicDetector**: Tests core detection logic
- **Integration tests**: Tests complete detection workflow

```bash
# Run unit tests
python run_tests.py unit

# With verbose output
python run_tests.py unit --verbose

# With coverage report
python run_tests.py unit --coverage
```

### Sample Analysis

Test with pre-built sample files that contain known duplicates:

```bash
# Analyze sample files
python run_tests.py sample
```

Sample files:
- `test_samples/original_code.py` - Original functions
- `test_samples/duplicate_code.py` - Near-identical duplicates
- `test_samples/similar_but_different.py` - Similar but different logic

### Integration Tests

Test the detector on real repository scenarios:

```bash
# Test on current repository
python run_tests.py integration

# Test specific files
python run_tests.py integration --changed-files file1.py file2.py

# Test different repository
python run_tests.py integration --repository-path /path/to/repo
```

## Manual Testing

### Direct Script Usage

You can also run the detection script directly:

```bash
cd scripts
python duplicate_logic_detector.py \
    --repository-path ../test_samples \
    --changed-files duplicate_code.py \
    --output-format json
```

### Testing with Your Own Code

1. **Create test files** with intentional duplicates:

```python
# file1.py
def validate_email(email):
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# file2.py  
def check_email_format(email_addr):
    import re
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email_addr) is not None
```

2. **Run detection**:

```bash
python run_tests.py integration --changed-files file2.py
```

## Test Configuration

### Custom Configuration

Create a test-specific config file:

```yaml
# test-config.yml
thresholds:
  high_similarity: 0.70    # Lower threshold for testing
  moderate_similarity: 0.50

similarity_weights:
  semantic: 0.50           # Emphasize semantic similarity
  signature: 0.30
  ast_structure: 0.15
  function_calls: 0.05

min_function_lines: 3      # Test smaller functions
```

Use with:

```bash
python scripts/duplicate_logic_detector.py \
    --config-file test-config.yml \
    --changed-files test_file.py
```

## Expected Results

### High-Confidence Duplicates

Functions that should be detected as high-confidence duplicates:
- `validate_email()` vs `check_email_format()` - Same regex, similar logic
- `calculate_discount()` vs `compute_discount_amount()` - Identical calculation
- `process_user_data()` vs `validate_and_process_users()` - Same workflow

### Medium-Confidence Matches

Functions with similar patterns but different purposes:
- `validate_email()` vs `validate_phone_number()` - Similar validation pattern
- `calculate_discount()` vs `calculate_tax()` - Similar math operations

### Expected Output

```json
{
  "summary": {
    "total_matches": 8,
    "high_confidence": 5,
    "medium_confidence": 2,
    "low_confidence": 1
  },
  "matches": [
    {
      "original_function": {
        "name": "validate_email",
        "file": "test_samples/original_code.py",
        "line_start": 8
      },
      "duplicate_function": {
        "name": "check_email_format", 
        "file": "test_samples/duplicate_code.py",
        "line_start": 8
      },
      "similarity_score": 0.92,
      "confidence_level": "very_high",
      "suggestions": [
        "Extract common email validation logic into a shared utility function",
        "Consider using the existing validate_email function instead"
      ]
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'duplicate_logic_detector'**
   ```bash
   # Make sure the script exists
   ls scripts/duplicate_logic_detector.py
   
   # Install dependencies
   python run_tests.py install
   ```

2. **NLTK Data Missing**
   ```bash
   python -c "
   import nltk
   nltk.download('punkt')
   nltk.download('stopwords')
   "
   ```

3. **No Matches Found**
   - Lower similarity thresholds in config
   - Check file patterns (include/exclude)
   - Verify functions meet minimum complexity/length requirements

4. **Too Many False Positives**
   - Increase similarity thresholds
   - Add exclusion patterns for utility functions
   - Adjust similarity weights

### Debug Mode

Enable detailed logging:

```bash
export DEBUG=1
python run_tests.py sample
```

### Test Coverage

Generate detailed coverage reports:

```bash
python run_tests.py unit --coverage
# Open htmlcov/index.html in browser
```

## CI/CD Integration

### GitHub Actions Testing

Add to `.github/workflows/test-duplicate-detection.yml`:

```yaml
name: Test Duplicate Detection

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: python run_tests.py install
        
      - name: Run tests
        run: python run_tests.py all --verbose
```

### Local Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
python run_tests.py unit
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

## Performance Testing

### Large Codebase Testing

Test with larger codebases:

```bash
# Clone a Python project
git clone https://github.com/python/cpython.git test_large_repo
cd test_large_repo

# Test duplicate detection
python ../run_tests.py integration \
    --repository-path . \
    --changed-files Lib/email/utils.py
```

### Benchmark Testing

Time the detection process:

```bash
time python run_tests.py sample
```

Expected performance:
- Small files (< 100 functions): < 5 seconds
- Medium files (100-500 functions): < 30 seconds  
- Large files (500+ functions): < 2 minutes

## Contributing Tests

When adding new features, include tests:

1. **Add unit tests** in `tests/test_duplicate_detector.py`
2. **Add sample cases** in `test_samples/`
3. **Update documentation** in this file
4. **Run full test suite** before submitting

```bash
# Verify all tests pass
python run_tests.py all --coverage
```
