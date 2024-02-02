import typing as t
from pathlib import Path


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
