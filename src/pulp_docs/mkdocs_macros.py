"""
The main mkdocs-macros-plugin file.

It defines a hook function (`define_env`) which is called at the beginning of mkdocs processing.
See: https://mkdocs-macros-plugin.readthedocs.io/en/latest/macros/

It's used here mainly to:

- Get source-code from all repositories by
    (a) downloading from github or
    (b) copying from local filesystem
- Edit mkdocs configuration (defined initially in mkdocs) programatically:
    1. Define navigation based on fetched files
    2. Configure mkdocstrings plugin to find the source code

"""
import logging
import os
import shutil
import tempfile
import typing as t
from pathlib import Path

from importlib_resources import as_file, files

from pulp_docs.main import Config
from pulp_docs.plugin_repos import Repos

# the name of the docs in the source repositories
SRC_DOCS_DIRNAME = "staging_docs"

# the dir to lookup for local repo checkouts
CHECKOUT_WORKDIR = Path().absolute().parent

log = logging.getLogger("mkdocs")


def create_clean_tmpdir(use_cache: bool = True):
    tmpdir_basepath = Path(tempfile.gettempdir()).absolute()
    tmpdir = tmpdir_basepath / "pulp-docs-tmp"
    # Clean tmpdir only if not using cache
    if tmpdir.exists() and use_cache is False:
        shutil.rmtree(tmpdir)
        tmpdir.mkdir()
    return tmpdir


def prepare_repositories(TMPDIR: Path, repos: Repos, config: Config):
    """
    Download repositories into tmpdir and organize them in a convenient way
    to mkdocs and its plugins.

    Notes:
        - repo_docs:
            The directory where each repository documentation files are going.
            These are *md files under each repo /docs folder.
        - repo_sources:
            The directory where each **repository source** is downloaded.
            Contains the whole source tree of that repository.
        - repo_docs/pulp-docs:
            The common assets used to configure the whole mkdocs site (lives in pulp-docs package).

    Returns: (Path(repo_docs), Path(repo_sources))

    Example:
        The final structure will be something like:

        ```
        tmpdir/
            repo_sources/
                core/{full-repo-source}
                repo1/{full-repo-source}
                ...
            repo_docs/
                pulp-docs/
                    assets/...
                    tags.md
                {for-each-repo}/
                    README.md
                    CHANGELOG.md
                    docs/

        ```
    """
    # Download/copy source code to tmpdir
    repo_sources = TMPDIR / "repo_sources"
    repo_docs = TMPDIR / "repo_docs"
    shutil.rmtree(repo_sources, ignore_errors=True)
    shutil.rmtree(repo_docs, ignore_errors=True)

    for repo in repos.all:
        # 1. Download repo (copy locally or fetch from GH)
        this_src_dir = repo_sources / repo.name
        repo.download(dest_dir=this_src_dir, clear_cache=config.clear_cache)

        # 2. Isolate docs dir from codebase (makes mkdocs happy)
        this_docs_dir = repo_docs / repo.name
        log.info(
            "Moving doc files:\nfrom '{}'\nto '{}'".format(this_src_dir, this_docs_dir)
        )
        shutil.copytree(this_src_dir / SRC_DOCS_DIRNAME, this_docs_dir / "docs")

        try:
            shutil.copy(this_src_dir / "CHANGELOG.md", this_docs_dir / "CHANGELOG.md")
        except FileNotFoundError:
            repo.status.has_changelog = False

        try:
            shutil.copy(this_src_dir / "README.md", this_docs_dir / "README.md")
        except FileNotFoundError:
            repo.status.has_readme = False

        # 3. Generate REST Api pages (workaround)
        if repo.type == "content":
            log.info("Generating REST_API page")
            rest_api_page = this_docs_dir / "docs" / "rest_api.md"
            rest_api_page.touch()
            md_title = f"# {repo.title} REST Api"
            md_body = f"[{repo.rest_api_link}]({repo.rest_api_link})"
            rest_api_page.write_text(f"{md_title}\n\n{md_body}")

    # Copy template-files (from this plugin) to tmpdir
    log.info("[pulp-docs] Moving pulp-docs /docs to final destination")
    data_file_docs = files("pulp_docs").joinpath("data/docs")
    with as_file(data_file_docs) as _docs:
        shutil.copytree(_docs, repo_docs / "pulp-docs")
    shutil.copy(
        repo_sources / repos.core.name / SRC_DOCS_DIRNAME / "index.md",
        repo_docs / "index.md",
    )

    # Log
    log.info("[pulp-docs] Done downloading sources. Here are the sources used:")
    for repo in repos.all:
        log.info({repo.name: repo.status})

    return (repo_docs, repo_sources)


def print_user_repo(repos: Repos, config: Config):
    """Emit report  about local checkout being used or warn if none."""
    local_checkouts = []
    cached_repos = []
    downloaded_repos = []

    # prepare data for user report
    for repo in repos.all:
        record = {
            "name": repo.name,
            "download_source": repo.status.download_source,
            "refs": repo.branch,
        }
        if repo.status.use_local_checkout is True:
            local_checkouts.append(record)
        elif repo.status.using_cache is True:
            cached_repos.append(record)
        else:
            downloaded_repos.append(record)

        # TODO: improve this refspec comparision heuristics
        if repo.status.original_refs and (repo.status.original_refs not in repo.branch):
            log.warning(
                f"[pulp-docs] Original repo ref is '{repo.status.original_refs}', but local one is '{repo.branch}'."
            )

    log.info(f"[pulp-docs] Config: {config.get_environ_dict()}")
    log.info(f"[pulp-docs] Cached repos: {cached_repos}")
    log.info(f"[pulp-docs] Downloaded repos: {downloaded_repos}")
    if len(local_checkouts) == 0:
        log.warning("[pulp-docs] No local checkouts found. Serving in read-only mode.")
    else:
        log.info(f"[pulp-docs] Local checkouts: {local_checkouts}")


