"""
The classes representing plugins git/git-hub repositories.

Their purpose is to facilitate declaring and downloading the source-code.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tarfile
import tempfile
import typing as t
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

import httpx
import yaml

log = logging.getLogger("mkdocs")

FIXTURE_WORKDIR = Path("tests/fixtures").absolute()
RESTAPI_TEMPLATE = "https://docs.pulpproject.org/{}/restapi.html"


@dataclass
class RepoStatus:
    """
    Usefull status information about a downloaded repository.
    """

    download_source: t.Optional[str] = None
    use_local_checkout: bool = False
    has_readme: bool = True
    has_changelog: bool = True
    has_staging_docs: bool = True
    using_cache: bool = False


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
    local_basepath: t.Optional[Path] = None
    status: RepoStatus = RepoStatus()
    type: t.Optional[str] = None

    @property
    def local_url(self):
        """Return local url for respository as {self.local_basepath}/{self.name}"""
        return self.local_basepath / self.name

    @property
    def rest_api_link(self):
        return RESTAPI_TEMPLATE.format(self.name)

    def download(self, dest_dir: Path) -> str:
        """
        Download repository source from url into the {dest_dir} Path.

        Uses local in the following cases and order (else, downloads from github):
        - local_basepath is explicitly set
        - parent directory contain dir with self.name

        For remote download, uses GitHub API to get latest source code:

        Args:
            dest: The destination directory where source files will be saved.
                e.g /tmp/pulp-tmp/repo_sources/pulpcore
        Returns:
            The download url used
        """
        log.info("Downloading '{}' to '{}'".format(self.name, dest_dir.absolute()))

        # Download from local filesystem
        download_url = None
        if self.local_basepath is not None:
            log.warning(f"Using local checkout: {str(self.local_url)}")
            download_url = self.local_url.absolute()
            shutil.copytree(
                self.local_url,
                dest_dir,
                ignore=shutil.ignore_patterns("tests", "*venv*", "__pycache__"),
            )
        # Download from remote
        elif not dest_dir.exists():
            download_url = download_from_gh_main(
                dest_dir, self.owner, self.name, self.branch
            )
        else:
            log.warning(f"Using cache: {str(dest_dir.absolute())}")
            self.status.using_cache = True
            download_url = str(dest_dir.absolute())

        # Return url used
        self.status.download_source = str(download_url)
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
    except subprocess.CalledProcessError:
        log.error(
            "An error ocurred while trying to download '{name}' source-code:".format(
                name=name
            )
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
class Repos:
    """A collection of Repos"""

    core: Repo
    content: t.List[Repo] = field(default_factory=list)
    other: t.List[Repo] = field(default_factory=list)

    @property
    def all(self):
        return [self.core] + self.content + self.other

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

        with open(file, "r") as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
        repos = data["repos"]
        core_repo = Repo(**repos["core"][0], type="core")
        content_repos = [Repo(**repo, type="content") for repo in repos["content"]]
        other_repos = [Repo(**repo, type="other") for repo in repos["other"]]
        return Repos(core=core_repo, content=content_repos, other=other_repos)

    @classmethod
    def test_fixtures(cls):
        """Factory of test Repos. Uses fixtures shipped in package data."""
        log.info("[pulp-docs] Loading repolist file from fixtures")
        DEFAULT_CORE = Repo("Pulp Core", "core", type="core")
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
        ]
        return Repos(core=DEFAULT_CORE, content=DEFAULT_CONTENT_REPOS)
