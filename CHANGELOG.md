# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
