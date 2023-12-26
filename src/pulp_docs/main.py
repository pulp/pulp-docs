import subprocess
import sys
from pathlib import Path

import click
from importlib_resources import files

from pulp_docs.fetch_repos import LocalRepo, download_repos

TMP_DIR = Path("tmp")
WORKDIR = Path.home() / "workspace" / "multirepo-prototype"


def get_abspath(name: str) -> Path:
    return Path(WORKDIR / name).absolute()


class Config:
    def __init__(self):
        self.verbose = False
        self.workdir = Path()


pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@pass_config
def main(config: Config):
    """
    This is pulp-docs, a cli tool to help run and build multirepo documenation within Pulp project.
    """


@main.command()
@pass_config
def serve(config: Config):
    """Run mkdocs server"""
    mkdocs_file = files("pulp_docs").joinpath("mkdocs.yml")
    print(mkdocs_file)
    cmd = ("mkdocs", "serve", "-f", mkdocs_file)
    subprocess.run(cmd)


@main.command()
@pass_config
def pull(config: Config):
    """Pull repositories source from remote into WORKDIR"""
    repolist = [
        LocalRepo("Pulp Rpm", get_abspath("new_repo1")),
        LocalRepo("Pulp Rpm", get_abspath("new_repo2")),
        LocalRepo("Pulp Rpm", get_abspath("new_repo3")),
    ]

    repo_paths = download_repos(repolist, TMP_DIR)
    print(repo_paths)


if __name__ == "__main__":
    sys.exit(main())
