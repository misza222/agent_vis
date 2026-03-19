.PHONY: help install run test lint format typecheck clean

help:
	@echo "Available commands:"
	@echo "  make install   - Install dependencies"
	@echo "  make run       - Run the development server"
	@echo "  make test      - Run tests"
	@echo "  make lint      - Run ruff linting"
	@echo "  make format    - Format code with ruff"
	@echo "  make typecheck - Run mypy type checking"
	@echo "  make clean     - Clean up cache files"

install:
	uv sync

run:
	uv run uvicorn src.agent_vis.app:app --reload

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy src/agent_vis

clean:
	rm -rf .pytest_cache __pycache__ src/**/__pycache__ tests/__pycache__
	rm -rf .ruff_cache
