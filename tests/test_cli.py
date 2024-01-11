import os
import shutil
from pathlib import Path

import pytest
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
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, "build", env={"TMPDIR": str(tmp_path.absolute())})
        assert result.exit_code == 0
        assert Path("site").exists()
