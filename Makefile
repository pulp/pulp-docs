.PHONY: help
help:
	@echo "COMMANDS:"
	@echo "    dist-build   Build the distribution package"
	@echo "    dist-test    Test the built distribution package"
	@echo "    docs-ci      Build docs for COMPONENT's CI"
	@echo "    lint         Run pre-commit hooks on all files"
	@echo "    clean        Remove build artifacts and temporary files"
	@echo "    help         Show this help message"

.PHONY: dist-build
dist-build:
	python -m build

.PHONY: dist-test
dist-test:
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

.PHONY: docs-ci
docs-ci: clean
ifndef COMPONENT
	@echo "Error: COMPONENT is required"
	@echo "Usage: make docs-ci COMPONENT=<component-name>"
	@exit 1
endif
	$(eval DOCS_PATH := "pulp-docs@..:$(COMPONENT)@..")
	$(eval DOCS_TMPDIR := "/tmp/pulp-docs-tmp")
	pulp-docs fetch --path-exclude "$(DOCS_PATH)" --dest "$(DOCS_TMPDIR)"
	pulp-docs build --path "$(DOCS_PATH):$(DOCS_TMPDIR)"
	@ls site || (echo "ERROR: something wen't wrong, 'site/' dir doesn't exist"; exit 1)


.PHONY: clean
clean:
	rm -rf dist build venv-dist site
