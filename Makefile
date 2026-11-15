all: install run

install:
	uv sync

run:
	uv run --env-file .env call-me-maybe

help:
	uv run call-me-maybe -h

debug:
	uv run python -m pdb .venv/bin/call-me-maybe

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +

lint:
	flake8
	uv run mypy . --warn-return-any \
			--warn-unused-ignores \
			--ignore-missing-imports \
			--disallow-untyped-defs \
			--check-untyped-defs \
			--exclude llm_sdk

.PHONY: install run help debug clean lint
