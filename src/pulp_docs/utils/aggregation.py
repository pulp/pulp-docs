import os
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

    def get_children(self, path: t.Union[str, Path]) -> t.List[str]:
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
        repo_types: t.Optional[t.List[str]] = None,
        content_types: t.Optional[t.List[str]] = None,
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
            selected_repos.extend(self.repos.get_repos(repo_types=repo_types))

        # Dont expand content-types
        if not _expand_content_types:
            for repo in selected_repos:
                lookup_path = self.tmpdir / template_str.format(
                    repo=repo.name, admin=Names.ADMIN, user=Names.USER
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
                        admin=Names.ADMIN,
                        user=Names.USER,
                        content=content_type,
                    )
                    _repo_content = self.get_children(lookup_path)

                    # special treatment to quickstart tutorial
                    if content_type.lower() == "tutorials":
                        quickstart_file = self._pop_quickstart_from(_repo_content)
                        if quickstart_file:
                            repo_nav["Quickstart"] = quickstart_file  # type: ignore

                    # doesnt render content-type section if no files inside
                    if _repo_content:
                        content_type_name = Names.get(content_type)
                        repo_nav[content_type_name] = _repo_content  # type: ignore
                if repo_nav:
                    _nav[repo.title] = repo_nav
        return _nav or ["#"]

    def _pop_quickstart_from(self, pathlist: t.List[str]) -> t.Optional[str]:
        """Get quickstart.md file from filelist with case and variations tolerance"""
        for path in pathlist:
            if not isinstance(path, str):
                continue

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
