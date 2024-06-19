# Architecture

In general, pulp-docs is a wrapper around mkdocs and use its hooks to get things working together.
It also leverages some plugins from the `mkdocs` ecosystem.

## How it works

Through a `mkdocs-macro-plugin` hook (called in early stages of mkdocs processing), we inject the following steps:

1. Read [`repolist.yml`](https://github.com/pulp/pulp-docs/blob/main/src/pulp_docs/data/repolist.yml) packaged with `pulp-docs` to know which repos/urls to use
1. Download and Place all source code required to dir under `tempfile.gettempdir()`
    - Uses `../{repo}` if available OR
    - Uses existing cached `{tmpdir}/{repo}` if available OR
    - Downloads from github
1. Configure `mkdocs` through a hook: fix `mkdocstrings` config, generate navigation structure, etc
