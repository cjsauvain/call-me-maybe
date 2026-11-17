ifneq ($(wildcard .env),)
	ENV_FILE_OPT := --env-file .env
else
	ENV_FILE_OPT :=
endif

all: install run

install:
	uv sync

run:
	uv run $(ENV_FILE_OPT) python -m src

run-visualize:
	uv run $(ENV_FILE_OPT) python -m src --generation-visualization

test:
	uv run $(ENV_FILE_OPT) pytest --cov=src --cov-report=term-missing tests

help:
	uv run python -m src -h

debug:
	uv run $(ENV_FILE_OPT) python -m pdb -m src

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf .mypy_cache .coverage

lint:
	uv run flake8
	uv run mypy . --warn-return-any \
			--warn-unused-ignores \
			--ignore-missing-imports \
			--disallow-untyped-defs \
			--check-untyped-defs \
			--exclude llm_sdk

.PHONY: all install run run-visualize test help debug clean lint
