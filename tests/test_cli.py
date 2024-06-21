import os
import shutil
from pathlib import Path

import pytest
import subprocess
from click.testing import CliRunner

from pulp_docs.cli import main


def test_trivial():
    runner = CliRunner()
    result = runner.invoke(main)
    assert result.exit_code == 0


@pytest.mark.skip("TODO: rewrite this test")
def test_build(tmp_path):
    """Sanity check build cmd"""
    # setup folder structure so test uses local fixtures
    fixture_path = Path("tests/fixtures").absolute()
    dest_path = tmp_path / "workdir"
    shutil.copytree(fixture_path, dest_path)
    for dir in os.scandir(dest_path):
        subprocess.run(["git", "-C", str(Path(dir).absolute()), "init"])

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        os.chdir(dest_path / "pulpcore")  # using local checkout depends on cwd
        result = runner.invoke(main, "build", env={"TMPDIR": str(tmp_path.absolute())})
        assert result.exit_code == 0
        assert Path("site").exists()
