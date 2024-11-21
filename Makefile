.PHONY: test clean lint format help coverage mypy

# Default target
help:
	@echo "Available commands:"
	@echo "  make test       - Run all tests"
	@echo "  make lint       - Run linter"
	@echo "  make format     - Format code"
	@echo "  make clean      - Clean up cache files"
	@echo "  make coverage   - Run tests with coverage"
	@echo "  make mypy       - Run type checker"

# Test targets
test:
	PYTHONPATH=${PWD} pytest -v tests/core tests/interface tests/integration tests/tools

# Coverage
coverage:
	PYTHONPATH=${PWD} pytest --cov=src --cov-report=html --cov-report=term tests/

# Type checking
mypy:
	mypy src/ tests/

# Linting
lint:
	ruff check .

# Formatting
format:
	black .
	isort .

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} + 