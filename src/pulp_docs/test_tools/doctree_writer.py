import re
import tomllib
from pathlib import Path

import yaml


def parse_doctree_file(doctree_file: Path, target: Path, project_name: str = "foobar"):
    """Create a whole documentation tree base on @doctree_file on @target.

    The goal is to facilitate creating fixtures for testing complex build cases, such
    as pulp structure.

    The declarative doctree file specifies a list of (path,content) tuples, with an semantic
    header separation..

    The overall structure is:

    ```pseudo-format
    {
        project-name-1: [{path: content}, ...,  {path: content}],
        ...
        project-name-N: [{path: content}, ..., {path: content}],
    }
    ```

    See `test_doctree_writer` for samples.

    Params:
        doctree_file: The input file to be parsed. Supports `.toml` `.yml` and `.doctree`
        target: The directory where the project should be written to.
    """

    def custom_parser(file: Path):
        _data = file.read_text()
        section_match = r"\n*\[\[\s*[\w-]+\s*\]\]\n"
        item_match = r"----+\n"
        section_split = [section for section in re.split(section_match, _data) if section]
        item_split = [
            item
            for section in section_split
            for item in re.split(item_match, section)
            if section and item
        ]
        item_partition = [t.partition("\n\n") for t in item_split if t]

        def sanitize_path(s):
            return s.partition("\n")[0].strip(" ")

        items = [{"path": sanitize_path(s[0]), "data": s[2]} for s in item_partition]
        return {"foobar": items}

    # Open and parse doctree file
    if doctree_file.suffix in (".yml", ".yaml"):
        data = yaml.load(doctree_file.read_text(), Loader=yaml.SafeLoader)
    elif doctree_file.suffix in (".toml",):
        data = tomllib.loads(doctree_file.read_text())
    elif doctree_file.suffix in (".doctree",):
        data = custom_parser(doctree_file)
        # breakpoint()
    else:
        raise NotImplementedError(f"File type not supported: {doctree_file.name}")

    # Create all directories
    for prj_name, contents in data.items():
        for item in contents:
            basedir, _, filename = item["path"].strip("/").rpartition("/")
            basedir = target / basedir
            basedir.mkdir(parents=True, exist_ok=True)
            Path(target / basedir / filename).write_text(item["data"])
