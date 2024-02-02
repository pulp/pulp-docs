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
    help_section = [
        {"Overview": f.section_file("help/index.md")},
        {
            "Bugs, Feature and Backport Requests": f.section_file(
                "help/bugs-features.md"
            )
        },
    ]
    usage_section = [
        {"Overview": f.section_file("usage/index.md")},
        {
            "Pulpcore": [
                f.section(
                    Names.PULPCORE_TUTORIAL,
                    f.get_children,
                    "pulpcore/docs/user/tutorials",
                ),
                f.section(Names.LEARN, f.get_children, "pulpcore/docs/user/learn"),
                f.section(Names.GUIDES, f.get_children, "pulpcore/docs/user/guides"),
            ]
        },
        {
            "Plugins": f.repo_grouping(
                "{repo}/docs/user/{content}", repo_types=["content"]
            )
        },
        {"Extras": f.repo_grouping("{repo}/docs/user/{content}", repo_types=["other"])},
    ]
    admin_section = [
        {"Overview": f.section_file("admin/index.md")},
        {
            "Pulpcore": [
                f.section(
                    Names.PULPCORE_TUTORIAL,
                    f.get_children,
                    "pulpcore/docs/admin/tutorials",
                ),
                f.section(Names.LEARN, f.get_children, "pulpcore/docs/admin/learn"),
                f.section(Names.GUIDES, f.get_children, "pulpcore/docs/admin/guides"),
            ]
        },
        f.section(
            "Plugins",
            f.repo_grouping,
            "{repo}/docs/admin/{content}",
            repo_types=["content"],
            hide_empty_section=False,
        ),
        f.section(
            "Extras",
            f.repo_grouping,
            "{repo}/docs/admin/{content}",
            repo_types=["other"],
            hide_empty_section=False,
        ),
    ]
    development_section = [
        {"Overview": f.section_file("development/index.md")},
        {
            "Pulpcore": [
                f.section(
                    Names.PULPCORE_TUTORIAL,
                    f.get_children,
                    "pulpcore/docs/dev/tutorials",
                ),
                f.section(Names.LEARN, f.get_children, "pulpcore/docs/dev/learn"),
                f.section(Names.GUIDES, f.get_children, "pulpcore/docs/dev/guides"),
            ]
        },
        {
            "Plugins": f.repo_grouping(
                "{repo}/docs/dev/{content}", repo_types=["content"]
            )
        },
        {"Extras": f.repo_grouping("{repo}/docs/dev/{content}", repo_types=["other"])},
    ]
    reference_section = [
        {"Overview": f.section_file("reference/index.md")},
        {"Repository Map": f.section_file("reference/01-repository-map.md")},
        {"Glossary": f.section_file("reference/02-glossary.md")},
        {"Repositories": f.repo_reference_grouping()},
    ]

    # Main Section
    navigation = [
        {"Home": "index.md"},
        {"User Manual": usage_section},
        {"Admin Manual": admin_section},
        {"Development": development_section},
        {"Reference": reference_section},
        {"Help": help_section},
    ]
    return navigation
