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

import httpx
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


def has_restapi(repo_or_pkg):
    return repo_or_pkg.type == "content" or repo_or_pkg.name == "pulpcore"


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
    api_src_dir = TMPDIR / "api_json"
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

        # restapi
        if has_restapi(repo_or_pkg):
            _download_api_json(api_src_dir, repo_or_pkg.name)
            _generate_rest_api_page(this_src_dir, repo_or_pkg.name, repo_or_pkg.title)

        # install and post-process
        _place_doc_files(this_src_dir, this_docs_dir, repo_or_pkg, api_src_dir)

        end = time.perf_counter()
        log.info(f"{repo_or_pkg.name} completed in {end - start:.2} sec")

    # Copy core-files (shipped with pulp-docs) to tmpdir
    shutil.copy(
        repo_sources / "pulp-docs" / SRC_DOCS_DIRNAME / "index.md",
        repo_docs / "index.md",
    )

    # Log
    log.info("[pulp-docs] Done downloading sources. Here are the sources used:")
    for repo_or_pkg in repos.all:
        log.info({repo_or_pkg.name: str(repo_or_pkg.status)})

    return (repo_docs, repo_sources)


def _download_api_json(api_dir: Path, repo_name: str):
    api_json_path = api_dir / f"{repo_name}/api.json"
    if api_json_path.exists():
        log.info(f"{repo_name} api.json already downloaded.")
        return

    log.info(f"Downloading api.json for {repo_name}")
    api_url_1 = "https://docs.pulpproject.org/{repo_name}/api.json"
    api_url_2 = "https://docs.pulpproject.org/{repo_name}/_static/api.json"
    response = httpx.get(api_url_1.format(repo_name=repo_name))
    if response.is_error:
        response = httpx.get(api_url_2.format(repo_name=repo_name))
    if response.is_error:
        raise Exception("Couldnt get rest api page")

    # Schema overrides for better display
    json_file_content = response.json()
    json_file_content["info"]["title"] = f"{repo_name} API"

    api_json_path.parent.mkdir(parents=True, exist_ok=True)
    api_json_path.write_text(json.dumps(json_file_content))
    log.info("Done.")


def _place_doc_files(src_dir: Path, docs_dir: Path, repo: Repo, api_src_dir: Path):
    """
    Copy only doc-related files from src_dir to doc_dir.

    Examples:
        ```
        # src_dir
        $WORKSPACE/pulpcore/
        $WORKSPACE/pulpcore/pulp_glue

        # docs_dir
        $TMPDIR/repo_docs/pulpcore/docs
        $TMPDIR/repo_docs/pulp_glue/docs
        ```

    """
    log.info(f"Moving doc files:\nfrom '{src_dir}'\nto '{docs_dir}'")

    try:
        shutil.copytree(src_dir / SRC_DOCS_DIRNAME, docs_dir / "docs")
    except FileNotFoundError:
        Path(docs_dir / "docs").mkdir(parents=True)
        repo.status.has_staging_docs = False

    # Setup rest Api
    if has_restapi(repo):
        api_json = api_src_dir / f"{repo.name}/api.json"
        api_md_page = src_dir / "restapi.md"
        shutil.copy(api_json, docs_dir / "api.json")
        shutil.copy(api_md_page, docs_dir / "restapi.md")

    # Get changelog
    repo.status.has_changelog = False
    changes_dir = Path(docs_dir)
    changes_dir.mkdir(exist_ok=True)
    for changelog_name in ("CHANGELOG.md", "CHANGES.md", "CHANGES.rst"):
        changelog_path = Path(src_dir / changelog_name)
        if changelog_path.exists():
            shutil.copy(changelog_path, changes_dir / "changes.md")
            repo.status.has_changelog = True
            return

    # Create redirect message for nested packages
    if isinstance(repo, SubPackage):
        empty_changelog = changes_dir / "changes.md"
        changes_url = f"site:{repo.subpackage_of}/changes/"
        empty_changelog.write_text(
            f"# Changelog\n\nThe changelog for this package is nested under [{repo.subpackage_of}]({changes_url})."
        )
        return

    # Create placeholder, case it was not possible to fetch one
    empty_changelog = changes_dir / "changes.md"
    empty_changelog.write_text(
        "# Changelog\n\nThe repository does not provide a changelog or there was a problem fetching it."
    )


