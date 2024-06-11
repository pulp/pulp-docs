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
        personas: t.Optional[t.List[str]] = None,
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

        # Selected Repository, Persona and Content Type
        selected_content = content_types or [
            "tutorials",
            "guides",
            "learn",
            "reference",
        ]

        selected_repo_types = repo_types or self.repos.repo_types
        selected_repo_types = [(name, name.title()) for name in selected_repo_types]

        selected_personas = personas or ("user", "admin", "dev")

        # Create navigation
        main_nav = []
        for repo_type, repo_type_title in selected_repo_types:
            repo_type_nav = []
            for repo in self.repos.get_repos([repo_type]):
                # filter dev_only repos
                if repo.dev_only and personas and "dev" not in personas:
                    continue

                repo_nav = []
                repo_basepath = self.tmpdir / repo.name
                repo_docs_basepath = repo_basepath / "docs"

                persona_section = []
                for persona in selected_personas:
                    persona_nav = []

                    # Include index.md if present in staging_docs/{persona}/index.md
                    persona_basepath = repo_docs_basepath / persona
                    index_path = persona_basepath / "index.md"
                    if index_path.exists():
                        persona_nav.append(
                            {"Overview": str(index_path.relative_to(self.tmpdir))}
                        )

                    # Add content type for a repo/persona (guides,tutorials,etc)
                    for content_type in selected_content:
                        content_basepath = persona_basepath / content_type
                        content_type_literate_nav_path = self.add_literate_nav_dir(
                            content_basepath
                        )

                        if (
                            content_type_literate_nav_path
                        ):  # No content section if there are no files
                            content_type_title = Names.get(content_type)
                            persona_nav.append({content_type_title: content_type_literate_nav_path})  # type: ignore

                    # Add persona_nav to repo nav
                    if persona_nav:
                        persona_title = Names.get(persona)
                        persona_section.append({persona_title: persona_nav})

                # Add persona section to Repo nav
                if len(persona_section) == 1 and "dev" in selected_personas:
                    persona_squashed = [
                        content_nav for content_nav in persona_section[0][Names.DEV]
                    ]
                    persona_section = persona_squashed  # type: ignore
                repo_nav.extend(persona_section)

                # Add changelog and restapi
                if "dev" not in selected_personas:
                    CHANGES_PATH = f"{repo.name}/changes.md"
                    RESTAPI_PATH = f"{repo.name}/restapi.md"
                    if repo.type in ("content", "core"):
                        repo_nav.append({"REST API": RESTAPI_PATH})
                    repo_nav.append({"Changelog": CHANGES_PATH})

                # Add navigation to Repo, if one exsits
                if repo_nav:
                    repo_type_nav.append({repo.title: repo_nav})
            if repo_type_nav:
                main_nav.append({repo_type_title: repo_type_nav})
        return main_nav or ["#"]

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

    def add_literate_nav_dir(self, lookup_path: Path) -> t.Optional[str]:
        """
        Return str-path expandable by literate-nav or None.

        If @lookup_path exists and is a dir, literate-nav can expand it with or without
        a "_SUMMARY.md" file. Otherwise, we return None, so we can ignore this path.
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
