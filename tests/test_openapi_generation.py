import json
import shutil
from pathlib import Path

import pytest

from pulp_docs.cli import fetch_repositories
from pulp_docs.openapi import OpenAPIGenerator, OpenApiPlugin


@pytest.fixture(scope="session")
def repositories(tmp_path_factory: pytest.TempPathFactory) -> dict[str, OpenApiPlugin]:
    """Fetch all component repositories for testing."""
    dest_path = tmp_path_factory.mktemp("repos")
    specs = fetch_repositories(dest_path, fetch_all=True)
    result = {}
    for spec in specs:
        if not spec.rest_api:
            continue
        repo_path = dest_path / spec.repository_name
        if repo_path.exists():
            result[spec.component_name] = OpenApiPlugin(
                repository_path=repo_path, plugin_label=spec.label
            )
    return result


class TestOpenAPIGeneratorClass:
    def test_deduplicate_repository_paths(self, repositories: dict[str, OpenApiPlugin]):
        """pulpcore and pulp_file share the same repository path."""
        filter = ["rpm", "file", "core"]
        plugins = [p for p in repositories.values() if p.plugin_label in filter]
        gen = OpenAPIGenerator(plugins, dry_run=True)
        # pulpcore and pulp_file share the same repository
        assert len(gen.repository_paths) == 2

    def test_podman_not_found(self, tmp_path, monkeypatch, repositories: dict[str, OpenApiPlugin]):
        monkeypatch.setattr(shutil, "which", lambda _: None)
        core_plugin = repositories["pulpcore"]
        gen = OpenAPIGenerator([core_plugin])
        with pytest.raises(RuntimeError, match="podman is required"):
            gen.generate(output_dir=tmp_path)

    @pytest.mark.parametrize(
        "filter",
        [
            pytest.param(None, id="all"),
            pytest.param(["pulp_rpm", "pulp_container", "pulp_python"], id="partial"),
        ],
    )
    def test_generate(self, tmp_path: Path, repositories: dict[str, OpenApiPlugin], filter):
        """Generate schemas for plugins (all or filtered subset)."""
        if filter is None:
            plugins = list(repositories.values())
        else:
            plugins = [repositories[name] for name in filter if name in repositories]

        generator = OpenAPIGenerator(plugins)
        generator.generate(output_dir=tmp_path)
        files = list(tmp_path.glob("*.json"))

        assert len(files) == len(plugins)
        for plugin in plugins:
            schema_file = tmp_path / f"{plugin.plugin_label}-api.json"
            assert schema_file.exists()

            content = json.loads(schema_file.read_text())
            assert plugin.plugin_label in content["info"]["x-pulp-app-versions"]