RESTAPI_TEMPLATE = """\
---
restapi_json_file: "../api.json"
---
"""


def _generate_rest_api_page(docs_dir: Path, repo_name: str, repo_title: str):
    """Create page that contain a link to the rest api, based on the project url template"""
    log.info("Generating REST_API page")
    rest_api_page = docs_dir / "restapi.md"
    rest_api_page.parent.mkdir(parents=True, exist_ok=True)
    # rest_api_page.write_text(RESTAPI_TEMPLATE.format(repo_title=repo_title))
    rest_api_page.write_text(RESTAPI_TEMPLATE)


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
    code_sources = []
    for repo_or_package in repos.all:
        # Handle subpackages or repos
        if isinstance(repo_or_package, SubPackage):
            repo_or_package_path = (
                repo_or_package.subpackage_of + "/" + repo_or_package.name
            )
        else:
            repo_or_package_path = repo_or_package.name
        # Add to mkdocstring pythonpath
        code_sources.append(str(source_dir / repo_or_package_path))

    # TODO: remove this.
    # Workaround for making "pulpcore/cli/common" from pulp-cli be available as:
    # '::: pulpcore.cli.common' (from any markdown)
    # This should be a general solution.
    pulpcore_inside_pulp_cli = source_dir / "pulp-cli/pulpcore"
    pulpcore_dir_exists = Path(source_dir / "pulpcore/pulpcore").exists()
    if pulpcore_dir_exists and pulpcore_inside_pulp_cli.exists():
        shutil.copytree(
            source_dir / "pulp-cli/pulpcore",
            source_dir / "pulpcore/pulpcore",
            dirs_exist_ok=True,
        )
        Path(source_dir / "pulpcore/pulpcore/cli/__init__.py").touch(exist_ok=True)
        Path(source_dir / "pulpcore/pulpcore/cli/common/__init__.py").touch(
            exist_ok=True
        )

    env.conf["plugins"]["mkdocstrings"].config["handlers"]["python"][
        "paths"
    ] = code_sources

    # Configure navigation
    log.info("[pulp-docs] Configuring navigation")
    env.conf["docs_dir"] = docs_dir
    env.conf["nav"] = get_navigation(docs_dir, repos)


    # env.conf["plugins"]["material/blog"].config["blog_dir"] = "pulp-docs/docs/sections/blog"
    # Try to watch CWD/staging_docs
    watched_workdir = Path("staging_docs")
    if watched_workdir.exists():
        env.conf["watch"].append(str(watched_workdir.resolve()))

    # Pass relevant data for future processing
    log.info("[pulp-docs] Done with pulp-docs.")
    env.conf["pulp_repos"] = repos
    env.config["pulp_repos"] = repos
    env.conf["pulp_config"] = config

    # Extra config
    @env.macro
    def get_repos(repo_type="content"):
        "Return repo names by type"
        _repo_type = [repo_type] if repo_type else None
        repos_list = sorted(
            repos.get_repos(repo_types=_repo_type), key=lambda x: x.title
        )
        MD_LINK = "[{title}](site:{path})"
        GITHUB_LINK = (
            "<a href='https://github.com/{owner}/{name}' target='blank'>{title}</a>"
        )
        repos_data = [
            {
                "title": repo.title,
                "version": "3.12.1",
                "restapi_link": MD_LINK.format(
                    title="REST API", path=f"{repo.name}/restapi/"
                ),
                "changes_link": MD_LINK.format(
                    title="Changelog", path=f"{repo.name}/changes/"
                ),
                "codebase_link": GITHUB_LINK.format(
                    title="Codebase", owner=repo.owner, name=repo.name
                ),
            }
            for repo in repos_list
        ]
        return repos_data


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
