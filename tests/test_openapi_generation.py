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


class TestOpenAPIGenerator:
    def test_label_to_path_mapping(self, repositories: dict[str, OpenApiPlugin]):
        """Each plugin label maps to its repository path."""
        filter = ["rpm", "file", "core"]
        plugins = [p for p in repositories.values() if p.plugin_label in filter]
        gen = OpenAPIGenerator(plugins, dry_run=True)
        assert len(gen.label_to_path) == len(plugins)
        for plugin in plugins:
            assert gen.label_to_path[plugin.plugin_label] == plugin.repository_path

    @pytest.mark.parametrize(
        "filter",
        [
            pytest.param(None, id="all"),
            pytest.param(["pulp_rpm", "pulp_container", "pulp_python"], id="partial"),
        ],
    )
    def test_generate(self, repositories: dict[str, OpenApiPlugin], filter):
        """Generate dry-run schemas for plugins (all or filtered subset)."""
        EXPECTED_TEMPLATE = OpenAPIGenerator.DRY_RUN_SPECFILE_TEMPLATE
        if filter is None:
            plugins = list(repositories.values())
        else:
            plugins = [repositories[name] for name in filter if name in repositories]

        generator = OpenAPIGenerator(plugins, dry_run=True)
        label_to_specfile = generator.generate()

        assert len(label_to_specfile) == len(plugins)
        for plugin in plugins:
            schema_file = label_to_specfile[plugin.plugin_label]
            expected_content = EXPECTED_TEMPLATE.format(plugin_label=plugin.plugin_label)
            assert schema_file.exists()
            assert schema_file.read_text() == expected_content
