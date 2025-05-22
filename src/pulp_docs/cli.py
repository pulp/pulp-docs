import asyncio
import tempfile
import json
import click
import git
from pathlib import Path

from mkdocs.__main__ import cli as mkdocs_cli
from mkdocs.config import load_config
from pulp_docs.context import ctx_blog, ctx_docstrings, ctx_draft, ctx_path


def blog_callback(ctx: click.Context, param: click.Parameter, value: bool) -> bool:
    ctx_blog.set(value)
    return value


def docstrings_callback(
    ctx: click.Context, param: click.Parameter, value: bool
) -> bool:
    ctx_docstrings.set(value)
    return value


def draft_callback(ctx: click.Context, param: click.Parameter, value: bool) -> bool:
    ctx_draft.set(value)
    return value


def find_path_callback(ctx: click.Context, param: click.Parameter, value: bool) -> bool:
    result = [item.strip() for item in value.split(":") if item.strip()]
    ctx_path.set(result)
    return result


async def clone_repositories(repositories: list[str], dest_dir: Path) -> None:
    """Clone multiple repositories concurrently."""

    async def clone_repository(repo_url: str) -> None:
        repo_name = repo_url.split("/")[-1]
        repo_path = dest_dir / repo_name
        if repo_path.exists():
            click.echo(
                f"Repository {repo_name} already exists at {repo_path}, skipping."
            )
            return
        click.echo(f"Cloning {repo_url} to {repo_path}...")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, lambda: git.Repo.clone_from(repo_url, repo_path, depth=1)
        )
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
    help="A colon separated list of lookup paths in the form: [repo1@]path1 [:[repo2@]path2 [...]].",
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
def fetch(dest, config_file):
    """Fetch repositories to destination dir."""
    dest_path = Path(dest)
    config = load_config(config_file)
    components = config.plugins["PulpDocs"].config.components
    repositories_list = list({r.git_url for r in components})

    if not dest_path.exists():
        dest_path.mkdir(parents=True)
    asyncio.run(clone_repositories(repositories_list, dest_path))


main = mkdocs_cli
main.add_command(fetch)

for command_name in ["build", "serve"]:
    sub_command = main.commands.get(command_name)
    draft_option(sub_command)
    blog_option(sub_command)
    docstrings_option(sub_command)
    path_option(sub_command)
    serve_options = sub_command.params
    config_file_opt = next(filter(lambda opt: opt.name == "config_file", serve_options))
    config_file_opt.envvar = "PULPDOCS_DIR"


@click.command()
@click.argument("pulp-docs-dir", type=click.Path(exists=True, file_okay=False))
@click.argument("component-dir", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--step",
    required=True,
    type=click.Choice(["all", "build"]),
    help="CI step to execute",
)
@click.pass_context
def ci(ctx, pulp_docs_dir, component_dir, step):
    """
    Run CI steps for Pulp documentation.
    """
    pulp_docs_path = Path(pulp_docs_dir)
    component_path = Path(component_dir)
    config_file = str(pulp_docs_path / "mkdocs.yml")
    site_dir = Path("site")
    temp_dir = Path(tempfile.gettempdir()) / "pulp-docs-ci"
    find_path = f"{pulp_docs_path.name}@{pulp_docs_path.parent}:{component_path.name}@{component_path.parent}:{temp_dir}"

    if step == "all" or step == "build":
        build_info = {
            "component_dir": str(component_path.absolute()),
            "pulp_docs_dir": str(pulp_docs_path.absolute()),
            "tmp_dir": str(temp_dir.absolute()),
            "site_dir": str(site_dir.absolute()),
        }
        ctx.invoke(fetch, dest=temp_dir, config_file=config_file)
        ctx.invoke(
            main.commands.get("build"),
            path=find_path,
            site_dir=str(site_dir),
            config_file=config_file,
        )
        click.echo("Build info:")
        click.echo(json.dumps(build_info, indent=4))


main.add_command(ci)
