SHELL := /bin/zsh

ifneq ($(wildcard .env),)
	ENV_FILE_OPT := --env-file .env
else
	ENV_FILE_OPT :=
endif

all: install run

install:
	uv sync

run:
	$(TIME) uv run $(ENV_FILE_OPT) python -m src

run-nested:
	$(TIME) uv run $(ENV_FILE_OPT) python -m src										\
		--function-definitions ./data/input/nested_function_definitions.json	\
		--input ./data/input/nested_function_calling_tests.json					\
		--output ./data/output/nested_function_calls.json

run-visualize:
	$(TIME) uv run $(ENV_FILE_OPT) python -m src --generation-visualization

run-nested-visualize:
	$(TIME) uv run $(ENV_FILE_OPT) python -m src										\
		--generation-visualization												\
		--function-definitions ./data/input/nested_function_definitions.json	\
		--input ./data/input/nested_function_calling_tests.json					\
		--output ./data/output/nested_function_calls.json

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
			--exclude src/lib

.PHONY: all install run run-visualize test help debug clean lint
