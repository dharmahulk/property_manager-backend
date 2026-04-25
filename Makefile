.PHONY: test test-unit test-integration test-coverage test-all install-test-deps lint security clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  make install-deps     - Install production dependencies"
	@echo "  make install-test     - Install test dependencies"
	@echo "  make install-dev      - Install development dependencies"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-coverage    - Run all tests with coverage report"
	@echo "  make test-all         - Run all tests"
	@echo "  make lint             - Run code linting"
	@echo "  make format           - Format code with black and isort"
	@echo "  make security         - Run security checks"
	@echo "  make clean            - Clean up generated files"
	@echo "  make server           - Start development server"
	@echo "  make help             - Show this help message"

# Installation targets
install-deps:
	pip install -r requirements.txt

install-test:
	pip install -r test_suite/requirements.txt

install-dev:
	pip install -r requirements-dev.txt

# Test targets
test-unit:
	python run_tests.py unit

test-integration:
	python run_tests.py integration

test-coverage:
	python run_tests.py coverage

test-all:
	python run_tests.py all

test: test-all

# Code quality targets
lint:
	python run_tests.py lint

format:
	black .
	isort .

security:
	python run_tests.py security

# Development targets
server:
	uvicorn app:app --reload --host 0.0.0.0 --port 8003

# Cleanup targets
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ 2>/dev/null || true
	rm -rf .coverage 2>/dev/null || true
	rm -rf .pytest_cache/ 2>/dev/null || true
	rm -rf dist/ 2>/dev/null || true
	rm -rf build/ 2>/dev/null || true

# Quick development setup
setup-dev: install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make server' to start the development server"
