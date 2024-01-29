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

import os
import typing as t
from pathlib import Path

from pulp_docs.repository import Repos

ADMIN_NAME = "admin"
USER_NAME = "user"

DISPLAY_NAMES = {
    "guides": "How-to Guides",
    "learn": "Learn More",
    "tutorials": "Tutorials",
    "reference": "Reference",
}
GUIDES = DISPLAY_NAMES["guides"]
LEARN = DISPLAY_NAMES["learn"]
TUTORIALS = DISPLAY_NAMES["tutorials"]


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
            {repos}/
                {content-type}
    """
    f = AgregationUtils(tmpdir, repos)
    # Aggregation and Grouping
    help_section = [
        {"Overview": f.section_file("help/index.md")},
        {
            "Bugs, Feature and Backport Requests": f.section_file(
                "help/bugs-features.md"
            )
        },
    ]
    # pulpcore_tutorial
    usage_section = [
        {"Overview": f.section_file("usage/index.md")},
        {
            "Getting Started": [
                f.section(
                    "Intro Tutorial", f.get_children, "pulpcore/docs/user/tutorials"
                ),
                f.section(LEARN, f.get_children, "pulpcore/docs/user/learn"),
                f.section(GUIDES, f.get_children, "pulpcore/docs/user/guides"),
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
            "Getting Started": [
                f.section(
                    "Intro Tutorial", f.get_children, "pulpcore/docs/admin/tutorials"
                ),
                f.section(LEARN, f.get_children, "pulpcore/docs/admin/learn"),
                f.section(GUIDES, f.get_children, "pulpcore/docs/admin/guides"),
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
            "Getting Started": [
                f.section("Quickstarts", f.get_children, "pulpcore/docs/dev/tutorials"),
                f.section(LEARN, f.get_children, "pulpcore/docs/dev/learn"),
                f.section(GUIDES, f.get_children, "pulpcore/docs/dev/guides"),
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


class AgregationUtils:
    def __init__(self, tmpdir: Path, repos: Repos):
        self.tmpdir = tmpdir
        self.repos = repos

    def section(self, name: str, fn: t.Callable, *args, **kwargs) -> dict:
        """
        Create section with @name by calling the @fn aggregation function.

        A section look like {"Name": [file1, file2, ...]}

        Params:
            hide_empty_section: Hide section if @fn return is empty. Default=True
        """
        hide_empty_section = kwargs.pop("hide_empty_section", False)
        section = fn(*args, **kwargs)
        if hide_empty_section is False:
            return {name: section}
        return {name: section} if section else {"": ""}

    def get_children(self, path: t.Union[str, Path]) -> list[str]:
        """
        Get all markdown files contained in @path recursively.

        Uses the dirname.title() as the subsection name if there are subdirs.
        """
        basepath = self.tmpdir / path if isinstance(path, str) else path
        if not basepath.exists():
            return []

        def _get_tree(_path):
            """Recursive scandir"""
            with os.scandir(_path) as it:
                children = []
                for entry in sorted(it, key=lambda x: x.name):
                    if entry.is_file() and entry.name.endswith(".md"):
                        filename = str(Path(entry.path).relative_to(self.tmpdir))
                        children.append(filename)
                    elif entry.is_dir():
                        sub_section = {entry.name.title(): _get_tree(entry)}
                        children.append(sub_section)
            return children

        result = _get_tree(basepath)
        return result

    def repo_grouping(
        self,
        template_str: str,
        repo_types: t.Optional[list[str]] = None,
        content_types: t.Optional[list[str]] = None,
    ):
        """
        Get all markdown files that matches @template_str basepath and group by repos.

        Arguments:
            template_str: The template with fields to expand. Accepts combination of '{repo}' and '{content}'
            repos: The set of repos to use. Accepts list with combination of "core", "content" and "other"
            content_types: The set of content-types to use. Accepts combination of "guides", "learn" and "tutorial"

        Example:
            ```python
            >>> repo_grouping("{repo}/docs/dev/guides")
            {
                "repoA": ["docs/dev/guides/file1.md", "docs/dev/guides/file2.md"],
                "repoB": ["docs/dev/guides/file3.md", "docs/dev/guides/file4.md"],
            }
            >>> repo_grouping("{repo}/docs/dev/{content}", content=["guide", "learn"])
            {
                "repoA": [
                    {"How-to": ["docs/dev/guides/file1.md", "docs/dev/guides/file2.md"]},
                    {"Learn": ["docs/dev/learn/file1.md", "docs/dev/learn/file2.md"]},
                ],
                "repoB": [...]

            }
            ```
        """
        _nav = {}
        _expand_content_types = "{content}" in template_str

        # Selected  a set of repos
        selected_repos = []
        selected_content = content_types or ["tutorials", "guides", "learn"]
        if not repo_types:  # default case
            selected_repos = self.repos.all
        else:
            for repo_name in repo_types:
                selected_repos.extend(getattr(self.repos, f"{repo_name}_repos"))

        # Dont expand content-types
        if not _expand_content_types:
            for repo in selected_repos:
                lookup_path = self.tmpdir / template_str.format(
                    repo=repo.name, admin=ADMIN_NAME, user=USER_NAME
                )
                _repo_content = self.get_children(lookup_path)
                if _repo_content:
                    _nav[repo.title] = _repo_content
        # Expand content-types
        else:
            for repo in selected_repos:
                repo_nav = {}
                for content_type in selected_content:
                    lookup_path = self.tmpdir / template_str.format(
                        repo=repo.name,
                        admin=ADMIN_NAME,
                        user=USER_NAME,
                        content=content_type,
                    )
                    _repo_content = self.get_children(lookup_path)

                    # special treatment to quickstart tutorial
                    quickstart_file = self._pop_quickstart_from(_repo_content)
                    if content_type.lower() == "tutorials" and quickstart_file:
                        repo_nav["Quickstart"] = quickstart_file  # type: ignore

                    # doesnt render content-type section if no files inside
                    if _repo_content:
                        content_type_name = DISPLAY_NAMES[content_type]
                        repo_nav[content_type_name] = _repo_content  # type: ignore
                if repo_nav:
                    _nav[repo.title] = repo_nav
        return _nav

    def _pop_quickstart_from(self, pathlist: list[str]) -> t.Optional[str]:
        """Get quickstart.md file from filelist with case and variations tolerance"""
        for path in pathlist:
            filename = path.split("/")[-1]
            if filename.lower() in ("quickstart.md", "quick-start.md"):
                pathlist.remove(path)
                return path
        return None

    def repo_reference_grouping(self):
        """
        Create reference section by aggregating some specific files.

        Group according to the pattern:
        {repo}/
            Readme.md
            Rest Api.md
            Code Api/
                Module A.md
                Module B.md
            Changelog.md

        """
        template_str = "{repo}/docs/reference"
        _nav = {}
        for repo in self.repos.all:
            lookup_path = self.tmpdir / template_str.format(repo=repo.name)
            _repo_content = self.get_children(lookup_path)
            reference_section = [
                {"REST API": f"{repo.name}/docs/rest_api.md"},
                {"Readme": f"{repo.name}/README.md"},
                {"Code API": _repo_content},
                {"Changelog": f"{repo.name}/CHANGELOG.md"},
            ]
            _nav[repo.title] = reference_section
        return _nav

    def section_file(self, section_and_filename: str):
        """Get a markdown file from the website section folder."""
        basepath = "pulpcore/docs/sections"
        return f"{basepath}/{section_and_filename}"

    def section_children(self, section_name: str):
        """Get children markdown files from the website section folder."""
        basepath = "pulpcore/docs/sections"
        section = self.get_children(f"{basepath}/{section_name}")
        return section
