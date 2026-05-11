"""
Module for generating open-api json files for selected Pulp plugins.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import NamedTuple


class OpenApiPlugin(NamedTuple):
    repository_path: Path
    plugin_label: str


class OpenAPIGenerator:
    """Generate openapi schemas.

    Args:
        plugins: A list of OpenApiPlugin with repository paths and labels.
        dry_run: Whether it should execute the commands or just show them.
    """

    # use this content instead of the real openapi spec when dry-run is enabled
    DRY_RUN_SPECFILE_TEMPLATE = "dry-run specfile for: {plugin_label}"

    def __init__(self, plugins: list[OpenApiPlugin], dry_run: bool = False):
        self.plugins = plugins
        self.repository_paths = list({p.repository_path for p in plugins if p.repository_path})
        self.dry_run = dry_run

    def generate(self) -> dict[str, Path]:
        """Generate openapi json files.

        Returns map of plugin labels to generated spec path.
        """
        if not self.plugins:
            return {}
        output_dir = Path(tempfile.TemporaryDirectory(delete=False).name)
        output_dir.mkdir(parents=True, exist_ok=True)
        label_to_specfile = {}
        for plugin in self.plugins:
            filename = f"{plugin.plugin_label}-api.json"
            file_path = output_dir / filename
            self._generate_schema(plugin.plugin_label, file_path)
            label_to_specfile[plugin.plugin_label] = file_path
        return label_to_specfile

    def _generate_schema(self, plugin_label: str, output_file: Path):
        cmd = ["uv", "run", "--isolated", "--with", "setuptools", "--with", "pulp_rust"]
        for repo_path in self.repository_paths:
            cmd.extend(["--with", str(repo_path.resolve())])
        cmd.extend(
            ["pulpcore-manager", "openapi", "--component", plugin_label, "--file", str(output_file)]
        )
        if self.dry_run:
            print(" ".join(cmd))
            output_file.write_text(self.DRY_RUN_SPECFILE_TEMPLATE.format(plugin_label=plugin_label))
            return
        try:
            subprocess.run(
                cmd,
                check=True,
                env={**os.environ, "PULP_CONTENT_ORIGIN": "NONE"},
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"uv run failed (exit {e.returncode}): {' '.join(cmd)}") from e
