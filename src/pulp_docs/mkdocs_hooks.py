"""
Hooks for mkdocs events.

See: https://www.mkdocs.org/user-guide/configuration/#hooks
"""
from bs4 import BeautifulSoup as bs


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
