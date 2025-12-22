.PHONY: help install install-dev run test lint format clean

help:
	@echo "Available commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make run           - Run the FastAPI server"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linter (ruff)"
	@echo "  make format        - Format code (black)"
	@echo "  make clean         - Clean cache and build files"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -v

test-cov:
	pytest --cov=app --cov-report=html --cov-report=term

lint:
	ruff check app tests

format:
	ruff format app tests
	ruff check --fix app tests

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

