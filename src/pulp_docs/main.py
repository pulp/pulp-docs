import sys
from pathlib import Path

from pulp_docs.fetch_repos import LocalRepo, download_repos

TMP_DIR = Path("tmp")
WORKDIR = Path.home() / "workspace" / "multirepo-prototype"


def get_abspath(name: str) -> Path:
    return Path(WORKDIR / name).absolute()


def main():
    repolist = [
        LocalRepo("Pulp Rpm", get_abspath("new_repo1")),
        LocalRepo("Pulp Rpm", get_abspath("new_repo2")),
        LocalRepo("Pulp Rpm", get_abspath("new_repo3")),
    ]

    repo_paths = download_repos(repolist, TMP_DIR)
    print(repo_paths)


if __name__ == "__main__":
    sys.exit(main())
