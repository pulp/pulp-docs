# pulp-docs: Unified multirepo documentation

<!--toc:start-->
- [Overview](#overview)
- [How it works](#how-it-works)
- [Runninng Locally](#runninng-locally)
<!--toc:end-->

Python Package to help aggregating Pulp's multirepo ecosystem into a unified doc.

## Overview

This packages is:

- A `mkdocs-macros-plugin` [pluget](https://mkdocs-macros-plugin.readthedocs.io/en/latest/pluglets/).
- A repository for common doc website asset.
- A centralized entrypoint for installing doc-related packages/tooling. (via its own requirements)
- A CLI for doc-related tasks, like serving and building.

The idea is that each repository should install `pulp-docs` and imediatelly be able run the unified website server.
Also, this should be used for the production build.

## How it works

Through a `mkdocs-macro-plugin` hook (called in early stages of mkdocs processing), we inject the following steps:

1. Read [`repolist.yml`](https://github.com/pulp/pulp-docs/blob/main/src/pulp_docs/data/repolist.yml) packaged with `pulp-docs` to know which repos/urls to use
1. Download/Move all source code required to dir under `tempfile.gettempdir()`
    - Uses `../{repo}` if available OR
    - Uses existing cached `{tmpdir}/{repo}` if available OR
    - Downloads from github
1. Configure `mkdocstrings` to find each repo codebase
1. Configure `mkdocs` navigation by leveraging our `/docs` content organization structure

And thats it, the magic is done.

## Setup

Recommended way for daily usage:

```bash
pipx install git+https://github.com/pulp/pulp-docs --include-deps
pulp-docs serve
```

For development, use your prefered method!

## How to override `repolist.yml`

If you want to share work you are doing in muliple forks, you can share a custom `repolist.yml` which points to your forks.

Then, anyone can test them locally by overriting your `repolist.yml` like so:

```bash
$ cat "path/to/my/repolist.yml"
repos:
  core:
    - name: pulpcore
      owner: some-github-username
      title: Pulp Core
      branch: main
(...)
$ export PULPDOCS_MKDOCS_FILE="path/to/my/repolist.yml"
$ pulp-docs serve
```

