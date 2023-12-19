
import argparse
import json
import os
import subprocess
import sys
import typing as t
from collections import defaultdict
from pathlib import Path

import yaml

PERSONAS = ("content-manager", "developer", "sys-admin")
CONTENT_TYPES = ("guides", "learn", "tutorials")


def process_glob(files) -> list:
    return [{f.stem: str(Path(*f.parts[1:]))} for f in files]


def load_same_structure(doc_basepath: Path) -> dict:
    yaml_tree = []

    for i, persona in enumerate(PERSONAS):
        yaml_tree.append({persona: []})
        for j, content_type in enumerate(CONTENT_TYPES):
            files = Path(
                f"{doc_basepath}/{persona}/{content_type}").glob("*.md")
            yaml_tree[i][persona].append(
                {content_type: process_glob(files)})
    return {"mkdocs": {"nav": yaml_tree}}


def load_flat_navs(doc_basepath: Path) -> dict:
    navs = {}
    for content_type in CONTENT_TYPES:
        for persona in PERSONAS:
            if content_type != "tutorials":
                files = doc_basepath.glob(f"{persona}/{content_type}/*.md")
                navs[f"mkdocs_{persona}_{content_type}"] = {
                    "nav": process_glob(files)}
            else:
                files = doc_basepath.glob(f"{persona}/{content_type}/*/*.md")
                _files = doc_basepath.glob(f"{persona}/{content_type}/*/*.md")
                tutorial_name = list(_files)[0].parts[-2]
                navs[f"mkdocs_{persona}_{content_type}"] = {
                    "nav": [{tutorial_name: process_glob(files)}]}
    return navs


def generate_yamls(doc_basepath: Path, loader=load_same_structure):
    """Create mkdocs yaml file for each combination of {persona}{content-type}"""
    # clean yaml files
    old_yamls = doc_basepath.glob("*.yml")
    for old in old_yamls:
        old.unlink()

    # create yaml file for each persona x content-type
    mkdocs_navs = loader(doc_basepath)
    for mkdocs_name, mkdocs_nav in mkdocs_navs.items():
        mkdocs_filename = f"{mkdocs_name}.yml"
        with open(doc_basepath / mkdocs_filename, "w") as file:
            print(f"Created {mkdocs_filename}")
            yaml.dump(mkdocs_nav, file)


def load_repo_filetree(doc_basepath: Path):
    """
    Load repository filetree as dict object

    Example:
        {
            admin_guides: [
                {'name': 'Guide 1', 'type': 'file', 'path': 'path/to/guide-1'},
                ...
            ],
            dev_tutorials: [
                {'name': 'Tutorial 1', 'type': 'dir', 'path': 'path/to/tutorial-1/', 'children': ['file-1.md', ..., 'file-n.md']},
                ...
            ],
        }
    """
    doctree = defaultdict(list)
    for content_type in CONTENT_TYPES:
        for persona in PERSONAS:
            files = doc_basepath.glob(f"{persona}/{content_type}/*")
            # breakpoint()
            for file in files:
                if file.is_file():
                    doctree[f"{persona}_{content_type}"].append({
                        'name': file.name,
                        'type': "file",
                        # 'path': str(file.relative_to("docs")),
                        'path': str(file),
                    })
                else:
                    doctree[f"{persona}_{content_type}"].append({
                        'name': file.name,
                        'type': "dir",
                        # 'path': str(file.relative_to("docs")),
                        'path': str(file),
                        'children': [child.name for child in file.glob("*.md")],
                    })
    return doctree


def generate_doctree(doc_basepath: Path):
    """Generate a json file containing listing of .md files and other metadata."""
    filename = doc_basepath / "doctree.json"
    doctree = load_repo_filetree(doc_basepath)
    with open(filename, "w") as file:
        json.dump(doctree, file)
    print(f"Created {filename}")


def commit_changes(basepath: Path):
    if not Path(basepath / ".git").exists():
        return 1

    git_cmd = ["git", "-C", basepath.absolute()]

    def run_git(*args):
        return subprocess.run(git_cmd+list(args))

    version_file = Path(basepath / "VERSION")
    if not version_file.exists() or (version_file.exists() and not version_file.read_text()):  # initialize version-file
        version_file.write_text("0")
        run_git("add", ".")
        run_git("commit", "-m", "add VERSION file")

    version = int(version_file.read_text())  # read current version
    version_file.write_text(str(version + 1))  # increment version

    run_git("add", ".")
    run_git("commit", "-m", f"commit {version}")


def main():
    # parse arguments
    parser = argparse.ArgumentParser(
        "mk_mkdocs", "Generates mkdocs for folder which contain 'docs' folder")
    parser.add_argument("--loader", "-l", default="flat", choices=["flat", "original"],
                        help="The loader used to generate the mkdocs.yml")
    parser.add_argument(
        "basepaths", nargs="+", help="The basepath to look for docs folder")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--doctree", action="store_true")
    args = parser.parse_args()

    # choose loaders
    loaders = {
        "flat": load_flat_navs,
        "original": load_same_structure,
    }
    loader = loaders[args.loader]

    errors = []
    # process all repos passed as arguments
    for repo_name in args.basepaths:
        # check filesystem
        basepath = Path(repo_name)
        docs_basepath = Path(basepath / "docs")
        if not docs_basepath.exists():
            errors.append(
                "Error: The basepath should contain a 'docs' folder.")
            continue

        # load filetree and dump as yaml
        print(f"Updating {repo_name}")
        if args.doctree:
            generate_doctree(docs_basepath)
        else:
            generate_yamls(docs_basepath, loader=loader)

        # git
        if args.commit:
            print(f"Commiting to {repo_name}")
            commit_changes(basepath)

    for error in errors:
        print(error)
    exit_code = 1 if errors else 0
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
