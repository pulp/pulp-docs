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
import os
import shutil
import tempfile
import typing as t
from pathlib import Path

from importlib_resources import as_file, files
from pulp_docs.plugin_repos import Repos


def create_clean_tmpdir(custom_tmpdir: t.Optional[Path] = None):
    tmpdir_basepath = Path(custom_tmpdir) if custom_tmpdir else Path(
        tempfile.gettempdir())
    tmpdir = tmpdir_basepath / "pulp-docs-tmp"
    if tmpdir.exists():
        shutil.rmtree(tmpdir)
    tmpdir.mkdir()
    return tmpdir


def prepare_repositories(TMPDIR: Path, repos: Repos):
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
    for repo in repos.all:
        # 1. Download repo (copy locally or fetch from GH)
        this_src_dir = repo_sources / repo.name
        print("Downloading '{}', at '{}'".format(repo.name, this_src_dir))
        repo.download(dest_dir=this_src_dir, from_local=True)

        # 2. Isolate docs dir from codebase (makes mkdocs happy)
        this_docs_dir = repo_docs / repo.name
        print("Moving doc related files:\nfrom '{}'\nto '{}'".format(
            this_src_dir, this_docs_dir))
        shutil.copytree(this_src_dir / "docs", this_docs_dir / "docs")
        shutil.copy(this_src_dir / "CHANGELOG.md",
                    this_docs_dir / "CHANGELOG.md")
        shutil.copy(this_src_dir / "README.md", this_docs_dir / "README.md")

        # 3. Generate REST Api pages (workaround)
        rest_api_page = this_docs_dir / "docs" / "rest_api.md"
        rest_api_page.touch()
        md_title = f"# {repo.title} REST Api"
        md_body = f"[{repo.rest_api_link}]({repo.rest_api_link})"
        rest_api_page.write_text(f"{md_title}\n\n{md_body}")

    # Copy template-files (from this plugin) to tmpdir
    data_file_docs = files("pulp_docs").joinpath("data/docs")
    with as_file(data_file_docs) as _docs:
        shutil.copytree(_docs, repo_docs / "pulp-docs")
    shutil.copy(repo_sources / repos.core.name / "docs" /
                "index.md", repo_docs / "index.md")
    return (repo_docs, repo_sources)


def get_navigation(tmpdir: Path, repos: Repos):
    """The dynamic generated 'nav' section of mkdocs.yml"""

    # {repo}/docs/{persona}/{content-type}/*md
    # {repo}/docs/reference/*md
    def get_children(path: t.Union[str, Path]):
        _path = tmpdir / path if isinstance(path, str) else path
        result = [str(file.relative_to(tmpdir))
                  for file in _path.glob("*.md") if not file.name.startswith("_")]
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

    getting_started = [
        {"Overview": "core/docs/sections/getting_started/index.md"},
        {"Quickstart": get_children(
            "core/docs/sections/getting_started/quickstart")},
        {"Fundamentals": get_children(
            "core/docs/sections/getting_started/fundamentals")}
    ]
    guides = [
        {"Overview": "core/docs/sections/guides/index.md"},
        {"For Content-Management": expand_repos(
            "{repo}/docs/content-manager/guides")},
        {"For Sys-Admins": expand_repos("{repo}/docs/sys-admin/guides")},
    ]
    learn = [
        {"Overview": "core/docs/sections/learn/index.md"},
        {"For Content-Management": expand_repos(
            "{repo}/docs/content-manager/learn")},
        {"For Sys-Admins": expand_repos("{repo}/docs/sys-admin/learn")},
    ]
    reference = [
        {"Overview": "core/docs/sections/reference/index.md"},
        {"Repository Map": "core/docs/sections/reference/01-repository-map.md"},
        {"Glossary": "core/docs/sections/reference/02-glossary.md"},
        {"Repositories": expand_reference("{repo}/docs/reference")},
    ]
    development = [
        {"Overview": "core/docs/sections/development/index.md"},
        {"Quickstart": get_children(
            "core/docs/sections/development/quickstart/")},
        {"Onboarding": get_children(
            "core/docs/sections/development/onboarding/")},
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
    # Load repository listing
    base_repolist = os.environ.get("PULPDOCS_BASE_REPOLIST", None)
    repos = Repos.from_yaml(
        Path(base_repolist)) if base_repolist else Repos.test_fixtures()

    # Create tmp_dir with desired repos
    TMPDIR = create_clean_tmpdir()
    docs_dir, source_dir = prepare_repositories(TMPDIR, repos)

    # Configure mkdocstrings
    code_sources = [str(source_dir / repo.name) for repo in repos.all]
    env.conf["plugins"]["mkdocstrings"].config["handlers"]["python"]["paths"] = code_sources

    # Configure mkdocs navigation
    env.conf["docs_dir"] = docs_dir
    env.conf["nav"] = get_navigation(docs_dir, repos)
