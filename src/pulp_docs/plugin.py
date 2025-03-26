import typing as t
from pathlib import Path
import json
import tomllib
import yaml

import httpx
from git import Repo
from mkdocs.config import Config, config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import event_priority, get_plugin_logger, BasePlugin
from mkdocs.structure.files import File, Files
from mkdocs.structure.nav import Navigation, Section
from mkdocs.structure.pages import Page
from mkdocs.utils.templates import TemplateContext

log = get_plugin_logger(__name__)

REST_API_MD = """\
---
template: "rest_api.html"
---
"""


@config_options.SubConfig
class RepositoryOption(Config):
    title = config_options.Type(str)
    path = config_options.Type(str)
    kind = config_options.Type(str)
    git_url = config_options.Type(str, default="")
    rest_api = config_options.Type(str, default="")


class PulpDocsPluginConfig(Config):
    repositories = config_options.ListOfItems(RepositoryOption, default=[])


def _add_to_taxonomy_nav(
    src_uri: Path,
    taxonomy_nav: list[t.Any],
) -> bool:
    if src_uri.parts[3] == "tutorials":
        taxonomy_nav[0]["Tutorials"].append(str(src_uri))
    elif src_uri.parts[3] == "guides":
        taxonomy_nav[1]["How-to Guides"].append(str(src_uri))
    elif src_uri.parts[3] == "learn":
        taxonomy_nav[2]["Learn More"].append(str(src_uri))
    elif src_uri.parts[3] == "reference":
        taxonomy_nav[3]["Reference"].append(str(src_uri))
    else:
        log.info(f"Could not navigate {src_uri}.")
        return False
    return True


class RepositoryNav:
    def __init__(self, config: MkDocsConfig, repository_slug: Path):
        self._nav_file_name: str = config.plugins["literate-nav"].config.nav_file
        self._repository_slug = repository_slug

        self._user_index_uri: Path = repository_slug / "index.md"
        self._user_index_found: bool = False
        self._user_uris: list[Path] = []
        self._admin_uris: list[Path] = []

        self._dev_index_uri: Path = repository_slug / "docs" / "dev" / "index.md"
        self._dev_index_found: bool = False
        self._dev_uris: list[Path] = []

        self._extra_uris: list[Path] = []

    def add(self, src_uri: Path) -> None:
        # TODO Find and do something about the _SUMMARY.md files.
        assert src_uri.parts[0] == str(self._repository_slug)
        if src_uri.suffix == ".md" and not src_uri.name == self._nav_file_name:
            if src_uri == self._user_index_uri:
                self._user_index_found = True
            elif src_uri == self._dev_index_uri:
                self._dev_index_found = True
            elif len(src_uri.parts) == 2:
                self._extra_uris.append(src_uri)
            elif src_uri.parts[2] == "user":
                self._user_uris.append(src_uri)
            elif src_uri.parts[2] == "admin":
                self._admin_uris.append(src_uri)
            elif src_uri.parts[2] == "dev":
                self._dev_uris.append(src_uri)

    def user_nav(self) -> list[t.Any]:
        result: list[t.Any] = []
        if len(self._user_uris) + len(self._admin_uris) > 0 or self._user_index_found:
            result.append(str(self._user_index_uri))
            user_nav: list[t.Any] = [
                {"Tutorials": []},
                {"How-to Guides": []},
                {"Learn More": []},
                {"Reference": []},
            ]
            for src_uri in self._user_uris:
                # TODO filter for literate nav
                _add_to_taxonomy_nav(src_uri, user_nav)
            result.append({"Usage": user_nav})

            admin_nav: list[t.Any] = [
                {"Tutorials": []},
                {"How-to Guides": []},
                {"Learn More": []},
                {"Reference": []},
            ]
            for src_uri in self._admin_uris:
                # TODO filter for literate nav
                _add_to_taxonomy_nav(src_uri, admin_nav)
            result.append({"Administration": admin_nav})
            result.extend(str(uri) for uri in self._extra_uris)

        return result

    def dev_nav(self) -> list[t.Any]:
        result: list[t.Any] = []
        if len(self._dev_uris) > 0 or self._dev_index_found:
            result = [
                str(self._dev_index_uri),
                {"Tutorials": []},
                {"How-to Guides": []},
                {"Learn More": []},
                {"Reference": []},
            ]
            for src_uri in self._dev_uris:
                # TODO filter for literate nav
                _add_to_taxonomy_nav(src_uri, result[1:])
        return result

    def missing_indices(self) -> t.Iterator[Path]:
        if (
            not self._user_index_found
            and len(self._user_uris) + len(self._admin_uris) > 0
        ):
            yield self._user_index_uri

        if not self._dev_index_found and len(self._dev_uris) > 0:
            yield self._dev_index_uri


