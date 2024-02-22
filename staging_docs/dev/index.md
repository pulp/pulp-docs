# Overview

## What it is

`pulp-docs` is a tool for serving and building an unified doc out of Pulp's Plugin Ecosystem.

The idea is that each repository should install `pulp-docs` and imediatelly be able run the unified website server.
Also, this should be used for the production build.

It was developed as part of [The new Pulp "Unified Docs"](https://hackmd.io/eE3kG8qhT9eohRYbtooNww?view) project.

## How it works

Through a `mkdocs-macro-plugin` hook (called in early stages of mkdocs processing), we inject the following steps:

1. Read [`repolist.yml`](https://github.com/pedro-psb/pulp-docs/blob/main/src/pulp_docs/data/repolist.yml) packaged with `pulp-docs` to know which repos/urls to use
1. Download and Place all source code required to dir under `tempfile.gettempdir()`
    - Uses `../{repo}` if available OR
    - Uses existing cached `{tmpdir}/{repo}` if available OR
    - Downloads from github
1. Configure `mkdocs` through a hook: fix `mkdocstrings` config, generate navigation structure, etc

## Quickstart

Recommended way for daily usage:

=== "pipx"

    ```bash
    pipx install git+https://github.com/pedro-psb/pulp-docs --include-deps
    pulp-docs serve
    ```

=== "pip"

    ```bash
    pip --user install git+https://github.com/pedro-psb/pulp-docs
    pulp-docs serve
    ```
