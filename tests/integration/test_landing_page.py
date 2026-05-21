from pathlib import Path

import pytest
from bs4 import BeautifulSoup


def extract_image(site_dir: Path, name: str) -> Path | None:
    soup = BeautifulSoup((site_dir / "index.html").read_text(), "html.parser")
    img = soup.find("img", src=lambda s: s and name in s)
    if img is None:
        return None
    return site_dir / img["src"].lstrip("/")


@pytest.mark.integration
def test_logo_image(built_site):
    logo = extract_image(built_site, "pulp_logo_big.png")
    assert logo is not None, "pulp_logo_big.png not found in landing page"
    assert logo.exists(), f"Logo file missing: {logo}"