def _render_sitemap(section: Section) -> str:
    return "<ul>" + _render_sitemap_item(section) + "</ul>"


def _render_sitemap_item(nav_item: Page | Section) -> str:
    if isinstance(nav_item, Page):
        return f'<li><a href="{nav_item.abs_url}">{nav_item.title}</a></li>'
    elif isinstance(nav_item, Section):
        if nav_item.children:
            title: str = nav_item.title
            children: str = ""
            for item in nav_item.children:
                if isinstance(item, Page) and item.is_index:
                    title = f'<a href="{item.abs_url}">{title or item.title}</a>'
                else:
                    children += _render_sitemap_item(item)
            return f"<li>{title}<ul>{children}</ul></li>"
        else:
            return ""
    else:
        raise NotImplementedError(f"Unknown nav item {nav_item}")


# jinja2 macros and helpers


def repository_data(
    repository: RepositoryOption,
    repository_dir: Path,
) -> dict[str, str | list[str]]:
    """Generate data for rendering md templates."""
    path = repository_dir.name

    version = "unknown"
    try:
        pyproject = repository_dir / "pyproject.toml"
        version = tomllib.loads(pyproject.read_text())["project"]["version"]
    except Exception:
        pass
    github_org = "pulp"
    try:
        template_config = repository_dir / "template_config.yml"
        github_org = yaml.safe_load(template_config.read_text())["github_org"]
    except Exception:
        pass

    links = []
    if repository.rest_api:
        links.append(f"[REST API](site:{path}/restapi/)")
    links.append(f"[Repository](https://github.com/{github_org}/{path})")
    if (repository_dir / "CHANGES.md").exists():
        links.append(f"[Changelog](site:{path}/changes/)")

    return {
        "title": f"[{repository.title}](site:{path}/)",
        "kind": repository.kind,
        "version": version,
        "links": links,
    }


def rss_items() -> list:
    return []
    # that's Himdel's rss feed: https://github.com/himdel
    # TODO move this fetching to js.
    response = httpx.get("https://himdel.eu/feed/pulp-changes.json")
    if response.is_error:
        return [
            {
                "url": "#",
                "title": "Could not fetch the feed. Please, open an issue in https://github.com/pulp/pulp-docs/.",
            }
        ]

    rss_feed = json.loads(response.content)
    return rss_feed["items"][:20]


