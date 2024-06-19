from typing import Optional, Union

from mkdocs.structure.nav import Page, Section


class SectionToc:
    def __init__(self, section: Section, config):
        self._section = section
        self._config = config
        self._lines: list[str] = []

    def process(self, ignore_page: Optional[Page] = None):
        """Generate markdown lines from section data."""

        def indent_write(obj, depth: int):
            if obj == ignore_page:
                return

            self._add_item(obj, depth)
            if isinstance(obj, Section):
                for item in obj.children:
                    indent_write(item, depth + 1)

        for sub_section in self._section.children:
            indent_write(sub_section, 0)
        return self

    def _add_item(self, item: Union[Section, Page], depth: int):
        """Convert and store Section/Page as markdown (str) list entry."""
        if isinstance(item, Page):
            item.read_source(self._config)
        title = item.title
        if url := getattr(item, "url", ""):
            toc_entry = "[{title}](site:{url})".format(title=title, url=url)
        else:
            toc_entry = "[{title}](#)".format(title=title)

        space = "    " * depth
        line = "{space}* {toc_entry}".format(space=space, toc_entry=toc_entry)
        self._lines.append(line)

    def dump(self, fd) -> None:
        """Dump the ToC content o file."""
        ...

    def dumps(self) -> str:
        """Dump the ToC as string."""
        return "\n".join(self._lines)

    def __len__(self):
        return len(self._lines)
