"""
The main CLI module.

It defines its interface.
"""

import os
import subprocess
import sys
import tempfile
import typing as t
from pathlib import Path

import click
from importlib_resources import files

TMP_DIR = Path("tmp")
WORKDIR = Path.home() / "workspace" / "multirepo-prototype"


def get_abspath(name: str) -> Path:
    return Path(WORKDIR / name).absolute()


def cast_bool(value: str) -> bool:
    return False if value.lower() in ("f", "false") else True


class Config:
    """
    Configuration shared among CLI and mkdocs_macro.py hooks.

    Params:
        mkdocs_file: the base mkdocs used in serving/building
        repolist: the configuration repositories (which and how to fetch)
        clear_cache: whether to clear cache before downloading from remote
    """

    def __init__(self, from_environ: bool = False):
        if from_environ is False:
            self.verbose = False
            self.workdir = Path().absolute()
            self.mkdocs_file = files("pulp_docs").joinpath("data/mkdocs.yml").absolute()
            self.repolist = files("pulp_docs").joinpath("data/repolist.yml").absolute()
            self.clear_cache = False

            if env_mkdocs := os.environ.get("PULPDOCS_MKDOCS_FILE"):
                self.mkdocs_file = Path(env_mkdocs)
        else:
            self.verbose = cast_bool(os.environ["PULPDOCS_VERBOSE"])
            self.workdir = Path(os.environ["PULPDOCS_WORKDIR"])
            self.mkdocs_file = Path(os.environ["PULPDOCS_MKDOCS_FILE"])
            self.repolist = Path(os.environ["PULPDOCS_REPOLIST"])
            self.clear_cache = cast_bool(os.environ["PULPDOCS_CLEAR_CACHE"])

    def get_environ_dict(self):
        return {f"PULPDOCS_{k.upper()}": str(v) for k, v in self.__dict__.items()}


pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option("--verbose", "-v", is_flag=True)
@pass_config
def main(config: Config, verbose: bool):
    """
    This is pulp-docs, a cli tool to help run and build multirepo documentation within Pulp project.
    """
    config.verbose = verbose


# mkdocs help wrapper
watch_help = (
    "A directory or file to watch for live reloading. Can be supplied multiple times."
)
no_reload_help = "Disable the live reloading in the development server."


@main.command()
@click.option(
    "--clear-cache",
    default=False,
    is_flag=True,
    help="Whether to clear the cache before serving (default=False).",
)
@click.option("--verbose", "-v", is_flag=True)
@click.option(
    "-w",
    "--watch",
    help=watch_help,
    type=click.Path(exists=True),
    multiple=True,
    default=[],
)
@click.option("--no-livereload", "livereload", flag_value=False, help=no_reload_help)
@click.option("--livereload", "livereload", flag_value=True, default=True, hidden=True)
@pass_config
def serve(
    config: Config,
    clear_cache: bool,
    verbose: bool,
    watch: t.List[Path],
    livereload: bool,
):
    """Run mkdocs server."""
    env = os.environ.copy()
    config.clear_cache = clear_cache
    config.verbose = verbose
    env.update(config.get_environ_dict())

    watch_list = [("--watch", watched) for watched in watch]
    flag_list = []
    if livereload is False:
        flag_list.append(("--no-livereload",))

    options: t.List[tuple] = [("--config-file", config.mkdocs_file)]
    options.extend(watch_list)
    options.extend(flag_list)

    cmd = ["mkdocs", "serve"]
    for opt in options:
        cmd.extend(opt)
    print("Running:", " ".join(str(s) for s in cmd))
    subprocess.run(cmd, env=env)


@main.command()
@pass_config
def build(config: Config):
    """Build mkdocs site."""
    config.verbose = True
    env = os.environ.copy()
    env.update(config.get_environ_dict())

    options = (
        ("--config-file", config.mkdocs_file),
        ("--site-dir", str(Path("site").absolute())),
    )
    cmd = ["mkdocs", "build"]
    for opt in options:
        cmd.extend(opt)
    print("Building:", " ".join(str(s) for s in cmd))
    result = subprocess.run(cmd, env=env)
    sys.exit(result.returncode)


@main.command()
@pass_config
def status(config: Config):
    """Print relevant information about repositories that will be used."""
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main())
