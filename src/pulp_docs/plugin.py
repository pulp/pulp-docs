import json
import sys
import tomllib
import typing as t
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import httpx
import yaml
from git import GitCommandError, Repo
from mkdocs.config import Config, config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure.files import File, Files
from mkdocs.structure.nav import Link, Navigation, Section
from mkdocs.structure.pages import Page
from mkdocs.utils.templates import TemplateContext

from pulp_docs.context import ctx_blog, ctx_docstrings, ctx_draft, ctx_dryrun, ctx_path

log = get_plugin_logger(__name__)

REST_API_MD = """\
---
template: "rest_api.html"
---

# Rest API - {component} {{.hide-h1}}
"""

MISSING_INDEX_TEMPLATE = """\
# Welcome to {component.title}

This is a generated page. See how to add a custom overview page for your plugin
[here](site:pulp-docs/docs/dev/guides/create-plugin-overviews/).
"""


@config_options.SubConfig
class ComponentOption(Config):
    title = config_options.Type(str)
    path = config_options.Type(str)
    kind = config_options.Type(str)
    git_url = config_options.Type(str, default="")
    rest_api = config_options.Type(str, default="")

    @property
    def name(self) -> str:
        return self.path.rpartition("/")[-1]

    @property
    def label(self) -> str:
        return self.rest_api


@dataclass(frozen=True)
class Component:
    title: str
    path: str
    kind: str
    git_url: str
    rest_api: str

    version: str
    repository_dir: Path
    component_dir: Path

    @classmethod
    def build(cls, find_path: list[str], component_opt: ComponentOption):
        body = dict(component_opt)
        repository_name = component_opt.path.split("/")[0]
        for dir_spec in find_path:
            repo_filter, _, basedir = dir_spec.rpartition("@")
            if repo_filter and repo_filter != repository_name:
                continue
            basedir = Path(basedir)
            component_dir = basedir / component_opt.path
            if component_dir.exists():
                version = "unknown"
                try:
                    pyproject = component_dir / "pyproject.toml"
                    version = tomllib.loads(pyproject.read_text())["project"]["version"]
                except Exception:
                    pass
                body["version"] = version
                body["repository_dir"] = basedir / repository_name
                body["component_dir"] = component_dir
                return cls(**body)
        return None


class PulpDocsPluginConfig(Config):
    components = config_options.ListOfItems(ComponentOption, default=[])


class ComponentNav:
    def __init__(self, config: MkDocsConfig, component_slug: Path):
        self._nav_file_name: str = config.plugins["literate-nav"].config.nav_file
        self._component_slug = component_slug

        self._user_index_uri: Path = component_slug / "index.md"
        self._user_index_found: bool = False
        self._user_uris: list[Path] = []
        self._admin_uris: list[Path] = []

        self._dev_index_uri: Path = component_slug / "docs" / "dev" / "index.md"
        self._dev_index_found: bool = False
        self._dev_uris: list[Path] = []

        self._extra_uris: list[Path] = []

    def _add_to_taxonomy_nav(
        self,
        src_uri: Path,
        taxonomy_nav: list[t.Any],
        obj: t.Any = None,
    ) -> None:
        obj = obj or str(src_uri)
        if src_uri.parts[3] == "tutorials":
            k1, k2 = 0, "Tutorials"
        elif src_uri.parts[3] == "guides":
            k1, k2 = 1, "How-to Guides"
        elif src_uri.parts[3] == "learn":
            k1, k2 = 2, "Learn More"
        elif src_uri.parts[3] == "reference":
            k1, k2 = 3, "Reference"
        else:
            log.info(f"Could not navigate {src_uri}.")
            return
        if len(src_uri.parts) == 5 and src_uri.name == self._nav_file_name:
            taxonomy_nav[k1][k2] = str(src_uri.parent) + "/"
        if isinstance(taxonomy_nav[k1][k2], list):
            taxonomy_nav[k1][k2].append(obj)

    def add(self, src_uri: Path) -> None:
        assert src_uri.parts[0] == str(self._component_slug)
        if src_uri.suffix == ".md":
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
                self._add_to_taxonomy_nav(src_uri, user_nav)
            result.append({"Usage": user_nav})

            admin_nav: list[t.Any] = [
                {"Tutorials": []},
                {"How-to Guides": []},
                {"Learn More": []},
                {"Reference": []},
            ]
            for src_uri in self._admin_uris:
                self._add_to_taxonomy_nav(src_uri, admin_nav)
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
                self._add_to_taxonomy_nav(src_uri, result[1:])
        return result

    def missing_indices(self) -> t.Iterator[Path]:
        if not self._user_index_found and len(self._user_uris) + len(self._admin_uris) > 0:
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
    elif isinstance(nav_item, Link):
        return ""
    else:
        raise NotImplementedError(f"Unknown nav item {nav_item}")


