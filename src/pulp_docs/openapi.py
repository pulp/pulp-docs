"""
Module for generating open-api json files for selected Pulp plugins.
"""

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import NamedTuple, Optional

from importlib.resources import files

from pulp_docs.constants import BASE_TMPDIR_NAME
from pulp_docs.repository import Repos


def main(
    output_dir: Path, plugins_filter: Optional[list[str]] = None, dry_run: bool = False
):
    """Creates openapi json files for all or selected plugins in output dir."""
    repolist = str(files("pulp_docs").joinpath("data/repolist.yml"))
    repos = Repos.from_yaml(repolist).get_repos(["content"])
    if plugins_filter:
        repos = [p for p in repos if p.name in plugins_filter]

    pulp_plugins = []
    for repo in repos:
        name = repo.name
        label = name.split("_")[-1]
        is_subpackage = bool(getattr(repo, "subpackage_of", False))
        pulp_plugins.append(PulpPlugin(name, label, is_subpackage))

    openapi = OpenAPIGenerator(plugins=pulp_plugins, dry_run=dry_run)
    openapi.generate(target_dir=output_dir)


class PulpPlugin(NamedTuple):
    """
    A Pulp plugin.

    Args:
        name: The repository name for plugin as it exists in github.com
        label: The label of the plugin as its used in django (e.g, pulpcore.label == core)
        is_subpackage: If the plugin is a subpackage (e.g, pulp_file)
    """

    name: str
    label: str
    is_subpackage: bool
    remote_template: str = "https://github.com/pulp/{name}"

    def get_remote_url(self):
        return self.remote_template.format(name=self.name)


class OpenAPIGenerator:
    """
    Responsible for seting up a python environment with the required
    Pulp packages to generate openapi schemas for all registered plugins.

    Args:
        plugin_remotes: A list of git remote urls of the required Pulp packages.
        dry_run: Whether it should execute the commands or just show them.
    """

    def __init__(self, plugins: list[PulpPlugin], dry_run=False):
        self.pulpcore = PulpPlugin("pulpcore", "core", False)
        self.plugins = plugins + [self.pulpcore]
        self.dry_run = dry_run

        # setup working tmpdir
        self.tmpdir = Path(tempfile.gettempdir()) / BASE_TMPDIR_NAME / "openapi"
        self.venv_path = os.path.join(self.tmpdir, "venv")

        shutil.rmtree(self.tmpdir, ignore_errors=True)
        os.makedirs(self.tmpdir, exist_ok=True)

    def generate(self, target_dir: Path):
        """Generate openapi json files at target directory."""
        for plugin in self.plugins:
            self.setup_venv(plugin)
            outfile = str(target_dir / f"{plugin.label}-api.json")
            self.run_python(
                "pulpcore-manager",
                "openapi",
                "--component",
                plugin.label,
                "--file",
                outfile,
            )

    def setup_venv(self, plugin: PulpPlugin):
        """
        Creates virtualenv with plugin.
        """
        create_venv_cmd = ("python", "-m", "venv", self.venv_path)
        url = (
            plugin.get_remote_url()
            if not plugin.is_subpackage
            else self.pulpcore.get_remote_url()
        )
        install_cmd = ["pip", "install", f"git+{url}"]

        if self.dry_run is True:
            print(" ".join(create_venv_cmd))
        else:
            shutil.rmtree(self.venv_path, ignore_errors=True)
            subprocess.run(create_venv_cmd, check=True)

        self.run_python(*install_cmd)

    def run_python(self, *cmd: str) -> str:
        """Run a binary command from within the tmp venv.

        Basicaly: $tmp-venv/bin/{first-arg} {remaining-args}
        """
        cmd_bin = os.path.join(self.venv_path, f"bin/{cmd[0]}")
        final_cmd = [cmd_bin] + list(cmd[1:])
        if self.dry_run is True:
            cmd_str = " ".join(final_cmd)
            print(cmd_str)
            return cmd_str

        os.environ["PULP_CONTENT_ORIGIN"] = "NONE"
        result = subprocess.run(final_cmd, check=True)
        return result.stdout.decode() if result.stdout else ""


def parse_args():
    parser = argparse.ArgumentParser(
        "pulp-docs openapi generation",
        description="Creates a venv for each plugin and generate its openapi-json to output_dir.",
    )
    parser.add_argument(
        "output_dir", help="The directory where the {plugin}-api.json will be stored."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",  # default False
        help="Dont run the commands, only output how they are constructed.",
    )
    parser.add_argument(
        "-l",
        "--plugin-list",
        type=str,
        help="List of plugins that should be used. Use all if ommited.",
    )
    args = parser.parse_args()

    # validation
    if not os.path.isdir(args.output_dir):
        raise TypeError("Must provide an existing directory.")
    return args


if __name__ == "__main__":
    args = parse_args()
    dry_run = args.dry_run
    dest = Path(args.output_dir)

    plugins_filter = []
    if args.plugin_list:
        plugins_filter = [str(p) for p in args.plugin_list.split(",") if p]

    main(dest, plugins_filter, dry_run)