class PulpDocsPlugin(BasePlugin[PulpDocsPluginConfig]):
    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:
        # Two directories up from docs is where we expect all the other repositories.
        self.repositories_dir = Path(config.docs_dir).parent.parent

        mkdocstrings_config = config.plugins["mkdocstrings"].config
        repositories_var = []
        for repository in self.config.repositories:
            repository_dir = self.repositories_dir / repository.path
            repositories_var.append(repository_data(repository, repository_dir))
            config.watch.append(str(repository_dir / "docs"))
            mkdocstrings_config.handlers["python"]["paths"].append(str(repository_dir))

        macros_plugin = config.plugins["macros"]
        macros_plugin.register_macros({"rss_items": rss_items})
        macros_plugin.register_variables({"repositories": repositories_var})

        return config

    def on_files(self, files: Files, /, *, config: MkDocsConfig) -> Files | None:
        log.info(f"Loading Pulp repositories: {self.config.repositories}")

        pulp_docs_git_repository = Repo(".")
        user_nav: dict[str, t.Any] = {}
        dev_nav: dict[str, t.Any] = {}
        for repository in self.config.repositories:
            log.info(f"Fetching docs from '{repository.title}'")

            repository_dir = self.repositories_dir / repository.path
            git_repository_dir = self.repositories_dir / Path(repository.path).parts[0]
            git_branch = Repo(git_repository_dir).active_branch.name
            repository_parent_dir = repository_dir.parent
            repository_docs_dir = repository_dir / "staging_docs"
            if repository_docs_dir.exists():
                log.warn(
                    f"Found deprecated 'staging_docs' directory in {repository.path}."
                )
            else:
                repository_docs_dir = repository_dir / "docs"
            repository_slug = Path(repository_dir.name)
            assert repository_docs_dir.exists()

            repository_nav = RepositoryNav(config, repository_slug)

            for dirpath, dirnames, filenames in repository_docs_dir.walk(
                follow_symlinks=True
            ):
                for filename in filenames:
                    abs_src_path = dirpath / filename
                    pulp_meta: dict[str, t.Any] = {}
                    if abs_src_path == repository_docs_dir / "index.md":
                        src_uri = repository_slug / "index.md"
                        pulp_meta["index"] = True
                    elif abs_src_path == repository_docs_dir / "dev" / "index.md":
                        src_uri = repository_slug / "docs" / "dev" / "index.md"
                        pulp_meta["index"] = True
                    else:
                        src_uri = abs_src_path.relative_to(repository_parent_dir)
                    log.debug(f"Adding {abs_src_path} as {src_uri}.")
                    if repository.git_url:
                        git_relpath = abs_src_path.relative_to(git_repository_dir)
                        pulp_meta["edit_url"] = (
                            f"{repository.git_url}/edit/{git_branch}/{git_relpath}"
                        )
                    new_file = File.generated(
                        config, src_uri, abs_src_path=abs_src_path
                    )
                    new_file.pulp_meta = pulp_meta
                    files.append(new_file)
                    repository_nav.add(src_uri)

            for src_uri in repository_nav.missing_indices():
                new_file = File.generated(
                    config,
                    src_uri,
                    content=f"# Welcome to {repository.title}\n\nThis is a generated page. "
                    "See how to add a custom overview page for your plugin "
                    "[here](site:pulp-docs/docs/dev/guides/create-plugin-overviews/).",
                )
                new_file.pulp_meta = {"index": True}
                files.append(new_file)

            if repository.rest_api:
                src_uri = repository_slug / "restapi.md"
                files.append(
                    File.generated(
                        config,
                        src_uri,
                        content=REST_API_MD,
                    )
                )
                repository_nav.add(src_uri)
                api_json = pulp_docs_git_repository.git.show(
                    f"docs-data:data/openapi_json/{repository.rest_api}-api.json"
                )
                src_uri = (repository_dir / "api.json").relative_to(
                    repository_parent_dir
                )
                files.append(File.generated(config, src_uri, content=api_json))

            repository_changes = repository_dir / "CHANGES.md"
            if repository_changes.exists():
                src_uri = repository_slug / "changes.md"
                files.append(
                    File.generated(config, src_uri, abs_src_path=repository_changes)
                )
                repository_nav.add(src_uri)

            user_nav.setdefault(repository.kind, []).append(
                {repository.title: repository_nav.user_nav()}
            )
            dev_nav.setdefault(repository.kind, []).append(
                {repository.title: repository_nav.dev_nav()}
            )

        config.nav[1]["User Manual"].extend(
            [{key: value} for key, value in user_nav.items()]
        )
        config.nav[2]["Developer Manual"].extend(
            [{key: value} for key, value in dev_nav.items()]
        )
        return files

    def on_page_context(
        self,
        context: TemplateContext,
        page: Page,
        config: MkDocsConfig,
        nav: Navigation,
    ) -> TemplateContext:
        pulp_meta = getattr(page.file, "pulp_meta", {})
        if pulp_meta.get("index"):
            toc = (
                "<ul>"
                + "".join((f"<li>{item.title}</li>" for item in page.parent.children))
                + "</li>"
            )
            toc = '<div class="pulp-sitemap">' + _render_sitemap(page.parent) + "</div>"
            page.content = page.content.replace("PULP_SITEMAP", toc)

        # TODO adjust the repository link to the current plugin.
        return context

    def on_page_markdown(
        self,
        markdown: str,
        page: Page,
        config: MkDocsConfig,
        files: Files,
    ) -> str:
        pulp_meta = getattr(page.file, "pulp_meta", {})
        if pulp_meta.get("index"):
            markdown += "\n\n---\n\n## Site Map\n\nPULP_SITEMAP"
        return markdown

    def on_pre_page(
        self,
        page: Page,
        config: MkDocsConfig,
        files: Files,
    ) -> Page | None:
        pulp_meta = getattr(page.file, "pulp_meta", {})
        if edit_url := pulp_meta.get("edit_url"):
            page.edit_url = edit_url
        return page
