"""
Module for generating open-api json files for selected Pulp plugins.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import NamedTuple, Optional

from pulp_docs.cli import get_default_mkdocs
from pulp_docs.plugin import ComponentLoader, default_lookup_paths

CONTAINER_IMAGE = "quay.io/pulp/pulp-minimal:stable"
CONTAINER_NAME_PREFIX = "pulpdocs-openapi"
CONTAINER_OUTPUT_PATH = "/output"


def main(output_dir: Path, filter_list: Optional[list[str]] = None, dry_run: bool = False) -> int:
    """Creates openapi json files for found plugins in the output_dir.

    Optionally filter the found plugins with a filter list.
    """

    try:
        openapi_plugins = get_plugins(filter_list or [])
        openapi = OpenAPIGenerator(plugins=openapi_plugins, dry_run=dry_run)
        openapi.generate(output_dir=output_dir)
    except Exception as e:
        print(e, file=sys.stderr)
        return 1
    return 0


def get_plugins(filter_list: list[str]) -> list[OpenApiPlugin]:
    mkdocs_config = get_default_mkdocs()
    lookup_paths = default_lookup_paths()
    load_result = ComponentLoader(lookup_paths, mkdocs_config=mkdocs_config).load_all()
    all_specs = load_result.all_specs

    if filter_list:
        selected = [p for p in all_specs if p.component_name in filter_list]
    else:
        selected = all_specs

    return [OpenApiPlugin(git_url=spec.git_url, plugin_label=spec.label) for spec in selected]


class OpenApiPlugin(NamedTuple):
    git_url: str
    plugin_label: str


class OpenAPIGenerator:
    """Generate openapi schemas for all registered plugins.

    Args:
        plugins: A list of OpenApiPlugin with git URLs and labels.
        dry_run: Whether it should execute the commands or just show them.
        image: The container image to use.
    """

    def __init__(
        self,
        plugins: list[OpenApiPlugin],
        dry_run: bool = False,
        image: str = CONTAINER_IMAGE,
    ):
        self.plugins = plugins
        self.git_urls = list({p.git_url for p in plugins})
        self.dry_run = dry_run
        self.image = image

    def generate(self, output_dir: Path):
        """Generate openapi json files at target directory."""
        self._check_podman()
        output_dir.mkdir(parents=True, exist_ok=True)
        container = self._init_container(output_dir)
        with container.run():
            self._install_plugins(container)
            self._generate_schemas(container)

    def _init_container(self, output_dir: Path):
        abs_target = str(output_dir.resolve())
        return PodmanContainer(
            image=self.image,
            volumes={abs_target: CONTAINER_OUTPUT_PATH},
            env={"PULP_CONTENT_ORIGIN": "NONE"},
            dry_run=self.dry_run,
        )

    def _install_plugins(self, container: PodmanContainer):
        if not self.git_urls:
            return
        pip_args = [f"git+{url}" for url in self.git_urls]
        container.exec("pip", "install", *pip_args)

    def _check_podman(self):
        if not self.dry_run and not shutil.which("podman"):
            raise RuntimeError("podman is required but was not found on PATH. ")

    def _generate_schemas(self, container: PodmanContainer):
        for plugin in self.plugins:
            outfile = f"{CONTAINER_OUTPUT_PATH}/{plugin.plugin_label}-api.json"
            container.exec(
                "pulpcore-manager",
                "openapi",
                "--component",
                plugin.plugin_label,
                "--file",
                outfile,
            )


class PodmanContainer:
    """Manage a podman container lifecycle (create, start, exec, remove).

    Use the `run` context manager to ensure cleanup::

        container = PodmanContainer(image="myimage", volumes={"/host": "/container"})
        with container.run():
            container.exec("pip", "install", "some-package")
            container.exec("my-command", "--flag", "value")
    """

    def __init__(
        self,
        image: str,
        volumes: Optional[dict[str, str]] = None,
        env: Optional[dict[str, str]] = None,
        name: Optional[str] = None,
        dry_run: bool = False,
    ):
        self.image = image
        self.volumes = volumes or {}
        self.env = env or {}
        self.name = name or f"{CONTAINER_NAME_PREFIX}-{os.getpid()}"
        self.dry_run = dry_run

    @contextmanager
    def run(self):
        """Start the container and remove it on exit."""
        self._create()
        self._start()
        try:
            yield self
        finally:
            self._remove()

    def exec(self, *cmd: str):
        """Run a command inside the container."""
        self._run_podman("exec", self.name, *cmd)

    def _create(self):
        cmd = ["create", "--name", self.name]
        for key, value in self.env.items():
            cmd.extend(["-e", f"{key}={value}"])
        for host_path, container_path in self.volumes.items():
            cmd.extend(["-v", f"{host_path}:{container_path}:Z"])
        cmd.extend([self.image, "sleep", "infinity"])
        self._run_podman(*cmd)

    def _start(self):
        self._run_podman("start", self.name)

    def _remove(self):
        self._run_podman("rm", "--force", self.name)

    def _run_podman(self, *args: str):
        cmd = ["podman", *args]
        if self.dry_run:
            print(" ".join(cmd))
            return
        subprocess.run(cmd, check=True)
