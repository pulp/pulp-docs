from pathlib import Path
from textwrap import dedent
from typing import Sequence

import pytest


def scenario_ids(cases: Sequence) -> list[str]:
    return [c.name for c in cases]


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
