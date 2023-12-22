import shutil
import tempfile
import typing as t
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlretrieve

import requests


@dataclass
class LocalRepo:
    name: str
    href: Path

    def download(self, destination: Path) -> Path:
        reponame = self.href.name
        return shutil.copytree(self.href, destination / reponame)


class DocRepo:
    """Represent all relevant documentation of repository"""

    def __init__(self, basepath: Path):
        self.basepath = basepath

    def get_changelog(self) -> Path:
        ...

    def get_by_glob(self, partial_path: str) -> t.List[Path]:
        """
        Get recursive globs from doc relative path.

        Example:
            ```
            doc_repo = DocRepo(repo_basepath)
            doc_repo.get_by_glob("content-manager/guides")
            doc_repo.get_by_glob("reference")
            doc_repo.get_by_glob("common/guides")
            ```
        """
        return Path()


def download_repos(repos: t.List[LocalRepo], dest: Path):
    if dest.exists():
        if dest != "tmp" or input(f"Destination dir '{dest}' exists. Clear it? ").lower() in ("yes", "y"):
            print("Cleaning dest dir:", dest)
            shutil.rmtree(dest)
        else:
            print("Exiting...")
            return
    print("Creating dest dir:", dest)
    dest.mkdir(exist_ok=True)

    repo_paths = []
    for repo in repos:
        print("Downloading:", repo.href)
        repo_paths.append(repo.download(dest))
    print("Done")
    return repo_paths
