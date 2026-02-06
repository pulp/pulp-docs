import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from pulp_docs.cli import main
from pulp_docs.openapi import OpenAPIGenerator, OpenApiPlugin, PodmanContainer, get_plugins
from pulp_docs.openapi import main as openapi_main

PODMAN_AVAILABLE = shutil.which("podman") is not None


class TestPodmanContainer:
    def test_dry_run_lifecycle(self, tmp_path, capsys):
        c = PodmanContainer(
            image="myimage",
            volumes={str(tmp_path): "/output"},
            env={"FOO": "BAR"},
            dry_run=True,
        )
        with c.run():
            c.exec("echo", "hello")

        output = capsys.readouterr().out
        assert "podman create" in output
        assert "podman start" in output
        assert "podman exec" in output
        assert "echo hello" in output
        assert "podman rm --force" in output
        assert "FOO=BAR" in output
        assert f"{tmp_path}:/output:Z" in output


class TestGetPlugins:
    def test_no_filter_returns_all_plugins(self):
        all_plugins = get_plugins([])
        assert len(all_plugins) > 0

    def test_filter_returns_subset(self):
        all_plugins = get_plugins([])
        filtered = get_plugins(["pulp_rpm"])
        assert 0 < len(filtered) < len(all_plugins)


class TestOpenAPIGeneratorClass:
    def test_deduplicate_git_urls(self):
        """pulpcore and pulp_file share the same git URL."""
        plugins = [
            OpenApiPlugin(git_url="https://github.com/pulp/pulpcore", plugin_label="core"),
            OpenApiPlugin(git_url="https://github.com/pulp/pulpcore", plugin_label="file"),
            OpenApiPlugin(git_url="https://github.com/pulp/pulp_rpm", plugin_label="rpm"),
        ]
        gen = OpenAPIGenerator(plugins, dry_run=True)
        assert len(gen.git_urls) == 2
        assert "https://github.com/pulp/pulpcore" in gen.git_urls
        assert "https://github.com/pulp/pulp_rpm" in gen.git_urls

    def test_podman_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda x: None)
        gen = OpenAPIGenerator([OpenApiPlugin("https://github.com/pulp/pulpcore", "core")])
        with pytest.raises(RuntimeError, match="podman is required"):
            gen.generate(output_dir=tmp_path)

    def test_generate_core_only(self, tmp_path: Path):
        core = OpenApiPlugin(git_url="https://github.com/pulp/pulpcore", plugin_label="core")
        plugins = [core]
        generator = OpenAPIGenerator(plugins)
        generator.generate(output_dir=tmp_path)
        files = list(tmp_path.iterdir())
        assert len(files) == 1

        spec_file = files[0]
        assert spec_file.name == "core-api.json"

        content = json.loads(spec_file.read_text())
        assert "core" in content["info"]["x-pulp-app-versions"]


class TestOpenapiMainFunction:
    def test_dry_run_commands(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        output_dir = tmp_path / "openapi"
        filter_list = ["pulp_rpm", "pulp_file"]
        exit_code = openapi_main(output_dir=output_dir, filter_list=filter_list, dry_run=True)
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "podman create" in output
        assert "podman start" in output
        assert "podman rm --force" in output

        assert "pip install" in output
        assert "pulpcore-manager openapi --component file" in output
        assert "pulpcore-manager openapi --component rpm" in output
        assert str(output_dir.resolve()) in output

    def test_sample_generation(self, tmp_path: Path):
        output_dir = tmp_path / "openapi"
        output_dir.mkdir()
        assert len(list(output_dir.glob("*.json"))) == 0

        filter_list = ["pulp_rpm", "pulp_file"]
        openapi_main(output_dir=output_dir, filter_list=filter_list)

        output_paths = list(output_dir.glob("*.json"))
        output_ls = [f.name for f in output_paths]
        output_labels = [f.rpartition("-")[0] for f in output_ls]
        assert len(output_ls) == 2
        assert {"rpm-api.json", "file-api.json"} == set(output_ls)

        for label, path in zip(output_labels, output_paths):
            openapi_data = json.loads(path.read_text())
            assert label in openapi_data["info"]["x-pulp-app-versions"].keys()


class TestClickCLI:
    def test_openapi_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["openapi", "--help"])
        assert result.exit_code == 0
        assert "Generate OpenAPI" in result.output
        assert "OUTPUT_DIR" in result.output