def get_navigation(tmpdir: Path, repos: Repos):
    """The dynamic generated 'nav' section of mkdocs.yml"""

    # {repo}/docs/{persona}/{content-type}/*md
    # {repo}/docs/reference/*md
    def get_children(path: t.Union[str, Path]):
        _path = tmpdir / path if isinstance(path, str) else path
        result = [
            str(file.relative_to(tmpdir))
            for file in _path.glob("*.md")
            if not file.name.startswith("_")
        ]
        return result

    def expand_repos(template_str: str):
        _nav = {}
        for repo in repos.content:
            lookup_path = tmpdir / template_str.format(repo=repo.name)
            _repo_content = get_children(lookup_path)
            _nav[repo.title] = _repo_content
        return _nav

    def expand_reference(template_str: str):
        _nav = {}
        for repo in repos.all:
            lookup_path = tmpdir / template_str.format(repo=repo.name)
            _repo_content = get_children(lookup_path)
            reference_section = [
                {"REST API": f"{repo.name}/docs/rest_api.md"},
                {"Readme": f"{repo.name}/README.md"},
                {"Code API": _repo_content},
                {"Changelog": f"{repo.name}/CHANGELOG.md"},
            ]
            _nav[repo.title] = reference_section
        return _nav

    def from_core(url: str):
        corename = "pulpcore"
        return f"{corename}/{url}"

    getting_started = [
        {"Overview": from_core("docs/sections/getting_started/index.md")},
        {
            "Quickstart": get_children(
                from_core("docs/sections/getting_started/quickstart")
            )
        },
        {
            "Fundamentals": get_children(
                from_core("docs/sections/getting_started/fundamentals")
            )
        },
    ]
    guides = [
        {"Overview": from_core("docs/sections/guides/index.md")},
        {"For Content-Management": expand_repos("{repo}/docs/content-manager/guides")},
        {"For Sys-Admins": expand_repos("{repo}/docs/sys-admin/guides")},
    ]
    learn = [
        {"Overview": from_core("docs/sections/learn/index.md")},
        {"For Content-Management": expand_repos("{repo}/docs/content-manager/learn")},
        {"For Sys-Admins": expand_repos("{repo}/docs/sys-admin/learn")},
    ]
    reference = [
        {"Overview": from_core("docs/sections/reference/index.md")},
        {"Repository Map": from_core("docs/sections/reference/01-repository-map.md")},
        {"Glossary": from_core("docs/sections/reference/02-glossary.md")},
        {"Repositories": expand_reference("{repo}/docs/reference")},
    ]
    development = [
        {"Overview": from_core("docs/sections/development/index.md")},
        {
            "Quickstart": get_children(
                from_core("docs/sections/development/quickstart/")
            )
        },
        {
            "Onboarding": get_children(
                from_core("docs/sections/development/onboarding/")
            )
        },
        {"Guides": get_children("core/docs/sections/development/guides/")},
    ]

    # main navigation
    navigation = [
        {"Home": "index.md"},
        {"Getting Started": getting_started},
        {"Guides": guides},
        {"Learn": learn},
        {"Reference": reference},
        {"Development": development},
    ]
    return navigation


def define_env(env):
    """The mkdocs-marcros 'on_configuration' hook. Used to setup the project."""
    # Load configuration from environment
    log.info("[pulp-docs] Loading configuration from environ")
    config = Config(from_environ=True)

    if config.repolist:
        repos = Repos.from_yaml(config.repolist)
        repos.update_local_checkouts()
    else:
        repos = (
            Repos.test_fixtures()
        )  # try to use fixtures if there is no BASE_REPOLIST
    log.info(f"Repository configurations loaded: {[repo.name for repo in repos.all]}")

    # Download and organize repository files
    log.info("[pulp-docs] Preparing repositories")
    TMPDIR = create_clean_tmpdir()
    docs_dir, source_dir = prepare_repositories(TMPDIR, repos, config)

    # Configure mkdocstrings
    log.info("[pulp-docs] Configuring mkdocstrings")
    code_sources = [str(source_dir / repo.name) for repo in repos.all]
    env.conf["plugins"]["mkdocstrings"].config["handlers"]["python"][
        "paths"
    ] = code_sources

    # Configure navigation
    log.info("[pulp-docs] Configuring navigation")
    env.conf["docs_dir"] = docs_dir
    env.conf["nav"] = get_navigation(docs_dir, repos)

    log.info("[pulp-docs] Done with pulp-docs.")
    env.conf["pulp_repos"] = repos
    env.conf["pulp_config"] = config


def on_post_build(env):
    # Log relevant most useful information for end-user
    log.info("*" * 79)
    print_user_repo(repos=env.conf["pulp_repos"], config=env.conf["pulp_config"])
    log.info("*" * 79)
