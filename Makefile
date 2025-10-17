.PHONY: test test-cov test-quick test-verbose test-watch clean-test install-dev help

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-dev:  ## Install development dependencies
	@echo "Installing development dependencies..."
	@if command -v uv >/dev/null 2>&1; then \
		uv pip install -e ".[dev]"; \
	else \
		pip install -e ".[dev]"; \
	fi

test:  ## Run all tests
	pytest

test-cov:  ## Run tests with coverage report
	pytest --cov=fredo --cov-report=term-missing --cov-report=html
	@echo "\nCoverage report generated in htmlcov/index.html"

test-quick:  ## Run tests without coverage
	pytest --no-cov -x

test-verbose:  ## Run tests with verbose output
	pytest -vv

test-watch:  ## Run tests in watch mode (requires pytest-watch)
	pytest-watch

test-models:  ## Run only model tests
	pytest tests/test_models.py -v

test-database:  ## Run only database tests
	pytest tests/test_database.py -v

test-runner:  ## Run only runner tests
	pytest tests/test_runner.py -v

test-search:  ## Run only search tests
	pytest tests/test_search.py -v

test-config:  ## Run only config tests
	pytest tests/test_config.py -v

test-editor:  ## Run only editor tests
	pytest tests/test_editor.py -v

test-gist:  ## Run only gist tests
	pytest tests/test_gist.py -v

test-failed:  ## Run only failed tests from last run
	pytest --lf

clean-test:  ## Clean test artifacts
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf tests/__pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

clean: clean-test  ## Clean all generated files
	rm -rf build dist *.egg-info
	rm -rf .ruff_cache

lint:  ## Run linting
	ruff check .

format:  ## Format code
	ruff format .

check: lint test  ## Run linting and tests

.DEFAULT_GOAL := help

