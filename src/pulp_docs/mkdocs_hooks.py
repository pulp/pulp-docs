"""
Hooks for mkdocs events.

See: https://www.mkdocs.org/user-guide/configuration/#hooks
"""

import re
from collections import defaultdict

from bs4 import BeautifulSoup as bs
from mkdocs.structure.nav import Page, Section

from pulp_docs.utils.toc import SectionToc

# TODO: this should be more generalized for section pages
section_pattern = re.compile(r"([a-z-_]+)/index.md")
dev_section_pattern = re.compile(r"([a-z-_]+)/docs/dev/index.md")

toc_pages: dict[str, dict[str, SectionToc]] = {
    "User Manual": defaultdict(),
    "Developer Manual": defaultdict(),
}
dev_toc_pages: dict[str, SectionToc] = {}

TOC_PAGE_CSS = """
<style>
  .md-typeset ul {
    line-height: 1.1;
  }
</style>
"""


def get_index_page_from(section: Section) -> Page:
    for item in section.children:
        if isinstance(item, Page) and "index.md" in item.file.src_uri:
            return item
    raise RuntimeError(f"Couldnt find index page for {section.title}.")


def on_nav(nav, config, files):
    """
    Create repo-index-toc data here.
    See hook events: https://www.mkdocs.org/dev-guide/plugins/#events
    """
    for section_name in ["User Manual", "Developer Manual"]:
        # Get a flat list of plugin Section from for '{Type} Manual'
        user_section = [s for s in nav.items if s.title == section_name][0]
        user_subsections = [s for s in user_section.children if s.is_section]
        user_plugins = [
            s for type_section in user_subsections for s in type_section.children
        ]

        # Create and save each plugin section toc as SectionToc
        for section in user_plugins:
            plugin_page = get_index_page_from(section)
            plugin_name = plugin_page.url.split("/")[0]
            toc = SectionToc(section, config).process(ignore_page=plugin_page)
            toc_pages[section_name][plugin_name] = toc


def on_page_markdown(markdown, page: Page, config, files):
    plugin_toc = None

    if match := section_pattern.match(page.file.src_uri):
        plugin_name = match.groups()[0]
        plugin_toc = toc_pages["User Manual"].get(plugin_name, None)

    if match := dev_section_pattern.match(page.file.src_uri):
        plugin_name = match.groups()[0]
        plugin_toc = toc_pages["Developer Manual"].get(plugin_name, None)

    if plugin_toc and len(plugin_toc) > 0:
        markdown += TOC_PAGE_CSS + "\n\n---\n\n## Summary\n\n" + plugin_toc.dumps()

    return markdown


def on_serve(server, config, builder):
    """
    Hook to unwatch the temp dirs.

    See: https://www.mkdocs.org/dev-guide/plugins/#on_serve
    """
    tmpdir = config["docs_dir"]
    mkdocs_yml = config["config_file_path"]
    server.unwatch(tmpdir)
    server.unwatch(mkdocs_yml)
    return server


REDOC_HEADER = """
<link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
<style>
  body {
    margin: 0;
    padding: 0;
  }
</style>
"""

REDOC_TAG_TEMPLATE = """
<redoc spec-url='%s'></redoc>
"""

REDOC_SCRIPT = """
<script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"> </script>
"""


def on_post_page(output, page, config):
    if basepath := page.meta.get("restapi_json_file"):
        redoc_tag = REDOC_TAG_TEMPLATE % basepath
        bs_page = bs(output, "html.parser")

        # Append <head>scripts
        bs_page.html.head.append(bs(REDOC_HEADER, "html.parser"))

        # Replace main content-container with <redoc> tag
        main_container = bs_page.find_all("div", class_="md-main__inner")[0]
        main_container.replace_with(bs(redoc_tag, "html.parser"))

        # Append <script> tag at the end of body
        bs_page.html.body.append(bs(REDOC_SCRIPT, "html.parser"))

        # Remove footer (looks weird)
        footer = bs_page.find_all(class_="md-footer")[0]
        footer.decompose()
        return str(bs_page)
