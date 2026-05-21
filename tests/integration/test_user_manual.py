import pytest

from pulp_docs.plugin import ComponentSpec

from .conftest import SideNavigation


@pytest.mark.integration
def test_section_order_matches_mkdocs_yaml(
    side_navigation: SideNavigation, pulpdocs_components: list[ComponentSpec]
):
    # Expected order of "kinds" is first-seen from the config components list
    seen = {}
    for comp in pulpdocs_components:
        seen.setdefault(comp.kind, None)
    expected_order = list(seen)

    assert side_navigation.section_kinds() == expected_order
