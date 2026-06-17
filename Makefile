.PHONY: install test serve lint

install:
	pip install -e ".[dev]"

test:
	pytest -q

serve:
	deadwood serve

lint:
	ruff check src tests
