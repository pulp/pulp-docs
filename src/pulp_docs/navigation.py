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

    # Manual section for each persona
    TEMPLATE_STR = "{repo}/docs/{persona}/{content}"
    manual_nav = {
        "user": [
            {"Overview": "user/index.md"},
            *f.repo_grouping(TEMPLATE_STR, personas=["user", "admin"]),
        ],
        "dev": [
            {"Overview": "dev/index.md"},
            *f.repo_grouping(TEMPLATE_STR, personas=["dev"]),
        ],
    }

    # Custom help section
    help_section = [
        {"Overview": "help/index.md"},
        {"Community": "help/community/"},
        {"More": "help/more/"},
    ]

    navigation = [
        {"Home": "index.md"},
        {"User Manual": manual_nav["user"]},
        {"Developer Manual": manual_nav["dev"]},
        {"Blog": ["blog/index.md"]},
        {"Help": help_section},
    ]
    return navigation
