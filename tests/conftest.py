import os
import shutil
import subprocess
from pathlib import Path
from textwrap import dedent

import pytest


@pytest.fixture
def create_file(tmp_path: Path):
    def _create_file(filename: str, content: str) -> Path:
        if not filename:
            raise ValueError("filename can't be empty")
        newfile = tmp_path / filename
        newfile.parent.mkdir(parents=True, exist_ok=True)
        newfile.write_text(dedent(content))
        return newfile

    return _create_file


@pytest.fixture
def create_tree(create_file, tmp_path):
    def _create_tree(tree_text: str) -> tuple[Path, list[Path]]:
        files = []
        fragments = dedent(tree_text).split("=== ")
        for fragment in fragments:
            if not fragment.strip():
                continue
            filename, content = fragment.split("\n", maxsplit=1)
            content = content.strip() or f"Placeholder for {filename=}"
            files.append(create_file(filename.strip(), content))
        return tmp_path, files

    return _create_tree


@pytest.fixture
def repository_root() -> Path:
    return Path(__file__).parent.parent.resolve()


@pytest.fixture
def assets_tmpdir(repository_root: Path, tmp_path: Path) -> Path:
    assets_dir = repository_root / "tests" / "assets"
    _assets_tmpdir = tmp_path / "assets"

    def ignore_fn(src, names):
        return [".git"]

    shutil.copytree(assets_dir, _assets_tmpdir, ignore=ignore_fn)
    return _assets_tmpdir.resolve()


@pytest.fixture
def precommit_test(repository_root: Path, assets_tmpdir: Path):
    def git(*args: str):
        if not os.getcwd().startswith("/tmp"):
            RuntimeError("This must be used in a temporary directory.")
        subprocess.check_call(("git",) + args)

    def _precommit_test(hookid: str, fixture: str) -> tuple[int, str, str]:
        component_dir = assets_tmpdir / fixture
        os.chdir(component_dir)
        git("init")
        git("add", ".")
        cmd = ["pre-commit", "try-repo", str(repository_root), hookid, "-a", "-v"]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode, result.stdout.decode(), result.stderr.decode()

    return _precommit_test
