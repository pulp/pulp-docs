from __future__ import annotations

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
from mkdocs.config import Config, config_options, load_config
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
class ComponentSpec(Config):
    """The fundamental static specs of a component."""

    git_url = config_options.Type(str, default="")
    path = config_options.Type(str)
    title = config_options.Type(str)
    kind = config_options.Type(str)
    rest_api = config_options.Type(str, default="")

    @property
    def component_name(self) -> str:
        return self.path.rpartition("/")[-1]

    @property
    def repository_name(self) -> str:
        return self.path.split("/")[0]

    @property
    def label(self) -> str:
        return self.rest_api


class PulpDocsPluginConfig(Config):
    components = config_options.ListOfItems(ComponentSpec, default=[])


@dataclass(frozen=True)
class LoadedComponent:
    """Full representation of a specific loaded component."""

    spec: ComponentSpec
    repository_dir: Path
    pkg_version: str
    git_revision: str
    git_dirty: bool

    @property
    def component_dir(self) -> Path:
        return self.repository_dir.parent / self.spec.path

    @property
    def component_name(self) -> str:
        return self.spec.component_name

    @property
    def repository_name(self) -> str:
        return self.spec.repository_name

    @property
    def label(self) -> str:
        return self.spec.label


class LoadResult(t.NamedTuple):
    all_specs: list[ComponentSpec]
    loaded: list[LoadedComponent]
    missing: list[ComponentSpec]


class RepositoryFinder:
    def __init__(self, lookup_paths: list[str] | None = None):
        # Maps lookup paths to a filter list of repository names
        # If the filter list is empty, use that path to find any repository
        self.lookup_dir_to_filter_list: dict[Path, list[str]] = defaultdict(list)
        for lookup_path in lookup_paths or []:
            self.add_lookup_path(lookup_path)

    def add_lookup_path(self, lookup_path: str):
        """Add either global or scoped lookup_path internally.

        A global lookup_path doesn't have a component specifier. E.g: '/some/random/path'
        A scoped lookup_path have a component specifier. E.g: 'pulpcore@/some/random/path'
        """
        repository_name, _, lookup_dir = lookup_path.rpartition("@")
        path = Path(lookup_dir)
        if not repository_name:  # lookup path is not scoped (aka, is global)
            self.lookup_dir_to_filter_list[path].clear()
        else:
            self.lookup_dir_to_filter_list[path].append(repository_name)

    def find(self, repo_name: str) -> Path | None:
        for lookup_dir, filter_list in self.lookup_dir_to_filter_list.items():
            # apply path scoping if it's a scoped path
            if filter_list and repo_name not in filter_list:
                continue
            repo_dir = lookup_dir / repo_name
            if repo_dir.exists():
                return repo_dir
        return None


class ComponentLoader:
    def __init__(
        self,
        lookup_paths: list[str],
        mkdocs_config: t.Optional[Path] = None,
        pulpdocs_plugin: t.Optional[PulpDocsPlugin] = None,
        draft: bool = False,
    ):
        """Manage finding and loading plugins from config file or mkdocs plugin.

        Exactly one of `mkdocs_config` or `pulpdocs_plugin` must be provided.

        Args:
            lookup_paths: The list of lookup paths for the repositories. A lookup path has
                the form: [repo@]path. Example: "pulpcore@/tmp/", "/tmp/workdir".
            mkdocs_config: Load components from an mkdocs config file.
            pulpdocs_plugin: Load components from a PulpDocsPlugin instance
            draft: Whether it fails if any component is missing
        """
        if bool(mkdocs_config) is bool(pulpdocs_plugin):
            raise ValueError("Provide exactly one of 'mkdocs_config' or 'pulpdocs_plugin'.")
        if mkdocs_config:
            pulpdocs_plugin = load_config(str(mkdocs_config)).plugins["PulpDocs"]  # type: ignore
        else:
            pulpdocs_plugin = pulpdocs_plugin
        self.component_specs: list[ComponentSpec] = pulpdocs_plugin.config.components  # type: ignore
        self.repository_finder = RepositoryFinder(lookup_paths)

    def load_component(self, comp_spec: ComponentSpec) -> LoadedComponent | None:
        repo_name = comp_spec.repository_name
        repo_dir = self.repository_finder.find(repo_name)
        if repo_dir:
            comp_dir = repo_dir.parent / comp_spec.component_name
            extractor = DataExtractor(comp_dir, repo_dir)
            return LoadedComponent(
                spec=comp_spec,
                repository_dir=repo_dir,
                pkg_version=extractor.package_version() or "unknown",
                git_revision=extractor.git_revision() or "unknown",
                git_dirty=extractor.git_dirty(),
            )
        return None

    def load_all(self) -> LoadResult:
        loaded_comps: list[LoadedComponent] = []
        missing_comps: list[ComponentSpec] = []
        for comp_spec in self.component_specs:
            loaded_comp = self.load_component(comp_spec)
            if loaded_comp:
                loaded_comps.append(loaded_comp)
            else:
                missing_comps.append(comp_spec)
        return LoadResult(
            all_specs=self.component_specs,
            loaded=loaded_comps,
            missing=missing_comps,
        )


