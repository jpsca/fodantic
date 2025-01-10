.PHONY: install
install:
	uv sync --group dev --group test

.PHONY: test
test:
	pytest -x src/ test_fodantic.py

.PHONY: lint
lint:
	ruff check src/ test_fodantic.py

.PHONY: coverage
coverage:
	pytest --cov-config=pyproject.toml --cov-report html --cov src/ test_fodantic.py

.PHONY: types
types:
	pyright src/ test_fodantic.py
