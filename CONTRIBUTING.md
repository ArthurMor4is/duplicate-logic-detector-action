# Contributing to Duplicate Logic Detector Action

Thank you for your interest in contributing! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/duplicate-logic-detector-action.git
   cd duplicate-logic-detector-action
   ```
3. **Install dependencies**:
   ```bash
   make install
   # or
   uv sync --all-extras
   ```
4. **Run tests**:
   ```bash
   make test
   # or
   uv run pytest tests/ -v
   ```

## 🛠️ Development Workflow

### Setting up your development environment

```bash
# Install dependencies
make install

# Set up pre-commit hooks (optional but recommended)
uv run pre-commit install

# Run tests to ensure everything works
make test
```

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
3. **Add tests** for new functionality
4. **Run the test suite**:
   ```bash
   make test           # Run all tests
   make test-coverage  # Run with coverage report
   make lint          # Check code style
   make format        # Format code
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **Push and create a pull request**:
   ```bash
   git push origin feature/your-feature-name
   ```

## 📝 Coding Standards

### Code Style
- Use **Black** for code formatting
- Use **isort** for import sorting
- Use **flake8** for linting
- Follow **PEP 8** conventions

```bash
# Format code
make format

# Check linting
make lint
```

### Testing
- Write tests for new functionality
- Maintain test coverage above 80%
- Use descriptive test names
- Include both unit and integration tests

### Commit Messages
Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `test:` - Test changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

Examples:
```
feat: add semantic similarity threshold configuration
fix: handle empty function bodies in AST analysis
docs: update README with new configuration options
test: add integration tests for PR comment generation
```

## 🧪 Testing

### Running Tests

```bash
# All tests
make test

# Unit tests only
uv run pytest tests/ -v

# With coverage
make test-coverage

# Sample analysis test
make test-sample
```

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names: `test_should_detect_duplicate_when_similarity_high`
- Test both positive and negative cases
- Mock external dependencies (GitHub API, file system)

### Test Structure
```python
def test_should_detect_duplicate_when_functions_similar():
    # Arrange
    func1 = create_test_function("validate_email", ...)
    func2 = create_test_function("check_email", ...)
    
    # Act
    similarity = detector.calculate_similarity(func1, func2)
    
    # Assert
    assert similarity > 0.8
```

## 📚 Documentation

### Updating Documentation
- Update README.md for user-facing changes
- Update USAGE.md for configuration changes
- Update TESTING.md for testing changes
- Add docstrings to new functions
- Update type hints

### Documentation Style
- Use clear, concise language
- Include code examples
- Add emojis for better readability
- Keep documentation up to date with code changes

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Clear description** of the issue
2. **Steps to reproduce** the bug
3. **Expected behavior** vs **actual behavior**
4. **Environment details** (OS, Python version, etc.)
5. **Code samples** or **configuration files** if relevant

Use the bug report template in GitHub Issues.

## 💡 Feature Requests

When requesting features:

1. **Describe the problem** you're trying to solve
2. **Explain your proposed solution**
3. **Consider alternative solutions**
4. **Provide use cases** and examples

## 🔍 Code Review Process

### For Contributors
- Ensure all tests pass
- Update documentation as needed
- Respond to review feedback promptly
- Keep PRs focused and reasonably sized

### Review Criteria
- Code quality and style
- Test coverage
- Documentation updates
- Backward compatibility
- Performance implications

## 📦 Release Process

### Versioning
We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Steps
1. Update CHANGELOG.md
2. Update version in pyproject.toml
3. Create and push a git tag: `git tag v1.2.3`
4. GitHub Actions will automatically create the release

## 🤝 Community

### Getting Help
- 📖 [Documentation](https://github.com/ArthurMor4is/duplicate-logic-detector-action/wiki)
- 🐛 [Issues](https://github.com/ArthurMor4is/duplicate-logic-detector-action/issues)
- 💬 [Discussions](https://github.com/ArthurMor4is/duplicate-logic-detector-action/discussions)

### Code of Conduct
Please be respectful and inclusive. We welcome contributions from everyone regardless of experience level.

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to make code quality better for everyone! 🎉
