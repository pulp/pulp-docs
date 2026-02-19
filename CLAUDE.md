# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

`pulp-docs` is a documentation aggregation tool for the Pulp Project ecosystem. It is a custom MkDocs plugin that builds a unified documentation website by pulling content from ~30+ separate Pulp component repositories (pulpcore, pulp_ansible, pulp_container, etc.) into a single site at https://pulpproject.org/.

## Commands

**Linting:**
```bash
make lint          # Run pre-commit hooks (ruff, yamllint, typos)
```

**Testing:**
```bash
pytest -sv         # Run all tests
pytest -sv tests/test_openapi_generation.py  # Run a single test file
```

**Building the distribution:**
```bash
make dist-build    # Build wheel via python -m build
make dist-test     # Test wheel in a venv with twine
```

**Running the docs locally** (requires cloned component repos):
```bash
# 1. Clone required repos into a flat workspace (e.g., sibling of this repo)
pulp-docs fetch --dest "../"

# 2. Serve or build (--path points to the directory containing all cloned repos)
pulp-docs serve --path ".."
pulp-docs build --path ".." --blog --docstrings
```

**Building docs for a single component's CI:**
```bash
make docs-ci COMPONENT=pulpcore        # Build component-specific docs
```

## Code Architecture

### Entry Points
- `pulp-docs` CLI → `pulp_docs.cli:main` (Click-based, wraps MkDocs CLI)
- MkDocs plugin → `pulp_docs.plugin:PulpDocsPlugin` (registered as `PulpDocs` in pyproject.toml)

### Core Modules (`src/pulp_docs/`)

- **`plugin.py`** — The heart of the project. Contains the MkDocs plugin and all supporting classes:
  - `PulpDocsPlugin` — MkDocs lifecycle hooks (`on_config`, `on_files`, `on_page_context`, `on_page_markdown`, `on_pre_page`)
  - `ComponentLoader` — Discovers and loads component repos from configured lookup paths using `RepositoryFinder`
  - `ComponentNav` — Builds per-component navigation (Tutorials, How-to Guides, Learn More, Reference sections)
  - `DataExtractor` — Reads version from `pyproject.toml` and git metadata from component repos

- **`cli.py`** — Click CLI that sets context variables (`ctx_path`, `ctx_blog`, `ctx_docstrings`, `ctx_draft`, `ctx_dryrun`) before delegating to MkDocs

- **`context.py`** — `ContextVar` globals that pass CLI state into the MkDocs plugin without coupling them directly

- **`openapi.py`** — Generates OpenAPI JSON schemas by creating a venv per plugin and running `pulpcore-manager openapi`

### Configuration Flow

```
CLI flags (--path, --blog, --draft) → ContextVars → PulpDocsPlugin.on_config()
→ ComponentLoader (finds repos on disk) → ComponentNav (builds navigation)
→ MkDocs file/nav structure
```

### Component Discovery

Components are defined in `mkdocs.yml` under the `plugins.PulpDocs` section. At build time, `ComponentLoader` uses `RepositoryFinder` to locate each component on disk by searching the configured `--path` lookup directories (format: `name@/path/to/dir:name2@/path2`).

### Documentation Structure

Static content lives in `pulpproject.org/` (home page, blog posts, admin docs, dev docs). Per-component docs are loaded dynamically from each component's own repository. The `custom/` directory holds MkDocs theme overrides.

## Code Style

- Python 3.12+, line length 100, double quotes
- Ruff enforces `E`, `F`, `I` (isort), and `T100` (no breakpoints)
- Run `make lint` before committing; pre-commit hooks enforce ruff, yamllint, and typo checks
