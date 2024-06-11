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
from typing import List

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

    # Manual section for each persona
    TEMPLATE_STR = "{repo}/docs/{persona}/{content}"
    manual_nav = {
        "user": [
            {"Overview": f"{SECTION_HOST}/docs/sections/user/index.md"},
            *f.repo_grouping(TEMPLATE_STR, personas=["user", "admin"])
        ],
        "dev": [
            {"Overview": f"{SECTION_HOST}/docs/sections/dev/index.md"},
            *f.repo_grouping(TEMPLATE_STR, personas=["dev"])
        ],
    }

    # Custom help section
    help_section = [
        {"Overview": f"{SECTION_HOST}/docs/sections/help/index.md"},
        {"Community": f"{SECTION_HOST}/docs/sections/help/community/"},
        {"More": f"{SECTION_HOST}/docs/sections/help/more/"},
    ]

    # Main Section
    # pulpcore_nav = manual_nav["user"][1]["Core"][0]
    # pulpcore_nav = create_repo_toc_index(pulpcore_nav)
    # print(pulpcore_nav)
    # manual_nav["user"][1]["Core"][0] = pulpcore_nav

    navigation = [
        {"Home": "index.md"},
        {"User Manual": manual_nav["user"]},
        {"Developer Manual": manual_nav["dev"]},
        {"Blog": ["pulp-docs/docs/sections/blog/index.md"]},
        {"Help": help_section},
    ]
    return navigation


def create_repo_toc_index(repo_nav: List[dict]):
    """
    TODO: maybe try to leverage site-map

    Create a toc with the format: {tuple-path: file-path}

    Sample input:
        {'Pulp Core': [{'User': [{'Tutorials': 'pulpcore/docs/user/tutorials/'},
                             {'How-to Guides': 'pulpcore/docs/user/guides/'},
                             {'Learn More': 'pulpcore/docs/user/learn/'}]},
                   {'Admin': [{'How-to Guides': 'pulpcore/docs/admin/guides/'},
                              {'Learn More': 'pulpcore/docs/admin/learn/'}]},
                   {'REST API': 'pulpcore/restapi.md'},
                   {'Changelog': 'pulpcore/changes.md'}]}
    """

    def is_nav(item):
        return isinstance(item, list)

    # {dir-path: page-str}
    toc = {}
    path = []

    def recursive_add(nav):
        for name, item in nav.items():
            path.append(name)
            if isinstance(item, list):
                for entry in item:
                    recursive_add(entry)
                    path.pop()
            elif isinstance(item, dict):
                item_name, entry = item.items()
                path.append(item_name)
                recursive_add(entry)
                toc[tuple(path)] = None
                path.pop()
            else:
                toc[tuple(path)] = item

    recursive_add(repo_nav)
    return toc
