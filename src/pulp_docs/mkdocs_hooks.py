"""
Hooks for mkdocs events.

See: https://www.mkdocs.org/user-guide/configuration/#hooks
"""


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
