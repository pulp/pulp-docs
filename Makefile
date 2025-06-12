BUILD_DIR= build
SITE_DIR = $(BUILD_DIR)/site
FETCH_DIR = $(BUILD_DIR)/fetched
PACKAGE_DIR = $(BUILD_DIR)/package

# From: https://github.com/IllustratedMan-code/make-help
help: ## Show this help
	@sed -ne "s/^##\(.*\)/\1/p" $(MAKEFILE_LIST)
	@printf "────────────────────────`tput bold``tput setaf 2` pulp-docs commands `tput sgr0`───────────────────────────\n"
	@sed -ne "/@sed/!s/\(^[^#?=]*:\).*##\(.*\)/`tput setaf 2``tput bold`\1`tput sgr0`\2/p" $(MAKEFILE_LIST)
	@printf "───────────────────────────────────────────────────────────────────────\n"

clean: ## Clean the package and docs build artifacts
	rm -rf $(BUILD_DIR)

ci: ## Run the component CI workflow. E.g: make ci component=pulp_rpm
ifndef component
	$(error component is a required argument. Usage: make ci component=<your-component-name>)
endif
	@echo "Running CI for component=$(component)"
	@mkdir -p $(BUILD_DIR)
	pulp-docs fetch --dest $(FETCH_DIR)
	pulp-docs build --site-dir $(BUILD_DIR)/site-$(component) --path $(component)@..:$(FETCH_DIR)
	@echo "Built site at: $(BUILD_DIR)/site-$(component)"

docs: ## Build the production ready documentation
	@mkdir -p $(BUILD_DIR)
	pulp-docs fetch --dest $(FETCH_DIR)
	pulp-docs build --site-dir $(SITE_DIR) --path $(FETCH_DIR)
	@echo "Built site at: $(SITE_DIR)"

build: ## Build the pulp-docs package
	@mkdir -p $(BUILD_DIR)
	python -m build -o $(PACKAGE_DIR)

.PHONY: clean ci build help docs
.DEFAULT_GOAL := help
