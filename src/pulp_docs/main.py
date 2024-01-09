"""
The main CLI module.

It defines its interface.
"""
import subprocess
import os
import sys
from pathlib import Path

import click
from importlib_resources import files

TMP_DIR = Path("tmp")
WORKDIR = Path.home() / "workspace" / "multirepo-prototype"


def get_abspath(name: str) -> Path:
    return Path(WORKDIR / name).absolute()


class Config:
    """
    Params:
        mkdocs_file: the base mkdocs used in serving/building
        repolist: the configuration repositories (which and how to fetch)
    """

    def __init__(self):
        self.verbose = False
        self.workdir = Path()
        self.mkdocs_file = files("pulp_docs").joinpath("data/mkdocs.yml")
        self.repolist = files("pulp_docs").joinpath("data/repolist.yml")


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
    env = os.environ.copy()
    env.update({"PULPDOCS_BASE_REPOLIST": str(config.repolist.absolute())})

    options = (("--config-file", config.mkdocs_file),)
    cmd = ["mkdocs", "serve"]

    for opt in options:
        cmd.extend(opt)
    print("Running:", " ".join(str(s) for s in cmd))
    subprocess.run(cmd, env=env)


@main.command()
@pass_config
def build(config: Config):
    """Build mkdocs site"""
    env = os.environ.copy()
    env.update({"PULPDOCS_BASE_REPOLIST": str(config.repolist.absolute())})

    options = (
        ("--config-file", config.mkdocs_file),
        ("--site-dir", str(Path("site").absolute())),
    )
    cmd = ["mkdocs", "build"]
    for opt in options:
        cmd.extend(opt)
    print("Building:", " ".join(str(s) for s in cmd))
    subprocess.run(cmd, env=env)


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
