import click

from mkdocs.__main__ import cli as mkdocs_cli
from pulp_docs.context import ctx_draft


def draft_callback(ctx: click.Context, param: click.Parameter, value: bool) -> bool:
    ctx_draft.set(value)
    return value


draft_option = click.option(
    "--draft/--no-draft",
    expose_value=False,
    callback=draft_callback,
    help="Don't fail if repositories are missing.",
)

main = mkdocs_cli

build_command = main.commands.get("build")
serve_command = main.commands.get("serve")
draft_option(build_command)
draft_option(serve_command)
