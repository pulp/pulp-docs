
import sys
from pathlib import Path
from textwrap import indent

import yaml
from jinja2 import Environment, FileSystemLoader

BASE_URL = "file:///home/pbrochad/workspace/multirepo-prototype"
REPOSITORIES = {
    "new_repo1": {
        "title": "RPM Package",
        "url": f"{BASE_URL}/new_repo1",
    },
    "new_repo2": {
        "title": "Debian Package",
        "url": f"{BASE_URL}/new_repo2",
    },
    "new_repo3": {
        "title": "Maven",
        "url": f"{BASE_URL}/new_repo3",
    },
}


def get_repo_content_grouped(persona: str, content_type: str):
    """Return [{title: import-url}]"""
    content_list = []
    for repo, repomd in REPOSITORIES.items():
        repo_title = repomd["title"]
        content_list.append({repo_title: import_from(
            repo, config=f"docs/mkdocs_{persona}_{content_type}.yml")})
    return content_list


def get_repo_content_flat(persona: str, content_type: str):
    """Return [{title: import-url}]"""
    content_list = []
    for repo, repomd in REPOSITORIES.items():
        repo_title = repomd["title"]
        content_list.append({repo_title: import_from(
            repo, config=f"docs/mkdocs_{persona}_{content_type}.yml")})
    return content_list


def import_from(repo: str, docs_dir: str = "docs/*", branch="main", config="docs/mkdocs.yml"):
    url = "file:///home/pbrochad/workspace/multirepo-prototype"
    return f'!import {url}/{repo}?branch={branch}&docs_dir={docs_dir}&config={config}'


def main():
    # section
    tutorials = [
        {"Overview": "tutorials/index.md"},
        {"Tutorials": get_repo_content_flat("content-manager", "tutorials")}
    ]
    guides = [
        {"Overview": "guides/index.md"},
        {"For Content-Management": get_repo_content_grouped(
            "content-manager", "guides")},
        {"For Sys-Admins": get_repo_content_grouped("sys-admin", "guides")},
    ]
    learn = [
        {"Overview": "learn/index.md"},
    ]
    reference = [
        {"Overview": "reference/index.md"},
    ]

    # main navigation
    navigation = [
        {"Home": "index.md"},
        {"Getting Started": tutorials},
        {"Guides": guides},
        {"Learn": learn},
        {"Reference": reference},
    ]

    # template substitution
    jinja = Environment(loader=FileSystemLoader(Path()))
    template = jinja.get_template("mkdocs.yml.j2")
    result = template.render(navigation=indent(
        yaml.dump(navigation), prefix="  "))

    file = Path() / "mkdocs.yml"
    file.write_text(result)


if __name__ == "__main__":
    sys.exit(main())
