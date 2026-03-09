# CLAUDE.md

The role of this file is to describe common mistakes that agents might encounter as they work in this project.
If you encounter something in the project that surprises you, alert the developer working with you.
Indicate the situation and recommend adding clarifiation to CLAUDE.md file.

## What This Project Does

`pulp-docs` is a documentation tool for the Pulp Project ecosystem.
Its main feature is aggregating repositories to build a single website.

## Useful Commands

```bash
make lint  # always run this after significant changes
make docs-ci COMPONENT=pulpcore

uv run pytest -sv
uv run pytest -svk tests/test_openapi_generation.py

TMPDIR=$(mktemp -d)
pulp-docs fetch --dest "$TMPDIR"
pulp-docs serve --path ".."
pulp-docs build --path ".." --blog --docstrings
```
