import typing as t
from pathlib import Path

from pulp_docs.repository import Repos


def get_navigation(tmpdir: Path, repos: Repos):
    """The dynamic generated 'nav' section of mkdocs.yml"""

    # {repo}/docs/{persona}/{content-type}/*md
    # {repo}/docs/reference/*md
    def get_children(path: t.Union[str, Path]):
        _path = tmpdir / path if isinstance(path, str) else path
        result = [
            str(file.relative_to(tmpdir))
            for file in _path.glob("*.md")
            if not file.name.startswith("_")
        ]
        return result

    def expand_repos(template_str: str):
        _nav = {}
        for repo in repos.content:
            lookup_path = tmpdir / template_str.format(repo=repo.name)
            _repo_content = get_children(lookup_path)
            _nav[repo.title] = _repo_content
        return _nav

    def expand_reference(template_str: str):
        _nav = {}
        for repo in repos.all:
            lookup_path = tmpdir / template_str.format(repo=repo.name)
            _repo_content = get_children(lookup_path)
            reference_section = [
                {"REST API": f"{repo.name}/docs/rest_api.md"},
                {"Readme": f"{repo.name}/README.md"},
                {"Code API": _repo_content},
                {"Changelog": f"{repo.name}/CHANGELOG.md"},
            ]
            _nav[repo.title] = reference_section
        return _nav

    def from_core(url: str):
        corename = "pulpcore"
        return f"{corename}/{url}"

    getting_started = [
        {"Overview": from_core("docs/sections/getting_started/index.md")},
        {
            "Quickstart": get_children(
                from_core("docs/sections/getting_started/quickstart")
            )
        },
        {
            "Fundamentals": get_children(
                from_core("docs/sections/getting_started/fundamentals")
            )
        },
    ]
    guides = [
        {"Overview": from_core("docs/sections/guides/index.md")},
        {"For Content-Management": expand_repos("{repo}/docs/content-manager/guides")},
        {"For Sys-Admins": expand_repos("{repo}/docs/sys-admin/guides")},
    ]
    learn = [
        {"Overview": from_core("docs/sections/learn/index.md")},
        {"For Content-Management": expand_repos("{repo}/docs/content-manager/learn")},
        {"For Sys-Admins": expand_repos("{repo}/docs/sys-admin/learn")},
    ]
    reference = [
        {"Overview": from_core("docs/sections/reference/index.md")},
        {"Repository Map": from_core("docs/sections/reference/01-repository-map.md")},
        {"Glossary": from_core("docs/sections/reference/02-glossary.md")},
        {"Repositories": expand_reference("{repo}/docs/reference")},
    ]
    development = [
        {"Overview": from_core("docs/sections/development/index.md")},
        {
            "Quickstart": get_children(
                from_core("docs/sections/development/quickstart/")
            )
        },
        {
            "Onboarding": get_children(
                from_core("docs/sections/development/onboarding/")
            )
        },
        {"Guides": get_children("core/docs/sections/development/guides/")},
    ]

    # main navigation
    navigation = [
        {"Home": "index.md"},
        {"Getting Started": getting_started},
        {"Guides": guides},
        {"Learn": learn},
        {"Reference": reference},
        {"Development": development},
    ]
    return navigation
