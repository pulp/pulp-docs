build:
	python -m build

lint:
	pre-commit run -a

docs:
	mkdocs build

.PHONY: docs build
