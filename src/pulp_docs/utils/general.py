import typing as t
from pathlib import Path


def get_label(repo_name: str):
    """Get app_label from repo_name.

    E.g: 'pulp_ostree' -> 'ostree'.
    """
    if repo_name == "pulpcore":
        return "core"
    # E.g: "pulp-ostree" -> "pulp_ostree" -> ("", "pulp_", "ostree")
    return repo_name.replace("-", "_").rpartition("pulp_")[2]


def get_git_ignored_files(repo_path: Path) -> t.List[str]:
    """Get list of ignored files as defined in the repo .gitignore"""
    repo_gitignore = Path(repo_path / ".gitignore")
    gitignore_files = []
    if repo_gitignore.exists():
        gitignore_files.extend(
            [
                f.strip("/")
                for f in repo_gitignore.read_text().splitlines()
                if f and not f.startswith("#")
            ]
        )
    gitignore_files.append("tests")
    return gitignore_files
