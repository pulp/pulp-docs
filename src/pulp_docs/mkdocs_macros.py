import contextlib
import os
import shutil
import tempfile
import typing as t
from dataclasses import dataclass
from pathlib import Path

import yaml

WORKDIR = Path("tests/fixtures").absolute()


@dataclass
class Repo:
    title: str
    name: str
    rest_api_url: str

    @property
    def url(self):
        return WORKDIR / self.name


RESTAPI_TEMPLATE = "https://docs.pulpproject.org/{}/restapi.html"
PERSONAS = ("dev", "sys-admin", "content-manager")
COMMON_REPO = [Repo("Pulp Core", "core", RESTAPI_TEMPLATE.format("pulpcore"))]
CONTENT_REPOS = [
    Repo("Rpm Packages", "new_repo1", RESTAPI_TEMPLATE.format("pulp_rpm")),
    Repo("Debian Packages", "new_repo2", RESTAPI_TEMPLATE.format("pulp_deb")),
    Repo("Maven", "new_repo3", RESTAPI_TEMPLATE.format("pulp_maven")),
]
OTHER_REPOS = []  # type: ignore
ALL_REPOS = COMMON_REPO + CONTENT_REPOS + OTHER_REPOS


def create_clean_tmpdir(project_dir: Path):
    tmpdir = Path(f"{project_dir}/tmp_dir")
    if tmpdir.exists():
        shutil.rmtree(tmpdir)
    tmpdir.mkdir()
    return tmpdir


def download_repo(origin: Path, dest: Path):
    """
    Download repository source to dest folder as {dest}/{origin.basepath}/(...)

    E.g: tmp_dir/repo1/(...)
    """
    if origin.is_dir():
        shutil.copytree(origin, dest, ignore=shutil.ignore_patterns(
            "tests", "*venv*", "__pycache__"))
    else:
        raise NotImplementedError("No support for remote download yet.")


def get_navigation(tmpdir: Path):
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
        for repo in CONTENT_REPOS:
            lookup_path = tmpdir / template_str.format(repo=repo.name)
            _repo_content = get_children(lookup_path)
            _nav[repo.title] = _repo_content
        return _nav

    def expand_reference(template_str: str):
        _nav = {}
        for repo in ALL_REPOS:
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


def prepare_repositories(TMPDIR: Path):
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
        - repo_docs/template:
            The common asserts used to configure the whole mkdocs site (lives in pulp-docs).

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
                template/
                    assets/...
                    tags.md
                {for-each-repo}/
                    README.md
                    CHANGELOG.md
                    docs/

        ```
    """
    repo_sources_dir = TMPDIR / "repo_sources"
    repo_docs_dir = TMPDIR / "repo_docs"
    for repo in ALL_REPOS:
        # 1. Download repo (copy locally or fetch from GH)
        this_src_dir = repo_sources_dir / repo.name
        this_doc_dir = repo_docs_dir / repo.name
        download_repo(origin=repo.url, dest=this_src_dir)

        # 2. Isolate docs dir (from codebase)
        # this avoid mkdocs for warning about non-docs files
        shutil.copytree(this_src_dir / "docs", this_doc_dir / "docs")
        shutil.copy(this_src_dir / "CHANGELOG.md",
                    this_doc_dir / "CHANGELOG.md")
        shutil.copy(this_src_dir / "README.md", this_doc_dir / "README.md")

        # 3. Generate REST Api pages (workaround)
        rest_api_page = this_doc_dir / "docs" / "rest_api.md"
        rest_api_page.touch()
        md_title = f"# {repo.title} REST Api"
        md_body = f"[{repo.rest_api_url}]({repo.rest_api_url})"
        rest_api_page.write_text(f"{md_title}\n\n{md_body}")

    # Copy template-files (from this plugin) to tmpdir
    shutil.copytree(Path("docs"), repo_docs_dir / "template")
    shutil.copy(WORKDIR / "core" / "docs" /
                "index.md", repo_docs_dir / "index.md")
    return (repo_docs_dir, repo_sources_dir)


def define_env(env):
    """The mkdocs-marcros 'on_configuration' hook. Used to setup the project."""
    # Create tmp_dir with desired repos
    TMPDIR = create_clean_tmpdir(env.project_dir)
    docs_dir, source_dir = prepare_repositories(TMPDIR)

    # Configure mkdocstrings
    code_sources = [str(source_dir / repo.name) for repo in ALL_REPOS]
    env.conf["plugins"]["mkdocstrings"].config["handlers"]["python"]["paths"] = code_sources

    # Configure mkdocs navigation
    env.conf["docs_dir"] = docs_dir
    env.conf["nav"] = get_navigation(docs_dir)
