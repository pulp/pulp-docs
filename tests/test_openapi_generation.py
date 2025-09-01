import json
from pathlib import Path

from pulp_docs.openapi import main as openapi_main


class TestOpenApiGeneration:
    def test_dry_run(self, tmp_path: Path, monkeypatch):
        output_dir = tmp_path / "openapi"
        plugins_filter = ["pulp_rpm", "pulp_file"]
        openapi_main(output_dir=output_dir, plugins_filter=plugins_filter, dry_run=True)

    def test_sample_generation(self, tmp_path: Path, monkeypatch):
        output_dir = tmp_path / "openapi"
        output_dir.mkdir()
        assert len(list(output_dir.glob("*.json"))) == 0

        with monkeypatch.context() as m:
            m.setenv("TMPDIR", str(tmp_path))
            plugins_filter = ["pulp_rpm", "pulp_file"]
            openapi_main(output_dir=output_dir, plugins_filter=plugins_filter)

        output_paths = [f for f in output_dir.glob("*.json")]
        output_ls = [f.name for f in output_paths]
        output_labels = [f.rpartition("-")[0] for f in output_ls]
        assert len(output_ls) == 3
        assert {"core-api.json", "rpm-api.json", "file-api.json"} == set(output_ls)

        for label, path in zip(output_labels, output_paths):
            openapi_data = json.loads(path.read_text())
            assert label in openapi_data["info"]["x-pulp-app-versions"].keys()