# jinja2 macros and helpers


def get_component_data(
    component: Component,
) -> dict[str, str | list[str]]:
    """Generate data for rendering md templates."""
    component_dir = component.component_dir
    path = component_dir.name

    github_org = "pulp"
    try:
        template_config = component_dir / "template_config.yml"
        github_org = yaml.safe_load(template_config.read_text())["github_org"]
    except Exception:
        pass

    links = []
    if component.rest_api:
        links.append(f"[REST API](site:{path}/restapi/)")
    links.append(f"[Repository](https://github.com/{github_org}/{path})")
    if (component_dir / "CHANGES.md").exists():
        links.append(f"[Changelog](site:{path}/changes/)")

    return {
        "title": f"[{component.title}](site:{path}/)",
        "kind": component.kind,
        "version": component.version,
        "links": links,
    }


def rss_items() -> list:
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


def load_components(find_path: list[str], config: PulpDocsPluginConfig, draft: bool):
    loaded_components = []
    for component_opt in config.components:
        component = Component.build(find_path, component_opt)
        if component:
            loaded_components.append(component)
    all_components = {o.path for o in config.components}
    missing_components = all_components.difference({o.path for o in loaded_components})
    if not missing_components:
        return loaded_components
    # handle missing_components case
    missing_components = sorted(missing_components)
    if not draft:
        raise PluginError(f"Components missing: {missing_components}.")
    return loaded_components


def log_pulp_config(
    mkdocs_file: str, path: list[str], loaded_components: list[Component], site_dir: str
):
    components_map = defaultdict(list)
    sorted_components = sorted(loaded_components, key=lambda o: o.path)
    for component in sorted_components:
        basedir = str(component.repository_dir.parent)
        components_map[basedir].append(str(component.path))
    display = {
        "config": str(mkdocs_file),
        "path": str(path),
        "build_output": site_dir,
        "loaded_components": components_map,
    }
    display_str = json.dumps(display, indent=4)
    log.info(display_str)


def get_pulpdocs_git_url(config: PulpDocsPluginConfig):
    for component in config.components:
        if component.path == "pulp-docs":
            return component.git_url
    raise RuntimeError("Did pulp-docs changed it's name or was removed from mkdocs.yml?")


