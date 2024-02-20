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
import json
import logging
import shutil
import tempfile
import time
from pathlib import Path

import rich

from pulp_docs.cli import Config
from pulp_docs.constants import RESTAPI_URL_TEMPLATE
from pulp_docs.navigation import get_navigation
from pulp_docs.repository import Repo, Repos, SubPackage

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

    for repo_or_pkg in repos.all:
        start = time.perf_counter()
        # handle subpcakges nested under repositories
        this_docs_dir = repo_docs / repo_or_pkg.name
        if not isinstance(repo_or_pkg, SubPackage):
            this_src_dir = repo_sources / repo_or_pkg.name
            repo_or_pkg.download(dest_dir=this_src_dir, clear_cache=config.clear_cache)
        else:
            this_src_dir = repo_sources / repo_or_pkg.subpackage_of / repo_or_pkg.name

        # install and post-process
        _place_doc_files(this_src_dir, this_docs_dir, repo_or_pkg)
        if repo_or_pkg.type == "content":
            _generate_rest_api_page(this_docs_dir, repo_or_pkg.name, repo_or_pkg.title)

        end = time.perf_counter()
        log.info(f"{repo_or_pkg.name} completed in {end - start:.2} sec")

    # Copy core-files (shipped with pulp-docs) to tmpdir
    shutil.copy(
        repo_sources / repos.core_repo.name / SRC_DOCS_DIRNAME / "index.md",
        repo_docs / "index.md",
    )

    # Log
    log.info("[pulp-docs] Done downloading sources. Here are the sources used:")
    for repo_or_pkg in repos.all:
        log.info({repo_or_pkg.name: str(repo_or_pkg.status)})

    return (repo_docs, repo_sources)


def _place_doc_files(src_dir: Path, docs_dir: Path, repo: Repo):
    """Copy only doc-related files from src_dir to doc_dir"""
    log.info(f"Moving doc files:\nfrom '{src_dir}'\nto '{docs_dir}'")

    try:
        shutil.copytree(src_dir / SRC_DOCS_DIRNAME, docs_dir / "docs")
    except FileNotFoundError:
        Path(docs_dir / "docs").mkdir(parents=True)
        repo.status.has_staging_docs = False

    # Get CHANGELOG
    # TODO: remove reading .rst (plugins should provide markdown CHANGELOG)
    repo.status.has_changelog = False
    for changelog_name in ("CHANGELOG.md", "CHANGES.md", "CHANGES.rst"):
        changelog_path = Path(src_dir / changelog_name)
        if changelog_path.exists():
            reference_dir = Path(docs_dir / "docs/reference")
            reference_dir.mkdir(exist_ok=True)
            shutil.copy(changelog_path, reference_dir / "CHANGELOG.md")
            repo.status.has_changelog = True
            break


def _generate_rest_api_page(docs_dir: Path, repo_name: str, repo_title: str):
    """Create page that contain a link to the rest api, based on the project url template"""
    log.info("Generating REST_API page")
    rest_api_page = docs_dir / "docs" / "rest_api.md"
    rest_api_page.touch()
    restapi_url = RESTAPI_URL_TEMPLATE.format(repo_name)
    md_title = f"# {repo_title} REST Api"
    md_body = f"[{restapi_url}]({restapi_url})"
    rest_api_page.write_text(f"{md_title}\n\n{md_body}")


def print_user_repo(repos: Repos, config: Config):
    """Emit report  about local checkout being used or warn if none."""
    print("*" * 79)
    log.info("[pulp-docs] Summary info about the build. Use -v for more info")

    local_checkouts = []
    cached_repos = []
    downloaded_repos = []
    warn_msgs = []

    # prepare data for user report
    for repo in repos.all:
        record = {
            "name": repo.name,
            "download_source": repo.status.download_source,
            "refs": repo.branch_in_use,
        }
        if repo.status.use_local_checkout is True:
            local_checkouts.append(record)
        elif repo.status.using_cache is True:
            cached_repos.append(record)
        else:
            downloaded_repos.append(record)

        # TODO: improve this refspec comparision heuristics
        if repo.branch not in repo.branch_in_use:
            warn_msgs.append(
                f"[pulp-docs] Original {repo.name!r} ref is {repo.branch!r}, but local one is '{repo.branch_in_use}'."
            )

    if len(local_checkouts) == 0:
        warn_msgs.append(
            "[pulp-docs] No local checkouts found. Serving in read-only mode."
        )

    if config.verbose:
        report = {
            "config": config.get_environ_dict(),
            "cached_repos": cached_repos,
            "downloaded_repos": downloaded_repos,
            "local_checkouts": local_checkouts,
        }
    else:
        report = {
            "cached_repos": [repo["name"] for repo in cached_repos],
            "downloaded_repos": [repo["name"] for repo in downloaded_repos],
            "local_checkouts": [repo["name"] for repo in local_checkouts],
        }

    rich.print_json(json.dumps(report, indent=4))

    for msg in warn_msgs:
        log.warning(msg)
    print("*" * 79)


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
    env.config["pulp_repos"] = repos
    env.conf["pulp_config"] = config

    # Extra config
    @env.macro
    def get_repos(repo_type="content"):
        "Return repo names by type"
        return sorted(repos.get_repos(repo_types=[repo_type]), key=lambda x: x.title)


def on_pre_page_macros(env):
    """The mkdocs-macros hook just before an inidvidual page render."""
    repos: Repos = env.conf["pulp_repos"]  # type: ignore

    # Configure the edit_url with correct repository and path
    src_uri = env.page.file.src_uri.replace("/docs/", f"/{SRC_DOCS_DIRNAME}/")
    if src_uri != "index.md":
        repo, _, path = src_uri.partition("/")
    else:
        repo = "pulpcore"
        path = f"{SRC_DOCS_DIRNAME}/index.md"

    repo_obj = repos.get(repo)
    repo_branch = getattr(repo_obj, "branch", "main")
    edit_url = f"https://github.com/pulp/{repo}/edit/{repo_branch}/{path}"
    env.page.edit_url = edit_url


def on_post_build(env):
    """The mkdocs-marcros 'on_post_build' hook. Used to print summary report for end user."""
    # Log relevant most useful information for end-user
    print_user_repo(repos=env.conf["pulp_repos"], config=env.conf["pulp_config"])
