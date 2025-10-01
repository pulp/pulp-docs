.PHONY: build
build:
	python -m build

.PHONY: test-dist
test-dist:
	python -m venv venv-dist
	venv-dist/bin/pip install dist/pulp_docs*.whl twine
	venv-dist/bin/pulp-docs --version
	# test mkdocs.yml is accessible via installed package
	venv-dist/bin/python -c "from pulp_docs.cli import get_default_mkdocs; assert get_default_mkdocs()"
	venv-dist/bin/twine check --strict dist/pulp_docs-*.whl
	@echo "Build is fine!"

.PHONY: lint
lint:
	pre-commit run -a

.PHONY: docs
docs:
	mkdocs build

.PHONY: clean
clean:
	rm -rf dist build venv-dist site
