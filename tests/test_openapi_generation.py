import json
import shutil

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

    def test_two_generators_have_unique_container_names(self, tmp_path, repositories):
        plugins = list(repositories.values())[:1]
        gen1 = OpenAPIGenerator(plugins, dry_run=True)
        gen2 = OpenAPIGenerator(plugins, dry_run=True)
        container1 = gen1._init_container(tmp_path)
        container2 = gen2._init_container(tmp_path)
        assert container1.name != container2.name

    def test_podman_not_found(self, monkeypatch, repositories: dict[str, OpenApiPlugin]):
        monkeypatch.setattr(shutil, "which", lambda _: None)
        core_plugin = repositories["pulpcore"]
        gen = OpenAPIGenerator([core_plugin])
        with pytest.raises(RuntimeError, match="podman is required"):
            gen.generate()

    @pytest.mark.parametrize(
        "filter",
        [
            pytest.param(None, id="all"),
            pytest.param(["pulp_rpm", "pulp_container", "pulp_python"], id="partial"),
        ],
    )
    def test_generate(self, repositories: dict[str, OpenApiPlugin], filter):
        """Generate schemas for plugins (all or filtered subset)."""
        if filter is None:
            plugins = list(repositories.values())
        else:
            plugins = [repositories[name] for name in filter if name in repositories]

        generator = OpenAPIGenerator(plugins)
        result = generator.generate()

        assert len(result) == len(plugins)
        for plugin in plugins:
            schema_file = result[plugin.plugin_label]
            assert schema_file.exists()

            content = json.loads(schema_file.read_text())
            assert plugin.plugin_label in content["info"]["x-pulp-app-versions"]
