DOCS_IMAGE ?= pulp-docs

.PHONY: help
help:
	@echo "COMMANDS:"
	@echo "    dist-build      Build the distribution package"
	@echo "    dist-test       Test the built distribution package"
	@echo "    docs-image      Build the docs container image"
	@echo "    docs-ci         Build docs for COMPONENT's CI"
	@echo "    docs-prod       Build the full production docs site"
	@echo "    docs-linkcheck: Check for broken documentation links"
	@echo "    test            Run the test suite"
	@echo "    lint            Run pre-commit hooks on all files"
	@echo "    clean           Remove build artifacts and temporary files"
	@echo "    help            Show this help message"

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

.PHONY: test
test:
	uv run --with-requirements test_requirements.txt pytest

.PHONY: lint
lint:
	pre-commit run -a

.PHONY: docs-linkcheck
docs-linkcheck:
	@uv run pulp-linkchecker \
		$$(git ls-files | grep '^docs/**/.*md$$') \
		&& echo "No broken links found"

.PHONY: docs-image
docs-image:
	docker build -t $(DOCS_IMAGE) .

.PHONY: docs-prod
docs-prod: clean docs-image
	docker run --rm \
		--user $(shell id -u):$(shell id -g) \
		-v $(CURDIR):/pulp-docs \
		$(DOCS_IMAGE) \
		/pulp-docs/ci/scripts/build_docs_prod.sh

# avoid double mount if COMPONENT is pulp-docs
ifeq ($(COMPONENT),pulp-docs)
_COMPONENT_MOUNT =
else
_COMPONENT_MOUNT = -v $(CURDIR)/../$(COMPONENT):/$(COMPONENT)
endif

.PHONY: docs-ci
docs-ci: clean docs-image
ifndef COMPONENT
	@echo "Error: COMPONENT is required"
	@echo "Usage: make docs-ci COMPONENT=<component-name>"
	@exit 1
endif
	docker run --rm \
		--user $(shell id -u):$(shell id -g) \
		-v $(CURDIR):/pulp-docs \
		$(_COMPONENT_MOUNT) \
		$(DOCS_IMAGE) \
		/pulp-docs/ci/scripts/build_docs_ci.sh $(COMPONENT)


.PHONY: clean
clean:
	rm -rf dist build venv-dist site
