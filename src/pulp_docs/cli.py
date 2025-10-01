import asyncio
from importlib import resources
from pathlib import Path

import click
import git
from mkdocs.__main__ import cli as mkdocs_cli
from mkdocs.config import load_config

from pulp_docs.context import ctx_blog, ctx_docstrings, ctx_draft, ctx_dryrun, ctx_path
from pulp_docs.plugin import load_components


def blog_callback(ctx: click.Context, param: click.Parameter, value: bool) -> bool:
    ctx_blog.set(value)
    return value


def docstrings_callback(ctx: click.Context, param: click.Parameter, value: bool) -> bool:
    ctx_docstrings.set(value)
    return value


def draft_callback(ctx: click.Context, param: click.Parameter, value: bool) -> bool:
    ctx_draft.set(value)
    return value


def dryrun_callback(ctx: click.Context, param: click.Parameter, value: bool) -> bool:
    ctx_dryrun.set(value)
    return value


def find_path_callback(ctx: click.Context, param: click.Parameter, value: str) -> bool:
    result = [item.strip() for item in value.split(":") if item.strip()]
    ctx_path.set(result)
    return result


async def clone_repositories(repositories: set[str], dest_dir: Path) -> None:
    """Clone multiple repositories concurrently."""

    async def clone_repository(repo_url: str) -> None:
        repo_name = repo_url.split("/")[-1]
        repo_path = dest_dir / repo_name
        if repo_path.exists():
            click.echo(f"Repository {repo_name} already exists at {repo_path}, skipping.")
            return
        click.echo(f"Cloning {repo_url} to {repo_path}...")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: git.Repo.clone_from(repo_url, repo_path, depth=1))
        click.echo(f"Successfully cloned {repo_name}")

    tasks = [clone_repository(repo) for repo in repositories]
    await asyncio.gather(*tasks)


blog_option = click.option(
    "--blog/--no-blog",
    default=True,
    expose_value=False,
    callback=blog_callback,
    help="Build blog.",
)
docstrings_option = click.option(
    "--docstrings/--no-docstrings",
    default=True,
    expose_value=False,
    callback=docstrings_callback,
    help="Enable mkdocstrings plugin.",
)

draft_option = click.option(
    "--draft/--no-draft",
    expose_value=False,
    callback=draft_callback,
    help="Don't fail if repositories are missing.",
)

path_option = click.option(
    "--path",
    envvar="PULPDOCS_PATH",
    expose_value=False,
    default="",
    callback=find_path_callback,
    help="A colon separated list of lookup paths in the form:[repo1@]path1 [:[repo2@]path2 [...]].",
)

dryrun_option = click.option(
    "--dry-run/--no-dry-run",
    expose_value=False,
    default=False,
    callback=dryrun_callback,
    help="Only gather and parse all configuration, but don't run.",
)


@click.command()
@click.option(
    "--dest",
    required=True,
    type=click.Path(file_okay=False),
    help="Destination directory for cloned repositories",
)
@click.option(
    "-f",
    "--config-file",
    type=click.Path(exists=True, dir_okay=False),
    default="mkdocs.yml",
    envvar="PULPDOCS_DIR",
    help="Path to mkdocs.yml config file",
)
@click.option(
    "--path-exclude",
    default="",
    callback=find_path_callback,
    help=(
        "A colon separated list of lookup paths to exclude in the form "
        "[repo1@]path1 [:[repo2@]path2 [...]]."
    ),
)
def fetch(dest, config_file, path_exclude):
    """Fetch repositories to destination dir."""
    dest_path = Path(dest)
    pulpdocs_plugin = load_config(config_file).plugins["PulpDocs"]
    all_components = pulpdocs_plugin.config.components
    all_repositories_set = {r.git_url for r in all_components if r.git_url}
    found_components = load_components(path_exclude, pulpdocs_plugin.config, draft=True)
    found_repositories_set = {r.git_url for r in found_components}
    final_repositories_set = all_repositories_set - found_repositories_set

    if not dest_path.exists():
        dest_path.mkdir(parents=True)
    asyncio.run(clone_repositories(final_repositories_set, dest_path))


main = mkdocs_cli
main.add_command(fetch)


def get_default_mkdocs() -> Path | None:
    import pulp_docs

    # for install from distribution packages
    package_files = resources.files(pulp_docs)
    mkdocs_file = Path(package_files) / "mkdocs.yml"
    if mkdocs_file.is_file():
        return mkdocs_file

    # for editable installs
    package_root = Path(pulp_docs.__file__).parent.parent.parent
    mkdocs_file = package_root / "mkdocs.yml"
    if mkdocs_file.is_file():
        return mkdocs_file

    raise RuntimeError(
        "Can't find default mkdocs.yml. It should be shipped with pulp-docs python package."
    )


for command_name in ["build", "serve"]:
    sub_command = main.commands.get(command_name)
    draft_option(sub_command)
    blog_option(sub_command)
    docstrings_option(sub_command)
    path_option(sub_command)
    dryrun_option(sub_command)
    serve_options = sub_command.params
    config_file_opt = next(filter(lambda opt: opt.name == "config_file", serve_options))
    config_file_opt.envvar = "PULPDOCS_DIR"
    config_file_opt.default = get_default_mkdocs()
