.PHONY: help install test test-unit test-sample test-coverage lint format clean all

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with uv
	uv sync --all-extras
	uv run python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)" || true

test: test-unit ## Run all tests

test-unit: ## Run unit tests
	uv run pytest tests/ -v

test-coverage: ## Run tests with coverage report
	uv run pytest tests/ --cov=scripts --cov-report=html --cov-report=term

test-sample: ## Run sample duplicate detection analysis
	@echo "Running sample analysis..."
	@uv run python -c "import sys, os; sys.path.insert(0, 'scripts'); from duplicate_logic_detector import DuplicateLogicDetector; detector = DuplicateLogicDetector('.'); matches = detector.analyze_pr_changes(['test_samples/duplicate_code.py'], 'base', 'head'); print(f'Found {len(matches)} potential duplicates'); [print(f'  - {match.new_function.name} vs {match.existing_function.name} (similarity: {match.similarity_score:.2%})') for match in matches]"

lint: ## Run linting with flake8
	uv run flake8 scripts/ tests/ --max-line-length=88

format: ## Format code with black and isort
	uv run black scripts/ tests/
	uv run isort scripts/ tests/

type-check: ## Run type checking with mypy
	uv run mypy scripts/

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf htmlcov/ .coverage .pytest_cache/ .mypy_cache/
	rm -f duplicate-logic-report.json duplicate-logic-report.md

all: install lint type-check test ## Install, lint, type-check, and test

dev-setup: install ## Set up development environment
	@echo "Development environment ready!"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make test-sample' to test duplicate detection"

quick-test: ## Quick test without verbose output
	uv run pytest tests/ -q