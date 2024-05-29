"""
The navigation generator module.

Responsible for creating a specific structure out of the available content-types, personas
and repository types. This structure should be compatible with how it would be written
in mkdocs.yml.

`get_navigation` is the entrypoint used for the final render.

```
# yml
- pageA: some-file.md
- some-other-file.md

# python
[
    {"pageA": "/abs/path/to/some-file.md"},
    "/abs/path/to/some-other-file.md",
]
```

Note that you either specify:
1. {title: file.md} -> define title explicitly
2. "/path/to/file.md" -> uses markdown '# title' or the filename, if former isnt present.

"""

from __future__ import annotations

from pathlib import Path

from pulp_docs.constants import Names
from pulp_docs.repository import Repos
from pulp_docs.utils.aggregation import AgregationUtils


def get_navigation(tmpdir: Path, repos: Repos):
    """
    The entrypoint for dynamic 'nav' generation for  mkdocs.

    Replace by another generation function to change how content is structured.
    """
    # NAV_GENERATOR_FUNCTION = grouped_by_content_type
    NAV_GENERATOR_FUNCTION = grouped_by_persona
    return NAV_GENERATOR_FUNCTION(tmpdir, repos)


def grouped_by_persona(tmpdir: Path, repos: Repos):
    """
    A specific nav generator function.

    Organizes content (roughly) with the pattern.
        {persona}/
            Overview/
            {repos-type}/
                {repos}/
                    {content-type}
    """
    f = AgregationUtils(tmpdir, repos)
    SECTION_HOST = "pulp-docs"
    CHANGES_PATH = "{repo}/changes/changelog.md"

    # Manual section for each persona
    manual_nav = {}
    for section in ("user", "admin", "dev"):
        TEMPLATE_STRING = "{repo}/docs/%s/{content}" % section
        section_nav = [
            {"Overview": f"{SECTION_HOST}/docs/sections/{section}/index.md"},
            {"Core": f.repo_grouping(TEMPLATE_STRING, repo_types=["core"])},
            {"Plugins": f.repo_grouping(TEMPLATE_STRING, repo_types=["content"])},
            {"Extras": f.repo_grouping(TEMPLATE_STRING, repo_types=["other"])},
        ]
        manual_nav[section] = section_nav

    # Custom help section
    help_section = [
        {"Overview": f"{SECTION_HOST}/docs/sections/help/index.md"},
        {"Community": f"{SECTION_HOST}/docs/sections/help/community/"},
        {"More": f"{SECTION_HOST}/docs/sections/help/more/"},
        {
            "Changelogs": [
                {"Core": f.changes_grouping(CHANGES_PATH, repo_types=["core"])},
                {"Plugins": f.changes_grouping(CHANGES_PATH, repo_types=["content"])},
                {"Extra": f.changes_grouping(CHANGES_PATH, repo_types=["other"])},
            ]
        },
    ]

    # Main Section
    navigation = [
        {"Home": "index.md"},
        {"User Manual": manual_nav["user"]},
        {"Admin Manual": manual_nav["admin"]},
        {"Developer Manual": manual_nav["dev"]},
        {"Help": help_section},
    ]
    return navigation
