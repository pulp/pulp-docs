"""
Module for generating open-api json files for selected Pulp plugins.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import NamedTuple


def annotate_api_json(api_json: str) -> str:
    """Append version info from x-pulp-app-versions to the spec description."""
    spec = json.loads(api_json)
    versions = spec.get("info", {}).get("x-pulp-app-versions", {})
    if not versions:
        return api_json
    non_core = [f"pulp_{k} {v}" for k, v in versions.items() if k != "core"]
    core = [f"pulpcore {v}" for k, v in versions.items() if k == "core"]
    # core is secondary: shown in parens when a plugin is present, primary otherwise
    parts = non_core + [f"({c})" for c in core] if non_core else core
    version_string = " ".join(parts)
    existing_desc = spec["info"].get("description", "")
    description = f"{existing_desc}\n\nGenerated from: {version_string}".strip()
    spec["info"]["description"] = description
    return json.dumps(spec, indent=2)


class PulpResolutionError(Exception):
    """Raised when uv cannot resolve plugin dependencies due to incompatibilities."""

    pass


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
        missing = [p.plugin_label for p in plugins if not p.repository_path]
        if missing:
            raise ValueError(f"Plugins missing repository path: {missing}")
        self.label_to_path = {p.plugin_label: p.repository_path for p in plugins}
        self.dry_run = dry_run

    def generate(self) -> dict[str, Path]:
        """Generate openapi json files.

        Returns map of plugin labels to generated spec path.
        """
        if not self.label_to_path:
            return {}
        output_dir = Path(tempfile.mkdtemp())
        label_to_specfile = {}
        for label in self.label_to_path:
            filename = f"{label}-api.json"
            file_path = output_dir / filename
            self._generate_schema(label, file_path)
            label_to_specfile[label] = file_path
        return label_to_specfile

    def _generate_schema(self, plugin_label: str, output_file: Path):
        cmd = ["uv", "run", "--isolated", "--with", "setuptools"]
        repo_path = self.label_to_path[plugin_label]
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
                stderr=subprocess.PIPE,
                env={**os.environ, "PULP_CONTENT_ORIGIN": "NONE"},
            )
            output_file.write_text(annotate_api_json(output_file.read_text()))
        except subprocess.CalledProcessError as e:
            # catch UV resolution error based on their error message
            stderr = e.stderr.decode()
            _, found, message = stderr.partition("╰─▶ ")
            if found:
                message = (
                    "Package resolution error (from uv).\n"
                    "Maybe you want to use `--draft --path <plugin>@<path>` to narrow used plugins?"
                    f"\n\nError message:\n{message.strip()}"
                )
                raise PulpResolutionError(message) from e
            raise RuntimeError(
                f"uv run failed (exit {e.returncode}): {' '.join(cmd)}\n{stderr}"
            ) from e
