from textwrap import dedent
from typing import NamedTuple

import pytest

from linkchecker.cli import HEADER_ERROR, linkchecker


class Scenario(NamedTuple):
    tree: str
    component_dir: str
    exit_code: int
    output: str


COMMON_TREE = """
=== A/docs/guides/foo.md
=== A/docs/reference/bar.md
=== B/docs/guides/foo.md
=== B/docs/reference/bar.md
"""

cases = [
    Scenario(
        tree=f"""
            === A/docs/index.md
            [valid](site:A/docs/guides/foo)
            [valid](site:A/docs/guides/foo.md)

            [valid]: site:A/docs/reference/bar
            [valid]: site:A/docs/reference/bar.md
            {COMMON_TREE}
        """,
        component_dir="A",
        exit_code=0,
        output="",
    ),
    Scenario(
        tree=f"""
            === A/docs/index.md
            [valid](site:A/docs/guides/foo)
            [valid](site:A/docs/reference/bar)
            [invalid](site:A/docs/guides/NOEXIT.md)
            [invalid](site:A/docs/reference/NOEXIT.md)
            {COMMON_TREE}
        """,
        component_dir="A",
        exit_code=0,
        output=f"""
            {HEADER_ERROR}
            docs/index.md:3:[invalid](site:A/docs/guides/NOEXIT.md)
            docs/index.md:4:[invalid](site:A/docs/reference/NOEXIT.md)
        """,
    ),
]


@pytest.mark.parametrize("case", cases)
def test_linkchecker_main(case, create_tree, capsys):
    """Test checking all files in the docs directory."""
    basedir, files = create_tree(case.tree)
    exit_code = linkchecker(str(basedir / case.component_dir), files)
    out, err = capsys.readouterr()
    assert exit_code == case.exit_code
    assert out.strip() == dedent(case.output).strip()
