import os
from typing import NamedTuple

HEADER_ERROR = "Broken links:"


class LinkError(NamedTuple):
    link_target: str
    src_filename: str
    src_line: str
    src_lineno: int


def linkchecker(component_rootdir: str, filenames: list[str]) -> int:
    cumulative_errors = []
    for file in filenames:
        link_errors = check_file(component_rootdir, file)
        if not link_errors:
            continue
        cumulative_errors.extend(link_errors)
    report_errors(link_errors=cumulative_errors, component_rootdir=component_rootdir)
    return 0


def check_file(component_rootdir: str, src_filename: str) -> list[LinkError]:
    if not file_exists(src_filename):
        # log.warning(f"{file} does not exist.")
        return []

    link_errors = []
    with open(src_filename, "r") as fd:
        for src_lineno, src_line in enumerate(fd):
            invalid_links = check_line(src_line, component_rootdir)
            for link_target in invalid_links:
                link_error = LinkError(
                    link_target=link_target,
                    src_line=src_line,
                    src_filename=src_filename,
                    src_lineno=src_lineno,
                )
                link_errors.append(link_error)
    return link_errors


def check_line(line: str, basedir: str) -> list[str]:
    """Return invalid link in line."""
    invalid_links = []
    relative_path, component_name = os.path.split(basedir)

    for link in get_links(line):
        # Filter out external component links
        if not link.startswith(f"{component_name}/"):
            continue
        link_target = os.path.join(relative_path, link)
        if not file_exists(link_target):
            # Store original site: format
            invalid_links.append(link)
    return invalid_links


def get_links(line: str) -> list[str]:
    """Extract site: links from a markdown line."""
    import re

    links = []
    # Match inline links: [text](site:path)
    inline_pattern = r"\[([^\]]+)\]\(site:([^\)]+)\)"
    # Match reference links: [ref]: site:path
    reference_pattern = r"\[[^\]]+\]:\s*site:([^\s]+)"

    for match in re.finditer(inline_pattern, line):
        links.append(match.group(2))
    for match in re.finditer(reference_pattern, line):
        links.append(match.group(1))

    return links


def file_exists(file: str) -> bool:
    """Check if a file exists, treating .md extension as optional."""
    if os.path.exists(file):
        return True
    # Try with .md extension
    if os.path.exists(file + ".md"):
        return True
    return False


def report_errors(link_errors: list[LinkError], component_rootdir: str):
    """Print link errors to stdout."""
    if not link_errors:
        return
    print(HEADER_ERROR)
    for error in link_errors:
        line_str = error.src_line.strip()
        filename = os.path.relpath(error.src_filename, component_rootdir)
        lineno = error.src_lineno + 1
        print(f"{filename}:{lineno}:{line_str}")


def parse_arguments():
    """Parse command line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="Check markdown links")
    parser.add_argument("basedir", help="Base directory for link checking")
    parser.add_argument("files", nargs="+", help="Markdown files to check")
    args = parser.parse_args()
    return args.basedir, args.files


def main():
    """CLI entry point for the linkchecker command."""
    basedir, files = parse_arguments()
    exit(linkchecker(basedir, files))


if __name__ == "__main__":
    main()
