.PHONY: install test serve lint

install:
	pip install -e ".[dev]"

test:
	pytest -q

serve:
	deadwood serve

lint:
	python -m compileall -q src
