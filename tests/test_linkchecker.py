from textwrap import dedent
from typing import NamedTuple

import pytest

from linkchecker.cli import HEADER_ERROR, extract_links, linkchecker

from .conftest import scenario_ids


class Scenario(NamedTuple):
    name: str
    tree: str
    component_dir: str
    exit_code: int
    output: str


class LinkExtractionCase(NamedTuple):
    name: str
    line: str
    expected_links: list[str]


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


class TestExtractLinks:
    not_found_cases = [
        LinkExtractionCase(
            name="empty_line",
            line="",
            expected_links=[],
        ),
        LinkExtractionCase(
            name="no_links",
            line="Plain text with no links",
            expected_links=[],
        ),
        LinkExtractionCase(
            name="link_without_site_prefix",
            line="[text](A/docs/foo)",
            expected_links=[],
        ),
        LinkExtractionCase(
            name="http_link_ignored",
            line="[text](http://example.com)",
            expected_links=[],
        ),
        LinkExtractionCase(
            name="https_link_ignored",
            line="[text](https://example.com)",
            expected_links=[],
        ),
        LinkExtractionCase(
            name="reference_without_site_prefix",
            line="[ref]: A/docs/foo",
            expected_links=[],
        ),
        LinkExtractionCase(
            name="reference_http_link_ignored",
            line="[ref]: http://example.com",
            expected_links=[],
        ),
    ]

    success_cases = [
        LinkExtractionCase(
            name="single_inline_link",
            line="[text](site:A/docs/foo)",
            expected_links=["site:A/docs/foo"],
        ),
        LinkExtractionCase(
            name="single_reference_link",
            line="[ref]: site:A/docs/foo",
            expected_links=["site:A/docs/foo"],
        ),
        LinkExtractionCase(
            name="multiple_inline_links",
            line="[link1](site:A/docs/foo) and [link2](site:B/docs/bar)",
            expected_links=["site:A/docs/foo", "site:B/docs/bar"],
        ),
        LinkExtractionCase(
            name="mixed_inline_and_reference",
            line="[inline](site:A/docs/foo) and [ref]: site:B/docs/bar",
            expected_links=["site:A/docs/foo", "site:B/docs/bar"],
        ),
        LinkExtractionCase(
            name="link_with_hash",
            line="[link](site:A/docs/foo#section)",
            expected_links=["site:A/docs/foo#section"],
        ),
        LinkExtractionCase(
            name="link_with_hash_and_hyphen",
            line="[link](site:A/docs/foo#section-1)",
            expected_links=["site:A/docs/foo#section-1"],
        ),
        LinkExtractionCase(
            name="empty_link_text",
            line="[](site:A/docs/foo)",
            expected_links=["site:A/docs/foo"],
        ),
        LinkExtractionCase(
            name="link_with_trailing_slash",
            line="[text](site:A/docs/foo/)",
            expected_links=["site:A/docs/foo/"],
        ),
        LinkExtractionCase(
            name="link_with_surrounding_text",
            line="Text before [link](site:A/docs/foo) text after",
            expected_links=["site:A/docs/foo"],
        ),
        LinkExtractionCase(
            name="link_with_multiple_path_segments",
            line="[link](site:A/docs/guides/installation)",
            expected_links=["site:A/docs/guides/installation"],
        ),
        LinkExtractionCase(
            name="reference_with_extra_spaces",
            line="[ref]:   site:A/docs/foo",
            expected_links=["site:A/docs/foo"],
        ),
        LinkExtractionCase(
            name="link_text_with_spaces",
            line="[link text with spaces](site:A/docs/foo)",
            expected_links=["site:A/docs/foo"],
        ),
        LinkExtractionCase(
            name="duplicate_links",
            line="[link](site:A/docs/foo) [link](site:A/docs/foo)",
            expected_links=["site:A/docs/foo", "site:A/docs/foo"],
        ),
        LinkExtractionCase(
            name="empty_path_after_site",
            line="[text](site:)",
            expected_links=["site:"],
        ),
        LinkExtractionCase(
            name="link_with_hyphens_and_underscores",
            line="[link](site:A/docs/foo-bar_baz)",
            expected_links=["site:A/docs/foo-bar_baz"],
        ),
    ]

    @pytest.mark.parametrize("case", not_found_cases, ids=scenario_ids(not_found_cases))
    def test_doesnt_return_links(self, case: LinkExtractionCase):
        """Test extract_links returns empty list when no site: links are present."""
        assert extract_links(case.line) == []

    @pytest.mark.parametrize("case", success_cases, ids=scenario_ids(success_cases))
    def test_return_links(self, case: LinkExtractionCase):
        """Test extract_links correctly extracts site: links."""
        assert extract_links(case.line) == case.expected_links
