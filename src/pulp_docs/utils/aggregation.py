import os
import re
import typing as t
from pathlib import Path

from pulp_docs.constants import Names
from pulp_docs.repository import Repos


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

    def normalize_title(self, raw_title: str):
        return raw_title.replace("_", " ").title()

    def repo_grouping(
        self,
        template_str: str,
        repo_types: t.Optional[t.List[str]] = None,
        content_types: t.Optional[t.List[str]] = None,
    ):
        """
        Get all markdown files that matches @template_str basepath and group by repos.

        Arguments:
            template_str: The template with fields to expand. Accepts combination of '{repo}' and '{content}'
            repo_types: The set of repos to use. Accepts list with combination of "core", "content" and "other"
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

        selected_content = content_types or [
            "tutorials",
            "guides",
            "learn",
            "reference",
        ]

        selected_repos = self.repos.all
        if repo_types:
            selected_repos = self.repos.get_repos(repo_types=repo_types)

        group_nav = []
        for repo in selected_repos:
            repo_nav = []
            # Include index.md if present in staging_docs/{persona}/index.md
            persona_basepath = self._parse_template_str(
                template_str, repo.name, "placeholder"
            ).parent
            index_path = persona_basepath / "index.md"
            if index_path.exists():
                repo_nav.append({"Overview": str(index_path.relative_to(self.tmpdir))})

            for content_type in selected_content:
                # Get repo files from content-type and persona
                lookup_path = self._parse_template_str(
                    template_str, repo.name, content_type
                )
                _repo_content = self._add_literate_nav_dir(lookup_path)

                # Prevent rendering content-type section if there are no files
                if _repo_content:
                    content_type_title = Names.get(content_type)
                    repo_nav.append({content_type_title: _repo_content})  # type: ignore
            if repo_nav:
                group_nav.append({repo.title: repo_nav})
        return group_nav or ["#"]

    def changes_grouping(
        self, changes_path_template: str, repo_types: t.Optional[t.List[str]] = None
    ):
        selected_repos = self.repos.all
        if repo_types:
            selected_repos = self.repos.get_repos(repo_types=repo_types)

        group_nav = [
            {repo.title: changes_path_template.format(repo=repo.name)}
            for repo in selected_repos
        ]
        return group_nav or ["#"]  # type: ignore

    def _add_literate_nav_dir(self, lookup_path: Path) -> t.Optional[str]:
        """
        Take a path and return a path-str or None.

        The path-str is expanded by mkdocs-literate-nav. E.g:

        For "foo/bar/eggs/", it will:
        1. Try to find "foo/bar/eggs/_SUMMARY.md"
        2. If cant find, generate recursive nav for "foo/bar/eggs"

        If the @lookup_path is non-existent, non-dir or doesnt contain .md, returns None.
        """
        if not lookup_path.exists():
            return None

        if not lookup_path.is_dir():
            return None

        if len(list(lookup_path.rglob("*.md"))) == 0:
            return None

        path_str = str(lookup_path.relative_to(self.tmpdir)) + "/"
        return path_str

    def _parse_template_str(
        self, template_str: str, repo_name: str, content_type: t.Optional[str] = None
    ) -> Path:
        """
        Replace template_str with repo_name and content_type.

        Additionally, normalized {admin} {user} and {dev} names:
        - {repo}/docs/dev/{content}
        - {repo}/docs/{admin}/{content} -> uses constant for {admin}

        TODO: deprecate this method of template string and use dataclasses instead.
        """
        kwargs = {
            "repo": repo_name,
            "admin": Names.ADMIN,
            "user": Names.USER,
        }
        if content_type:
            kwargs["content"] = content_type

        return self.tmpdir / template_str.format(**kwargs)

