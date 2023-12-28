# pulp-docs: Unified multirepo documenation

<!--toc:start-->
- [pulp-docs: Unified multirepo documenation](#pulp-docs-unified-multirepo-documenation)
  - [Overview](#overview)
  - [How it works](#how-it-works)
  - [Runninng Locally](#runninng-locally)
<!--toc:end-->

Python Package to help aggregating Pulp's multirepo ecosystem into a unified doc.

## Overview

This packages is:

- A `mkdocs-macros-plugin` [pluget](https://mkdocs-macros-plugin.readthedocs.io/en/latest/pluglets/). [relevant-code]()
- A repository for common doc website asset. [relevant-code](https://github.com/pedro-psb/pulp-docs/tree/main/src/pulp_docs/docs)
- A centralized entrypoint for installing doc-related packages/tooling. (via its own requirements)
- A CLI for doc-related tasks, like serving and building. [relevant-code](https://github.com/pedro-psb/pulp-docs/blob/main/src/pulp_docs/main.py)

The idea is that each repository should install `pulp-docs` and imediatelly be able run the unified website server.
Also, this should be used for the production build.

## How it works

Through a `mkdocs-macro-plugin` hook (called in early stages of mkdocs processing), we inject the following steps:

1. Download all source code needed for the build (either copying from local filesystem or downloading from GH)
1. Configure `mkdocstrings` to find each repo codebase
1. Configure `mkdocs` navigation by leveraging our `/docs` content organization structure

And thats it, the magic is done.

## Runninng Locally

Fixtures are fake respositories with code and docs. They are located in `tests/fixtures/`.

Hopefully, this should run the fixture setup:

```bash
$ pip install -r requirements.txt
$ pulp-docs serve
```

For other command, see:

```bash
$ pulp-docs --help
```

