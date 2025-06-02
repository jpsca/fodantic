.PHONY: install
install:
	uv sync --group dev --group test

.PHONY: test
test:
	uv run pytest -x src tests

.PHONY: lint
lint:
	uv run ruff check src tests

.PHONY: types
types:
	uv run pyright src tests

.PHONY: coverage
coverage:
	uv run pytest --cov-config=pyproject.toml --cov-report html --cov src tests

.PHONY: tox
tox:
	uv run tox
