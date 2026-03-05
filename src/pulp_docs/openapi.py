"""
Module for generating open-api json files for selected Pulp plugins.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import NamedTuple, Optional

CONTAINER_IMAGE = "quay.io/pulp/pulp-minimal:stable"
CONTAINER_NAME_PREFIX = "pulpdocs-openapi"
CONTAINER_OUTPUT_PATH = "/output"


class PodmanError(Exception):
    """Raised when a podman command fails."""

    pass


class PluginInstallError(Exception):
    """Raised when plugin installation fails."""

    def __init__(self, repository_paths: list[Path]):
        plugins_str = ", ".join(str(path.name) for path in repository_paths)
        message = (
            "Failed to install plugins.\n"
            "Are all these components Pulp projects with REST APIs?\n"
            f"Trying with: {plugins_str}"
        )
        super().__init__(message)
        self.repository_paths = repository_paths


class OpenApiPlugin(NamedTuple):
    repository_path: Path
    plugin_label: str


class OpenAPIGenerator:
    """Generate openapi schemas for all registered plugins.

    Args:
        plugins: A list of OpenApiPlugin with repository paths and labels.
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
        self.repository_paths = list({p.repository_path for p in plugins if p.repository_path})
        self.dry_run = dry_run
        self.image = image

    def generate(self, output_dir: Path):
        """Generate openapi json files at target directory."""
        if not self.repository_paths:
            return  # nothing to do here
        self._check_podman()
        output_dir.mkdir(parents=True, exist_ok=True)
        container = self._init_container(output_dir)
        with container.run():
            self._install_plugins(container)
            self._generate_schemas(container)

    def _init_container(self, output_dir: Path):
        abs_target = str(output_dir.resolve())
        volumes = {abs_target: CONTAINER_OUTPUT_PATH}

        # Mount repository paths as volumes using repository names
        for repo_path in self.repository_paths:
            container_repo_path = f"/repos/{repo_path.name}"
            volumes[str(repo_path.resolve())] = container_repo_path

        return PodmanContainer(
            image=self.image,
            volumes=volumes,
            env={"PULP_CONTENT_ORIGIN": "NONE"},
            dry_run=self.dry_run,
        )

    def _install_plugins(self, container: PodmanContainer):
        pip_args = [f"/repos/{repo_path.name}" for repo_path in self.repository_paths]
        try:
            container.exec("pip", "install", *pip_args)
        except PodmanError as e:
            raise PluginInstallError(self.repository_paths) from e

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
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            cmd_str = " ".join(cmd)
            raise PodmanError(
                f"Podman command failed: {cmd_str}\nReturn code: {e.returncode}"
            ) from e
