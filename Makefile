.PHONY: lock
lock:
	uv pip compile --all-extras pyproject.toml -o requirements-dev.txt
	uv pip compile --extra=test pyproject.toml -o requirements-test.txt
	uv pip compile pyproject.toml -o requirements.txt

.PHONY: install
install: lock
	uv pip install -r requirements-dev.txt

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
	pyright src/
