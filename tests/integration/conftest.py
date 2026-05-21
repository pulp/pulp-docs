from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from mkdocs.config import load_config

from pulp_docs.plugin import ComponentSpec


class SideNavigation:
    def __init__(self, site_dir: Path):
        self.site_dir = site_dir
        self._soup = BeautifulSoup((site_dir / "index.html").read_text(), "html.parser")

    def section_kinds(self) -> list[str]:
        primary_nav = self._soup.find("nav", class_=lambda c: c and "md-nav--primary" in c)
        user_manual_a = primary_nav.find("a", href="user/")
        user_manual_li = user_manual_a.find_parent("li")
        inner_nav = user_manual_li.find("nav", class_="md-nav")
        section_lis = inner_nav.find("ul", class_="md-nav__list").find_all("li", recursive=False)
        return [
            li.find("label", class_="md-nav__link")
            .find("span", class_="md-ellipsis")
            .get_text(strip=True)
            for li in section_lis
        ]


ROOT = Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def pulpdocs_components() -> list[ComponentSpec]:
    config = load_config(str(ROOT / "mkdocs.yml"))
    return config.plugins["PulpDocs"].config.components


@pytest.fixture(scope="session")
def built_site() -> Path:
    site = ROOT / "site"
    if not site.exists():
        pytest.fail(f"site/ not found at {site}. Run 'make test-integration' to build it.")
    return site


@pytest.fixture(scope="session")
def side_navigation(built_site: Path) -> SideNavigation:
    return SideNavigation(built_site)
