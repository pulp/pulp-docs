"""
Module for generating open-api json files for selected Pulp plugins.
"""

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from mkdocs.config import load_config

from pulp_docs.cli import get_default_mkdocs
from pulp_docs.plugin import ComponentOption

BASE_TMPDIR_NAME = "pulpdocs_tmp"
CURRENT_DIR = Path(__file__).parent.absolute()


def main(output_dir: Path, plugins_filter: Optional[list[str]] = None, dry_run: bool = False):
    """Creates openapi json files for all or selected plugins in output dir."""

    def filter_plugin(name: str) -> bool:
        if not plugins_filter:
            return True
        return name in plugins_filter or name == "pulpcore"

    def get_plugins() -> list[ComponentOption]:
        mkdocs_yml = str(get_default_mkdocs())
        pulpdocs_plugin = load_config(mkdocs_yml).plugins["PulpDocs"]
        all_components = pulpdocs_plugin.config.components
        return [c for c in all_components if c.rest_api]

    all_plugins = get_plugins()
    all_plugins = [p for p in all_plugins if filter_plugin(p.name)]
    openapi = OpenAPIGenerator(plugins=all_plugins, dry_run=dry_run)
    openapi.generate(target_dir=output_dir)


class OpenAPIGenerator:
    """
    Responsible for setting up a python environment with the required
    Pulp packages to generate openapi schemas for all registered plugins.

    Args:
        plugin_remotes: A list of git remote urls of the required Pulp packages.
        dry_run: Whether it should execute the commands or just show them.
    """

    def __init__(self, plugins: list[ComponentOption], dry_run=False):
        self.pulpcore = next(filter(lambda p: p.name == "pulpcore", plugins))
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

    def setup_venv(self, plugin: ComponentOption):
        """
        Creates virtualenv with plugin.
        """
        create_venv_cmd = ("python", "-m", "venv", self.venv_path)
        # setuptools provides distutils for python >=3.12.
        install_cmd = ["pip", "install", f"git+{plugin.git_url}", "setuptools"]

        if self.dry_run is True:
            print(" ".join(create_venv_cmd))
        else:
            shutil.rmtree(self.venv_path, ignore_errors=True)
            subprocess.run(create_venv_cmd, check=True)

        self.run_python(*install_cmd)

    def run_python(self, *cmd: str) -> str:
        """Run a binary command from within the tmp venv.

        Basically: $tmp-venv/bin/{first-arg} {remaining-args}
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
        help="List of plugins that should be used. Use all if omitted.",
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
