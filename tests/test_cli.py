import os
import shutil
from pathlib import Path

import pytest
import subprocess
from click.testing import CliRunner

from pulp_docs.main import main


# @pytest.fixture(scope="session")
# def my_tmp_path(tmp_path_factory):
#     _tmp_path = tmp_path_factory.mktemp("data")
#     breakpoint()
#     shutil.copytree("tests/fixtures", _tmp_path)
#     return tmp_path_factory.getbasetemp()


def test_trivial():
    runner = CliRunner()
    result = runner.invoke(main)
    assert result.exit_code == 0


def test_build(tmp_path):
    """Sanity check build cmd"""
    # setup folder structure so test uses local fixtures
    fixture_path = Path("tests/fixtures/pulpcore").absolute()
    dest_path = tmp_path / "workdir" / fixture_path.name
    shutil.copytree(fixture_path, dest_path)
    subprocess.run(["git", "-C", str(dest_path.absolute()), "init"])

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        os.chdir(dest_path) # using local checkout depends on cwd
        result = runner.invoke(main, "build", env={"TMPDIR": str(tmp_path.absolute())})
        assert result.exit_code == 0
        assert Path("site").exists()