class DataExtractor:
    def __init__(self, comp_dir: Path, repo_dir: Path):
        self.comp_dir = comp_dir
        self.repo_dir = repo_dir

    def package_version(self) -> t.Optional[str]:
        try:
            pyproject = self.comp_dir / "pyproject.toml"
            return tomllib.loads(pyproject.read_text())["project"]["version"]
        except Exception:
            log.warning(f"Couldnt' get  version for: {str(self.comp_dir)}")
        return None

    def git_revision(self) -> t.Optional[str]:
        try:
            repo = Repo(self.repo_dir)
            return repo.head.commit.hexsha
        except Exception as e:
            log.warning(f"Couldn't get git revision for: {str(self.repo_dir)}.\n{e}")
        return None

    def git_dirty(self) -> bool:
        try:
            repo = Repo(self.repo_dir)
            return repo.is_dirty()
        except Exception as e:
            log.warning(f"Couldn't check git status for: {str(self.repo_dir)}.\n{e}")
        return False


def default_lookup_paths() -> list[str]:
    return [str(Path().cwd().parent)]


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
    comp: LoadedComponent,
) -> dict[str, str | list[str]]:
    """Generate data for rendering md templates."""
    comp_dir = comp.component_dir
    comp_name = comp.component_name

    github_org = "pulp"
    try:
        template_config = comp.component_dir / "template_config.yml"
        github_org = yaml.safe_load(template_config.read_text())["github_org"]
    except Exception:
        pass

    links = []
    if comp.spec.rest_api:
        links.append(f"[REST API](site:{comp_name}/restapi/)")
    links.append(f"[Repository](https://github.com/{github_org}/{comp_name})")
    if (comp_dir / "CHANGES.md").exists():
        links.append(f"[Changelog](site:{comp_name}/changes/)")

    return {
        "title": f"[{comp.spec.title}](site:{comp_name}/)",
        "kind": comp.spec.kind,
        "version": comp.pkg_version,
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


def log_pulp_config(
    mkdocs_file: str, path: list[str], loaded_components: list[LoadedComponent], site_dir: str
):
    repo_dir_to_comp_info = defaultdict(list)
    for comp in loaded_components:
        repo_dir = str(comp.repository_dir.parent)
        short_sha = comp.git_revision[:6]
        dirty = " (DIRTY)" if comp.git_dirty else ""
        info = f"{short_sha} {str(comp.spec.path)}{dirty}"
        repo_dir_to_comp_info[repo_dir].append(info)
    display = {
        "config": str(mkdocs_file),
        "path": str(path),
        "build_output": site_dir,
        "loaded_components": repo_dir_to_comp_info,
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
        self.mkdocs_yml_dir = Path(config.docs_dir).parent
        if "site-packages" in config.site_dir:
            config.site_dir = str(Path.cwd() / "site")

        self.blog = ctx_blog.get()
        self.docstrings = ctx_docstrings.get()
        self.draft = ctx_draft.get()
        self.dryrun = ctx_dryrun.get()
        self.pulpdocs_git_url = get_pulpdocs_git_url(self.config)

        # Load components
        lookup_paths = ctx_path.get() or default_lookup_paths()
        component_loader = ComponentLoader(lookup_paths, pulpdocs_plugin=self)
        load_result = component_loader.load_all()
        if load_result.missing and not self.draft:
            missing_names = sorted([p.component_name for p in load_result.missing])
            raise PluginError(f"Components missing: {missing_names}.")
        self.loaded_comps = load_result.loaded

        mkdocs_file = self.mkdocs_yml_dir / "mkdocs.yml"
        log_pulp_config(mkdocs_file, lookup_paths, self.loaded_comps, config.site_dir)

        mkdocstrings_config = config.plugins["mkdocstrings"].config
        components_var = []
        for component in self.loaded_comps:
            components_var.append(get_component_data(component))
            config.watch.append(str(component.component_dir / "docs"))
            component_dir = component.component_dir.resolve()
            mkdocstrings_config.handlers["python"]["paths"].append(str(component_dir))
            mkdocstrings_config.handlers["python"]["paths"].append(str(component_dir / "src"))

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
        log.info(f"Loading Pulp components: {self.loaded_comps}")
        pulp_docs_component = [c for c in self.loaded_comps if c.spec.path == "pulp-docs"]
        if pulp_docs_component:
            pulp_docs_git = Repo(pulp_docs_component[0].repository_dir)
        else:
            log.warning("Pulp Docs repository is missing. Can't get api.json for plugins.")
            pulp_docs_git = None

        user_nav: dict[str, t.Any] = {}
        dev_nav: dict[str, t.Any] = {}
        for comp in self.loaded_comps:
            title = comp.spec.title
            kind = comp.spec.kind
            git_url = comp.spec.git_url
            rest_api = comp.spec.rest_api
            comp_dir = comp.component_dir
            repo_dir = comp.repository_dir
            component_slug = Path(comp_dir.name)
            component_nav = ComponentNav(config, component_slug)

            log.info(f"Fetching docs from '{comp.spec.title}'.")
            try:
                git_branch = Repo(repo_dir).active_branch.name
            except TypeError:
                git_branch = None
            docs_dir = comp_dir / "staging_docs"
            if docs_dir.exists():
                log.warning(f"Found deprecated 'staging_docs' directory in {comp.spec.path}.")
            else:
                docs_dir = comp_dir / "docs"
            assert docs_dir.exists()

            for dirpath, dirnames, filenames in docs_dir.walk(follow_symlinks=True):
                for filename in filenames:
                    abs_src_path = dirpath / filename
                    pulp_meta: dict[str, t.Any] = {}
                    if abs_src_path == docs_dir / "index.md":
                        src_uri = component_slug / "index.md"
                        pulp_meta["index"] = True
                    elif abs_src_path == docs_dir / "dev" / "index.md":
                        src_uri = component_slug / "docs" / "dev" / "index.md"
                        pulp_meta["index"] = True
                    else:
                        src_uri = abs_src_path.relative_to(comp_dir.parent)
                    log.debug(f"Adding {abs_src_path} as {src_uri}.")
                    if git_url and git_branch:
                        git_relpath = abs_src_path.relative_to(repo_dir)
                        pulp_meta["edit_url"] = f"{git_url}/edit/{git_branch}/{git_relpath}"
                    new_file = File.generated(config, src_uri, abs_src_path=abs_src_path)
                    new_file.pulp_meta = pulp_meta
                    files.append(new_file)
                    component_nav.add(src_uri)

            for src_uri in component_nav.missing_indices():
                content = MISSING_INDEX_TEMPLATE.format(component=title)
                new_file = File.generated(config, str(src_uri), content=content)
                new_file.pulp_meta = {"index": True}
                files.append(new_file)

            if rest_api:
                src_uri = component_slug / "restapi.md"
                content = REST_API_MD.format(component=title)
                files.append(File.generated(config, src_uri, content=content))
                component_nav.add(src_uri)
                if pulp_docs_git:  # currently we require pulp_docs repository to be loaded
                    api_json_content = self.get_openapi_spec(comp, pulp_docs_git)
                    src_uri = (comp_dir / "api.json").relative_to(comp_dir.parent)
                    files.append(File.generated(config, src_uri, content=api_json_content))

            component_changes = comp_dir / "CHANGES.md"
            if component_changes.exists():
                src_uri = component_slug / "changes.md"
                files.append(File.generated(config, src_uri, abs_src_path=component_changes))
                component_nav.add(src_uri)

            user_nav.setdefault(kind, []).append({title: component_nav.user_nav()})
            dev_nav.setdefault(kind, []).append({title: component_nav.dev_nav()})

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

    def get_openapi_spec(self, comp: LoadedComponent, pulp_docs_git: Repo) -> str:
        rest_api = comp.spec.rest_api
        found_locally = False
        remotes = [""] + [f"{o}/" for o in pulp_docs_git.remotes]
        for remote in remotes:
            git_object = f"{remote}docs-data:data/openapi_json/{rest_api}-api.json"
            try:
                api_json = pulp_docs_git.git.show(git_object)
                found_locally = True
                break
            except GitCommandError:
                continue

        if not found_locally:
            pulp_docs_git.git.fetch(self.pulpdocs_git_url, "docs-data")
            git_object = f"FETCH_HEAD:data/openapi_json/{rest_api}-api.json"
            api_json = pulp_docs_git.git.show(git_object)
        # fix the logo url for restapi page, which is defined in the openapi spec file
        api_json = api_json.replace(
            "/pulp-docs/docs/assets/pulp_logo_icon.svg", "/assets/pulp_logo_icon.svg"
        )
        return api_json
