import os
import shutil
import tarfile
import tempfile
import typing as t
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

import httpx
import yaml
from importlib_resources import as_file, files

WORKDIR = Path("tests/fixtures").absolute()
RESTAPI_TEMPLATE = "https://docs.pulpproject.org/{}/restapi.html"
PERSONAS = ("dev", "sys-admin", "content-manager")


@dataclass
class Repo:
    title: str
    name: str
    owner: str = "pulp"
    local_basepath: Path = WORKDIR

    @property
    def local_url(self):
        """Return local url for respository as {self.local_basepath}/{self.name}"""
        return self.local_basepath / self.name

    @property
    def rest_api_link(self):
        return RESTAPI_TEMPLATE.format(self.name)

    def download(self, dest_dir: Path, from_local: bool = False) -> Path:
        """
        Download repository source from url into the {dest_dir} Path.

        For remote download, uses GitHub API to get latest source code:
        https://docs.github.com/en/rest/releases/releases?apiVersion=2022-11-28#get-the-latest-release

        Args:
            dest: The destination directory where source files will be saved.
            from_local: If true, the repo is copied from the local path {self.local_url} instead of being
                        downloaded from remote.
        """
        # Copy from local filesystem
        if from_local is True:
            shutil.copytree(self.local_url, dest_dir, ignore=shutil.ignore_patterns(
                "tests", "*venv*", "__pycache__"))
            return self.local_basepath

        # or Download from remote
        latest_release_link_url = "https://api.github.com/repos/{}/{}/releases/latest".format(
            self.owner, self.name)

        print("Fetching latest release with:", latest_release_link_url)
        response = httpx.get(latest_release_link_url)
        latest_release_tar_url = response.json()["tarball_url"]

        print("Downloadng tarball from:", latest_release_tar_url)
        response = httpx.get(latest_release_tar_url, follow_redirects=True)
        bytes_data = BytesIO(response.content)

        print("Extracting tarball to:", dest_dir)
        with tempfile.TemporaryDirectory() as tmpdir:
            with tarfile.open(fileobj=bytes_data) as tar:
                tar.extractall(tmpdir, filter="data")
            # workaround because I cant know the name of the extracted dir with tarfile lib
            dirname = Path(tmpdir) / tar.getmembers()[0].name.split()[0]
            shutil.move(str(dirname.absolute()), str(dest_dir.absolute()))
        # Reference:
        # https://www.python-httpx.org/quickstart/#binary-response-content
        # https://docs.python.org/3/library/tarfile.html#tarfile.TarFile.extractall
        return dest_dir


@dataclass
class Repos:
    core: Repo
    content: t.List[Repo] = field(default_factory=list)
    other: t.List[Repo] = field(default_factory=list)

    @property
    def all(self):
        return [self.core] + self.content + self.other

    @classmethod
    def from_yaml(cls, path: str):
        """
        Load repositories listing from yaml file

        Example:
            ```yaml
            repos:
                core:
                  name:
                  title:
                content:
                  - name: pulp_rpm
                    title: Rpm Package
                  - name: pulp_maven
                    title: Maven
            ```
        """
        file = Path(path)
        if not file.exists():
            raise ValueError("File does not exist:", file)

        with open(file, "r") as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
        repos = data["repos"]
        core_repo = Repo(**repos["core"][0])
        content_repos = [Repo(**repo) for repo in repos["content"]]
        other_repos = [Repo(**repo) for repo in repos["other"]]
        return Repos(core=core_repo, content=content_repos, other=other_repos)

    @classmethod
    def test_fixtures(cls):
        DEFAULT_CORE = Repo("Pulp Core", "core")
        DEFAULT_CONTENT_REPOS = [
            Repo("Rpm Packages", "new_repo1"),
            Repo("Debian Packages", "new_repo2"),
            Repo("Maven", "new_repo3"),
        ]
        return Repos(core=DEFAULT_CORE, content=DEFAULT_CONTENT_REPOS)


def create_clean_tmpdir(custom_tmpdir: t.Optional[Path] = None):
    tmpdir_basepath = Path(custom_tmpdir) if custom_tmpdir else Path(
        tempfile.gettempdir())
    tmpdir = tmpdir_basepath / "pulp-docs-tmp"
    if tmpdir.exists():
        shutil.rmtree(tmpdir)
    tmpdir.mkdir()
    return tmpdir


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
        shutil.copy(this_src_dir / "CHANGELOG.md", this_docs_dir / "CHANGELOG.md")
        shutil.copy(this_src_dir / "README.md", this_docs_dir / "README.md")

        # 3. Generate REST Api pages (workaround)
        rest_api_page = this_docs_dir / "docs" / "rest_api.md"
        rest_api_page.touch()
        md_title = f"# {repo.title} REST Api"
        md_body = f"[{repo.rest_api_link}]({repo.rest_api_link})"
        rest_api_page.write_text(f"{md_title}\n\n{md_body}")

    # Copy template-files (from this plugin) to tmpdir
    data_file_docs = files("pulp_docs").joinpath("docs")
    with as_file(data_file_docs) as _docs:
        shutil.copytree(_docs, repo_docs / "pulp-docs")
    shutil.copy(repo_sources / repos.core.name / "docs" /
                "index.md", repo_docs / "index.md")
    return (repo_docs, repo_sources)


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
