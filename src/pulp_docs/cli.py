import click

from mkdocs.__main__ import cli as mkdocs_cli
from pulp_docs.context import ctx_blog, ctx_draft


def blog_callback(ctx: click.Context, param: click.Parameter, value: bool) -> bool:
    ctx_blog.set(value)
    return value


def draft_callback(ctx: click.Context, param: click.Parameter, value: bool) -> bool:
    ctx_draft.set(value)
    return value


blog_option = click.option(
    "--blog/--no-blog",
    default=True,
    expose_value=False,
    callback=blog_callback,
    help="Don't fail if repositories are missing.",
)

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
blog_option(build_command)
blog_option(serve_command)
