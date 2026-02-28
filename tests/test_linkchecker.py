from textwrap import dedent
from typing import NamedTuple

import pytest

from linkchecker.cli import HEADER_ERROR, linkchecker

from .conftest import scenario_ids


class Scenario(NamedTuple):
    name: str
    tree: str
    component_dir: str
    exit_code: int
    output: str


COMMON_TREE = """
=== A/docs/guides/foo.md
Content from file foo, repository A
=== A/docs/reference/bar.md
Content from file bar, repository A
=== B/docs/guides/foo.md
Content from file foo, repository B
=== B/docs/reference/bar.md
Content from file bar, repository B
"""

cases = [
    Scenario(
        name="valid_links",
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
        name="valid_links_trailing_slash",
        tree=f"""
            === A/docs/index.md
            [valid trailing slash](site:A/docs/guides/foo/)
            [valid ref trailing slash]: site:A/docs/reference/bar/
            {COMMON_TREE}
        """,
        component_dir="A",
        exit_code=0,
        output="",
    ),
    Scenario(
        name="restapi_ignored",
        tree=f"""
            === A/docs/index.md
            [restapi](site:A/restapi/#some-operation)
            [restapi ref]: site:A/restapi/#another-operation
            {COMMON_TREE}
        """,
        component_dir="A",
        exit_code=0,
        output="",
    ),
    Scenario(
        name="missing_files",
        tree=f"""
            === A/docs/index.md
            [valid](site:A/docs/guides/foo)
            [valid](site:A/docs/reference/bar)
            [invalid](site:A/docs/guides/NOEXIT.md)
            [invalid](site:A/docs/reference/NOEXIT.md)
            {COMMON_TREE}
        """,
        component_dir="A",
        exit_code=1,
        output=f"""
            {HEADER_ERROR.format(n=2)}
            docs/index.md:3  site:A/docs/guides/NOEXIT.md
            docs/index.md:4  site:A/docs/reference/NOEXIT.md
        """,
    ),
]


@pytest.mark.parametrize("case", cases, ids=scenario_ids(cases))
def test_linkchecker_main(case: Scenario, create_tree, capsys):
    """Test checking all files in the docs directory."""
    basedir, files = create_tree(case.tree)
    exit_code = linkchecker(str(basedir / case.component_dir), files)
    out, err = capsys.readouterr()
    assert exit_code == case.exit_code
    assert out.strip() == dedent(case.output).strip()
