build:
	pyproject-build -n

docs:
	pulp-docs build

.PHONY: build docs
