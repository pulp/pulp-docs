import argparse
import os
from typing import NamedTuple

HEADER_ERROR = "Found {n} broken links:"


class LinkError(NamedTuple):
    link_target: str
    src_filename: str
    src_line: str
    src_lineno: int


class LinkChecker:
    def __init__(self, basedir: str):
        self._relative_path, self._component_name = os.path.split(basedir)

    def is_valid(self, link: str) -> bool:
        """Return True if link is valid or should be ignored."""
        rel_link, _ = self._normalize_link(link)
        if self._should_skip(rel_link):
            return True
        abs_link = os.path.join(self._relative_path, rel_link)
        return file_exists(abs_link)

    def _should_skip(self, link: str) -> bool:
        if not link.startswith(f"{self._component_name}/"):
            return True
        if link.strip("/") == f"{self._component_name}/restapi":
            return True
        return False

    def _normalize_link(self, link: str):
        link = link.removeprefix("site:")
        link, _, query_string = link.partition("#")
        link = link.strip()
        return link, query_string


def linkchecker(component_rootdir: str, filenames: list[str]) -> int:
    checker = LinkChecker(component_rootdir)
    cumulative_errors = []
    for file in filenames:
        link_errors = check_file(file, checker)
        if not link_errors:
            continue
        cumulative_errors.extend(link_errors)
    report_errors(link_errors=cumulative_errors, component_rootdir=component_rootdir)
    if cumulative_errors:
        return 1
    return 0


def check_file(src_filename: str, checker: LinkChecker) -> list[LinkError]:
    link_errors = []
    with open(src_filename, "r") as fd:
        for src_lineno, src_line in enumerate(fd):
            invalid_links = check_line(src_line, checker)
            for link_target in invalid_links:
                link_error = LinkError(
                    link_target=link_target,
                    src_line=src_line,
                    src_filename=src_filename,
                    src_lineno=src_lineno,
                )
                link_errors.append(link_error)
    return link_errors


def check_line(line: str, checker: LinkChecker) -> list[str]:
    """Return invalid links in line."""
    return [link for link in get_links(line) if not checker.is_valid(link)]


def get_links(line: str) -> list[str]:
    """Extract site: links from a markdown line."""
    import re

    links = []
    # Match inline links: [text](site:path)
    inline_pattern = r"\[([^\]]+)\]\((site:[^\)]+)\)"
    # Match reference links: [ref]: site:path
    reference_pattern = r"\[[^\]]+\]:\s*(site:[^\s]+)"

    for match in re.finditer(inline_pattern, line):
        links.append(match.group(2))
    for match in re.finditer(reference_pattern, line):
        links.append(match.group(1))

    return links


def file_exists(file: str) -> bool:
    """Check if a file exists, treating .md extension as optional."""
    file = os.path.realpath(file)
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
    print(HEADER_ERROR.format(n=len(link_errors)))
    for error in link_errors:
        # line_str = error.src_line.strip()[:85] + " (...)"
        filename = os.path.relpath(error.src_filename, component_rootdir)
        lineno = error.src_lineno + 1
        print(f"{filename}:{lineno}  {error.link_target}")


def parse_arguments():
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description="Check markdown links")
    parser.add_argument(
        "--basedir",
        default=".",
        help="Base directory for link checking (default: current directory)",
    )
    parser.add_argument("files", nargs="+", help="Markdown files to check")
    args = parser.parse_args()

    # Shell-expand and normalize the basedir path
    basedir = os.path.expanduser(args.basedir)
    basedir = os.path.expandvars(basedir)
    basedir = os.path.abspath(basedir)

    if not os.path.exists(basedir):
        parser.error(f"basedir does not exist: {basedir}")
    if not os.path.isdir(basedir):
        parser.error(f"basedir is not a directory: {basedir}")

    for f in args.files:
        if not os.path.exists(f):
            parser.error(f"file does not exist: {f}")
        if os.path.isdir(f):
            parser.error(f"expected a file but got a directory: {f}")

    return basedir, args.files


def main():
    """CLI entry point for the linkchecker command."""
    basedir, files = parse_arguments()
    exit(linkchecker(basedir, files))


if __name__ == "__main__":
    main()
