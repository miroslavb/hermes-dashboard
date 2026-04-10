.PHONY: dev test lint format install clean

install:
	pip install -e ".[dev]"

dev:
	uvicorn hermes_dashboard.app:create_app --reload --host 0.0.0.0 --port 8090

test:
	pytest tests/ -v --tb=short

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff check --fix src/ tests/
	ruff format src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf *.egg-info dist .pytest_cache
