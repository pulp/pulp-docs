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


def _add_to_repository_nav(
    src_uri: Path,
    repository_user_nav: list[t.Any],
    repository_dev_nav: list[t.Any],
) -> bool:
    if src_uri.suffix == ".md" and not src_uri.stem == "_SUMMARY":
        if src_uri.parts[2] == "user":
            return _add_to_taxonomy_nav(src_uri, repository_user_nav[0]["Usage"])
        elif src_uri.parts[2] == "admin":
            return _add_to_taxonomy_nav(
                src_uri, repository_user_nav[1]["Administration"]
            )
        elif src_uri.parts[2] == "dev":
            return _add_to_taxonomy_nav(src_uri, repository_dev_nav)
    return False


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
            git_repository = Repo(git_repository_dir)
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

            # Tri-state bool: None indicates we don't even want one.
            user_index_found: bool | None = None
            dev_index_found: bool | None = None

            repository_user_nav: list[t.Any] = [
                {
                    "Usage": [
                        {"Tutorials": []},
                        {"How-to Guides": []},
                        {"Learn More": []},
                        {"Reference": []},
                    ]
                },
                {
                    "Administration": [
                        {"Tutorials": []},
                        {"How-to Guides": []},
                        {"Learn More": []},
                        {"Reference": []},
                    ]
                },
            ]
            repository_dev_nav: list[t.Any] = [
                {"Tutorials": []},
                {"How-to Guides": []},
                {"Learn More": []},
                {"Reference": []},
            ]

            # TODO Find and do something about the _SUMMARY.md files.
            for dirpath, dirnames, filenames in repository_docs_dir.walk(
                follow_symlinks=True
            ):
                for filename in filenames:
                    abs_src_path = dirpath / filename
                    pulp_meta: dict[str, t.Any] = {}
                    if abs_src_path == repository_docs_dir / "index.md":
                        src_uri = repository_slug / "index.md"
                        user_index_found = True
                        pulp_meta["index"] = True
                    elif abs_src_path == repository_docs_dir / "dev" / "index.md":
                        src_uri = repository_slug / "docs" / "dev" / "index.md"
                        dev_index_found = True
                        pulp_meta["index"] = True
                    else:
                        src_uri = abs_src_path.relative_to(repository_parent_dir)
                        if _add_to_repository_nav(
                            src_uri, repository_user_nav, repository_dev_nav
                        ):
                            if src_uri.parts[2] in ["user", "admin"]:
                                user_index_found = user_index_found or False
                            elif src_uri.parts[2] == "dev":
                                dev_index_found = dev_index_found or False
                    log.debug(f"Adding {abs_src_path} as {src_uri}.")
                    if repository.git_url:
                        branch = git_repository.active_branch.name
                        git_relpath = abs_src_path.relative_to(git_repository_dir)
                        pulp_meta["edit_url"] = (
                            f"{repository.git_url}/edit/{branch}/{git_relpath}"
                        )
                    new_file = File.generated(
                        config, src_uri, abs_src_path=abs_src_path
                    )
                    new_file.pulp_meta = pulp_meta
                    files.append(new_file)

            for src_uri, index_found, nav_list in [
                (repository_slug / "index.md", user_index_found, repository_user_nav),
                (
                    repository_slug / "docs" / "dev" / "index.md",
                    dev_index_found,
                    repository_dev_nav,
                ),
            ]:
                if index_found is False:  # None means no index needed.
                    new_file = File.generated(
                        config,
                        src_uri,
                        content=f"# Welcome to {repository.title}\n\nThis is a generated page. "
                        "See how to add a custom overview page for your plugin "
                        "[here](site:pulp-docs/docs/dev/guides/create-plugin-overviews/).",
                    )
                    new_file.pulp_meta = {"index": True}
                    files.append(new_file)
                if index_found is not None:
                    nav_list.insert(0, str(src_uri))

            if repository.rest_api:
                src_uri = (repository_dir / "restapi.md").relative_to(
                    repository_parent_dir
                )
                files.append(
                    File.generated(
                        config,
                        src_uri,
                        content=REST_API_MD,
                    )
                )
                repository_user_nav.append(str(src_uri))
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
                repository_user_nav.append(str(src_uri))

            user_nav.setdefault(repository.kind, []).append(
                {repository.title: repository_user_nav}
            )
            dev_nav.setdefault(repository.kind, []).append(
                {repository.title: repository_dev_nav}
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
