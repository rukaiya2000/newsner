.PHONY: help format lint type-check test coverage clean

help:
	@echo "NewsNER — Development Commands"
	@echo ""
	@echo "  make format      Format code with black and ruff"
	@echo "  make lint        Check code with ruff"
	@echo "  make type-check  Type-check with mypy"
	@echo "  make test        Run pytest suite"
	@echo "  make coverage    Run tests with coverage report"
	@echo "  make check       Run all checks (lint, type-check, test)"
	@echo "  make clean       Remove cache and build files"

format:
	black src/ tests/ main.py demo.py
	ruff check src/ tests/ main.py demo.py --fix

lint:
	ruff check src/ tests/ main.py demo.py

type-check:
	mypy src/ main.py demo.py

test:
	pytest tests/ -v

coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

check: lint type-check test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type d -name htmlcov -exec rm -rf {} +
	find . -name ".coverage" -delete
	find . -name "*.pyc" -delete
