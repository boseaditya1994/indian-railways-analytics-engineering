.PHONY: install test lint format dbt-parse

install:
	python -m pip install -e ".[dev,warehouse,ml]"

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

dbt-parse:
	dbt parse --project-dir dbt_railway