class PulpDocsPlugin(BasePlugin[PulpDocsPluginConfig]):
    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:
        # mkdocs may default to the installation dir
        if "site-packages" in config.site_dir:
            config.site_dir = str(Path.cwd() / "site")

        self.blog = ctx_blog.get()
        self.docstrings = ctx_docstrings.get()
        self.draft = ctx_draft.get()
        self.dryrun = ctx_dryrun.get()

        self.mkdocs_yml_dir = Path(config.docs_dir).parent
        self.find_path = ctx_path.get() or [str(Path().cwd().parent)]
        self.loaded_components = load_components(self.find_path, self.config, self.draft)
        self.pulpdocs_git_url = get_pulpdocs_git_url(self.config)

        mkdocs_file = self.mkdocs_yml_dir / "mkdocs.yml"
        log_pulp_config(mkdocs_file, self.find_path, self.loaded_components, config.site_dir)

        mkdocstrings_config = config.plugins["mkdocstrings"].config
        components_var = []
        for component in self.loaded_components:
            components_var.append(get_component_data(component))
            config.watch.append(str(component.component_dir / "docs"))
            component_dir = str(component.component_dir.resolve())
            mkdocstrings_config.handlers["python"]["paths"].append(component_dir)

        macros_plugin = config.plugins["macros"]
        macros_plugin.register_macros({"rss_items": rss_items})
        macros_plugin.register_variables({"components": components_var})

        blog_plugin = config.plugins["material/blog"]
        blog_plugin.config["enabled"] = self.blog

        mkdocstrings_plugin = config.plugins["mkdocstrings"]
        mkdocstrings_plugin.config["enabled"] = self.docstrings

        if self.dryrun is True:
            log.info("Stopping: dry-run in enabled")
            sys.exit(0)

        return config

    def on_files(self, files: Files, /, *, config: MkDocsConfig) -> Files | None:
        log.info(f"Loading Pulp components: {self.loaded_components}")
        pulp_docs_component = [c for c in self.loaded_components if c.path == "pulp-docs"]
        if pulp_docs_component:
            pulp_docs_git = Repo(pulp_docs_component[0].repository_dir)
        else:
            log.warning("Pulp Docs repository is missing. Can't get api.json for plugins.")
            pulp_docs_git = None

        user_nav: dict[str, t.Any] = {}
        dev_nav: dict[str, t.Any] = {}
        for component in self.loaded_components:
            component_dir = component.component_dir

            log.info(f"Fetching docs from '{component.title}'.")
            git_repository_dir = component.repository_dir
            try:
                git_branch = Repo(git_repository_dir).active_branch.name
            except TypeError:
                git_branch = None
            component_parent_dir = component_dir.parent
            component_docs_dir = component_dir / "staging_docs"
            if component_docs_dir.exists():
                log.warning(f"Found deprecated 'staging_docs' directory in {component.path}.")
            else:
                component_docs_dir = component_dir / "docs"
            component_slug = Path(component_dir.name)
            assert component_docs_dir.exists()

            component_nav = ComponentNav(config, component_slug)

            for dirpath, dirnames, filenames in component_docs_dir.walk(follow_symlinks=True):
                for filename in filenames:
                    abs_src_path = dirpath / filename
                    pulp_meta: dict[str, t.Any] = {}
                    if abs_src_path == component_docs_dir / "index.md":
                        src_uri = component_slug / "index.md"
                        pulp_meta["index"] = True
                    elif abs_src_path == component_docs_dir / "dev" / "index.md":
                        src_uri = component_slug / "docs" / "dev" / "index.md"
                        pulp_meta["index"] = True
                    else:
                        src_uri = abs_src_path.relative_to(component_parent_dir)
                    log.debug(f"Adding {abs_src_path} as {src_uri}.")
                    if component.git_url and git_branch:
                        git_relpath = abs_src_path.relative_to(git_repository_dir)
                        pulp_meta["edit_url"] = (
                            f"{component.git_url}/edit/{git_branch}/{git_relpath}"
                        )
                    new_file = File.generated(config, src_uri, abs_src_path=abs_src_path)
                    new_file.pulp_meta = pulp_meta
                    files.append(new_file)
                    component_nav.add(src_uri)

            for src_uri in component_nav.missing_indices():
                content = MISSING_INDEX_TEMPLATE.format(component=component.title)
                new_file = File.generated(config, src_uri, content=content)
                new_file.pulp_meta = {"index": True}
                files.append(new_file)

            if component.rest_api:
                src_uri = component_slug / "restapi.md"
                content = REST_API_MD.format(component=component.title)
                files.append(File.generated(config, src_uri, content=content))
                component_nav.add(src_uri)
                if pulp_docs_git:  # currently we require pulp_docs repository to be loaded
                    api_json_content = self.get_openapi_spec(component, pulp_docs_git)
                    src_uri = (component_dir / "api.json").relative_to(component_parent_dir)
                    files.append(File.generated(config, src_uri, content=api_json_content))

            component_changes = component_dir / "CHANGES.md"
            if component_changes.exists():
                src_uri = component_slug / "changes.md"
                files.append(File.generated(config, src_uri, abs_src_path=component_changes))
                component_nav.add(src_uri)

            user_nav.setdefault(component.kind, []).append(
                {component.title: component_nav.user_nav()}
            )
            dev_nav.setdefault(component.kind, []).append(
                {component.title: component_nav.dev_nav()}
            )

        config.nav[1]["User Manual"].extend([{key: value} for key, value in user_nav.items()])
        config.nav[2]["Developer Manual"].extend([{key: value} for key, value in dev_nav.items()])
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

    def get_openapi_spec(self, component, pulp_docs_git: Repo) -> str:
        found_locally = False
        remotes = [""] + [f"{o}/" for o in pulp_docs_git.remotes]
        for remote in remotes:
            git_object = f"{remote}docs-data:data/openapi_json/{component.rest_api}-api.json"
            try:
                api_json = pulp_docs_git.git.show(git_object)
                found_locally = True
                break
            except GitCommandError:
                continue

        if not found_locally:
            pulp_docs_git.git.fetch(self.pulpdocs_git_url, "docs-data")
            git_object = f"FETCH_HEAD:data/openapi_json/{component.rest_api}-api.json"
            api_json = pulp_docs_git.git.show(git_object)
        # fix the logo url for restapi page, which is defined in the openapi spec file
        api_json = api_json.replace(
            "/pulp-docs/docs/assets/pulp_logo_icon.svg", "/assets/pulp_logo_icon.svg"
        )
        return api_json
