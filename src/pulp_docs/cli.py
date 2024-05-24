"""
The main CLI module.
"""

import typing as t
from pathlib import Path

import click
from pulp_docs.main import Config, PulpDocs


class PulpDocsContext:
    def __init__(self):
        self.config = Config()
        self.pulp_docs = PulpDocs()


pass_pulpdocs_context = click.make_pass_decorator(PulpDocsContext, ensure=True)


@click.group()
@click.option("--verbose", "-v", is_flag=True)
@pass_pulpdocs_context
def main(ctx: PulpDocsContext, verbose: bool):
    """
    This is pulp-docs, a cli tool to help run and build multirepo documentation within Pulp project.
    """
    ctx.config.verbose = verbose


# mkdocs help wrapper
watch_help = (
    "A directory or file to watch for live reloading. Can be supplied multiple times."
)
no_reload_help = "Disable the live reloading in the development server."


@main.command()
@click.option(
    "--clear-cache",
    default=False,
    is_flag=True,
    help="Whether to clear the cache before serving (default=False).",
)
@click.option("--verbose", "-v", is_flag=True)
@click.option(
    "-w",
    "--watch",
    help=watch_help,
    type=click.Path(exists=True),
    multiple=True,
    default=[],
)
@click.option("--no-livereload", "livereload", flag_value=False, help=no_reload_help)
@click.option("--livereload", "livereload", flag_value=True, default=True, hidden=True)
@pass_pulpdocs_context
def serve(
    ctx: PulpDocsContext,
    clear_cache: bool,
    verbose: bool,
    watch: t.List[Path],
    livereload: bool,
):
    """Run mkdocs server."""
    config = ctx.config
    pulpdocs = ctx.pulp_docs

    config.clear_cache = clear_cache
    config.verbose = verbose
    config.watch = watch
    config.livereload = livereload

    dry_run = True if config.test_mode else False
    pulpdocs.serve(config, dry_run=dry_run)


@main.command()
@pass_pulpdocs_context
def build(ctx: PulpDocsContext):
    """Build mkdocs site."""
    config = ctx.config
    pulpdocs = ctx.pulp_docs

    config.verbose = True

    dry_run = True if config.test_mode else False
    pulpdocs.build(config, dry_run=dry_run)


@main.command()
@pass_pulpdocs_context
def status(ctx: PulpDocsContext):
    """Print relevant information about repositories that will be used."""
    config = ctx.config
    pulpdocs = ctx.pulp_docs
    pulpdocs.status(config)
