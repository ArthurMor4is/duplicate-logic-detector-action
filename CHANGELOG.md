# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Configurable Similarity Methods**: Added `similarity-method` input parameter with three options:
  - `jaccard_tokens` (default): Fast, token-based Jaccard similarity
  - `sequence_matcher`: Balanced approach using Python's difflib.SequenceMatcher
  - `levenshtein_norm`: High precision using normalized Levenshtein distance
- New examples demonstrating different similarity methods
- Enhanced documentation with method recommendations and use cases
- **Modular Architecture**: Refactored codebase into professional modular structure:
  - `duplicate_detector.models`: Data models (CodeFunction, DuplicateMatch)
  - `duplicate_detector.similarity`: Similarity analysis algorithms
  - `duplicate_detector.extractor`: Python function extraction
  - `duplicate_detector.reporters`: Multi-format report generation
  - `duplicate_detector.detector`: Main orchestration class
  - `duplicate_detector.main`: Main entry point (moved from root scripts/)
- Added similarity threshold parameter for filtering results
- Enhanced error handling and validation throughout

### Fixed
- **Dependency Installation**: Fixed action failing when target repository doesn't have `pyproject.toml` or `setup.py`
- Action now installs dependencies from its own directory instead of target repository
- Improved code organization and maintainability

## [1.0.2] - 2025-09-30

### Fixed
- **JSON Serialization Error**: Fixed "Object of type set is not JSON serializable" error by converting Set fields to List in CodeFunction dataclass
- **Deprecated GitHub Actions Commands**: Replaced deprecated `::set-output` commands with environment files to eliminate warnings
- Improved compatibility with GitHub Actions runtime environment

## [1.0.1] - 2025-09-30

### Fixed
- **Critical Bug Fix**: Removed dependency on target repository having `pyproject.toml` file
- Changed from `uv` to `pip` for dependency installation to ensure compatibility with all Python repositories
- Action now works in any Python repository regardless of dependency management setup

## [1.0.0] - 2025-09-30

### Added
- Initial public release
- GitHub Marketplace publication
- Complete documentation and examples
- CI/CD workflows for testing and releases
