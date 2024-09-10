"""
The classes representing plugins git/git-hub repositories.

Their purpose is to facilitate declaring and downloading the source-code.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tarfile
import tempfile
import typing as t
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

import httpx
import configparser
import tomllib
import yaml

from pulp_docs.utils.general import get_git_ignored_files

log = logging.getLogger("mkdocs")

FIXTURE_WORKDIR = Path("tests/fixtures").absolute()
DOWNLOAD_CACHE_DIR = Path(tempfile.gettempdir()) / "repo_downloads"


# @dataclass # raising errors in py311/312
class RepoStatus:
    """
    Usefull status information about a downloaded repository.
    """

    def __init__(self, **kwargs):
        self.download_source = kwargs.get("download_source", None)
        self.use_local_checkout = kwargs.get("use_local_checkout", False)
        self.has_readme = kwargs.get("has_readme", True)
        self.has_changelog = kwargs.get("has_changelog", True)
        self.has_staging_docs = kwargs.get("has_staging_docs", True)
        self.using_cache = kwargs.get("using_cache", False)
        self.original_refs = kwargs.get("original_refs", None)

    def __str__(self):
        return str(self.__dict__)


@dataclass
class Repo:
    """
    A git/gh repository representation.

    The real repository content is plugin sourcecode and markdown documentation.
    """

    title: str
    name: str
    owner: str = "pulp"
    branch: str = "main"
    branch_in_use: t.Optional[str] = None
    local_basepath: t.Optional[Path] = None
    subpackages: t.Optional[t.List] = None
    status: RepoStatus = field(default_factory=lambda: RepoStatus())
    type: t.Optional[str] = None
    dev_only: bool = False
    version: t.Optional[str] = None
    template_config: t.Optional[dict] = None
    app_label: t.Optional[str] = None

    def __post_init__(self):
        self.branch_in_use = self.branch_in_use or self.branch

    def download(
        self, dest_dir: Path, clear_cache: bool = False, disabled: t.Sequence[str] = []
    ) -> str:
        """
        Download repository source from url into the {dest_dir} Path.

        Uses local in the following cases and order (else, downloads from github):
        - local_basepath is explicitly set
        - parent directory contain dir with self.name

        For remote download, uses GitHub API to get latest source code:

        Args:
            dest: The destination directory where source files will be saved.
                e.g /tmp/pulp-tmp/repo_sources/pulpcore
            clear_cache: Whether the cache should be cleared before downloading.
        Returns:
            The download url used
        """
        log.info("Downloading '{}' to '{}'".format(self.name, dest_dir.absolute()))

        if clear_cache is True:
            log.info("Clearing cache dir")
            shutil.rmtree(DOWNLOAD_CACHE_DIR, ignore_errors=True)
            DOWNLOAD_CACHE_DIR.mkdir()

        cached_repo = Path(DOWNLOAD_CACHE_DIR / self.name).absolute()
        download_from = cached_repo
        src_copy_path = cached_repo
        log_header = ""

        # from local filesystem
        if self.local_basepath is not None:
            log_header = "Using local checkout"
            download_from = Path(self.local_basepath / self.name).absolute()
            src_copy_path = download_from
        # from cache
        elif cached_repo.exists():
            log_header = "Using cache in tmpdir"
            download_from = cached_repo
            src_copy_path = cached_repo
            self.status.using_cache = True
        # from remote
        elif not cached_repo.exists():
            log_header = "Downloading from remote"
            src_copy_path = DOWNLOAD_CACHE_DIR / self.name
            download_from = download_from_gh_main(
                src_copy_path,
                self.owner,
                self.name,
                self.branch_in_use,
            )

        # copy from source/cache to pulp-docs workdir
        log.info(f"{log_header}: source={download_from}, copied_from={src_copy_path}")

        # ignore files lisetd in .gitignore and files that starts with "."
        # shutil ignore limitation: https://github.com/Miserlou/Zappa/issues/692#issuecomment-283012663
        ignore_patterns = get_git_ignored_files(Path(src_copy_path)) + [".*"]

        # skip blog for faster reloads
        if self.name == "pulp-docs" and "blog" in disabled:
            ignore_patterns.append("*posts")

        shutil.copytree(
            src_copy_path,
            dest_dir,
            ignore=shutil.ignore_patterns(*ignore_patterns),
            dirs_exist_ok=True,
        )

        # get version
        version_file = src_copy_path / ".bumpversion.cfg"
        if version_file.exists():
            config = configparser.ConfigParser()
            config.read(version_file)
            self.version = config["bumpversion"]["current_version"]
        else:
            version_file = src_copy_path / "pyproject.toml"
            if version_file.exists():
                content = tomllib.loads(version_file.read_text())
                self.version = (
                    content.get("tool", {})
                    .get("bumpversion", {})
                    .get("current_version")
                )

        # update app_label for app plugins
        template_config_file = src_copy_path / "template_config.yml"
        if template_config_file.exists():
            self.template_config = yaml.load(
                template_config_file.read_bytes(), Loader=yaml.SafeLoader
            )
            app_label_map = {
                p["name"]: p["app_label"] for p in self.template_config["plugins"]
            }
            subpackages = self.subpackages or []
            for plugin in (self, *subpackages):
                plugin.app_label = app_label_map.get(plugin.name, None)

        self.status.download_source = str(download_from)
        return self.status.download_source


def download_from_gh_main(dest_dir: Path, owner: str, name: str, branch: str):
    """
    Download repository source-code from main

    Returns the download url.
    """
    url = f"https://github.com/{owner}/{name}.git"
    cmd = ("git", "clone", "--depth", "1", "--branch", branch, url, str(dest_dir))
    log.info("Downloading from Github with:\n{}".format(" ".join(cmd)))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        log.error(
            f"An error ocurred while trying to download '{name}' source-code:\n{e}"
        )
        raise

    log.info("Done.")
    return url


def download_from_gh_latest(dest_dir: Path, owner: str, name: str):
    """
    Download repository source-code from latest GitHub Release (w/ GitHub API).

    See: https://docs.github.com/en/rest/releases/releases?apiVersion=2022-11-28#get-the-latest-release

    Returns the download url.
    """
    latest_release_link_url = (
        "https://api.github.com/repos/{}/{}/releases/latest".format(owner, name)
    )

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
    return latest_release_tar_url


@dataclass
class SubPackage:
    """A package that lives under another Repo."""

    name: str
    title: str
    subpackage_of: str
    type: t.Optional[str] = None
    status: RepoStatus = field(default_factory=lambda: RepoStatus())
    local_basepath = None
    branch_in_use = ""
    branch = ""
    owner = ""
    dev_only: bool = False
    version: t.Optional[str] = None
    app_label: t.Optional[str] = None


@dataclass
class Repos:
    """A collection of Repos"""

    repo_by_types: dict[str, Repo] = field(default_factory=dict)

    def update_local_checkouts(self):
        """Update repos to use local checkout, if exists in the parent dir of CWD"""
        for repo in self.all:
            checkout_dir = Path().absolute().parent / repo.name
            if repo.local_basepath is None and checkout_dir.exists():
                repo.status.use_local_checkout = True
                repo.local_basepath = Path().absolute().parent
                # looks like 'refs/head/main'
                checkout_refs = Path(checkout_dir / ".git" / "HEAD").read_text()
                checkout_refs = checkout_refs[len("ref: ") :].replace("\n", "")
                repo.branch_in_use = checkout_refs

    def get(self, repo_name: str) -> t.Optional[Repo]:
        repo = [r for r in self.all if r.name == repo_name] or [None]
        return repo[0]

    @property
    def repo_types(self):
        return list(self.repo_by_types.keys())

    @property
    def all(self):
        """The set of repositories and subpackages"""
        repos = [
            repo for repo_type in self.repo_by_types.values() for repo in repo_type
        ]
        subpackages = []
        for repo in repos:
            if repo.subpackages:
                subpackages.extend(repo.subpackages)
        return sorted(repos + subpackages, key=lambda x: x.title)

    def get_repos(self, repo_types: t.Optional[t.List] = None):
        """Get a set of repositories and subpackages by type."""
        # Default case
        if repo_types is None:
            return self.all

        # Filter by repo_types
        repos_and_pkgs = self.all
        return [repo for repo in repos_and_pkgs if repo.type in repo_types]

    @classmethod
    def from_yaml(cls, path: str):
        """
        Load repositories listing from yaml file (repolist.yml)

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
        log.info("[pulp-docs] Loading repolist file from repofile.yml")
        file = Path(path)
        if not file.exists():
            raise ValueError("File does not exist:", file)
        log.info(f"repofile={str(file.absolute())}")

        # Create Repo objects from yaml data
        repos: t.Dict[str, t.List] = {}
        nested_packages: t.Dict[str, t.List[SubPackage]] = {}
        with open(file, "r") as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
            repo_types = data["meta"]["repo_types"]
            for repo_type in repo_types:
                repos[repo_type] = []
                for repo in data["repos"][repo_type]:
                    # Collect nested packages
                    if parent_package := repo.get("subpackage_of", None):
                        nested_packages.setdefault(parent_package, []).append(
                            SubPackage(**repo, type=repo_type)
                        )
                        continue
                    # Create regular packages
                    repos[repo_type].append(Repo(**repo, type=repo_type))

        # Update Repo objects that contain subpackages
        for parent_repo_name, subpackages_list in nested_packages.items():
            flat_repos = [repo for type_ in repo_types for repo in repos[type_]]
            for repo in flat_repos:
                if repo.name == parent_repo_name:
                    repo.subpackages = subpackages_list

        return Repos(repos)

    @classmethod
    def test_fixtures(cls):
        """Factory of test Repos. Uses fixtures shipped in package data."""
        log.info("[pulp-docs] Loading repolist file from fixtures")
        DEFAULT_CORE = [Repo("Pulp Core", type="core")]
        DEFAULT_CONTENT_REPOS = [
            Repo(
                "Rpm Packages",
                "new_repo1",
                local_basepath=FIXTURE_WORKDIR,
                type="content",
            ),
            Repo(
                "Debian Packages",
                "new_repo2",
                local_basepath=FIXTURE_WORKDIR,
                type="content",
            ),
            Repo("Maven", "new_repo3", local_basepath=FIXTURE_WORKDIR, type="content"),
            Repo(
                "Docs Tool", "pulp-docs", local_basepath=FIXTURE_WORKDIR, type="other"
            ),
        ]
        repo_types = {
            "core": DEFAULT_CORE,
            "content": DEFAULT_CONTENT_REPOS,
        }
        return Repos(repo_by_types=repo_types)
