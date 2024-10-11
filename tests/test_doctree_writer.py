from pathlib import Path

import pytest
import textwrap

from pulp_docs.test_tools.doctree_writer import parse_doctree_file

file_sample = """\
# check-title

check-content

---
not/a/path (separator must have 4+ ---)

dont split."""

yaml_sample = f"""\
project1:
  - path: docs/index.md
    data: |
{textwrap.indent(file_sample, " " * 6)}
  - path: docs/guides/foo.md
    data: |
{textwrap.indent(file_sample, " " * 6)}
project2:
  - path: docs/guides/bar.md
    data: |
{textwrap.indent(file_sample, " " * 6)}
"""

toml_sample = f"""\
[[project1]]
path = 'docs/index.md'
data = '''
{file_sample}
'''

[[project1]]
path = 'docs/guides/foo.md'
data = '''
{file_sample}
'''

[[project2]]
path = 'docs/guides/bar.md'
data = '''
{file_sample}
'''
"""

# .doctree extenstion
custom_sample = f"""\
[[ project1 ]]
------------------------
docs/index.md

{file_sample}
-----------------
docs/guides/foo.md
---------------#ignore

{file_sample}

[[ project2 ]]
-----
docs/guides/bar.md

{file_sample}
"""


@pytest.mark.parametrize(
    "file_ext,content",
    [
        pytest.param("toml", toml_sample, id="toml"),
        pytest.param("yaml", yaml_sample, id="yaml"),
        pytest.param("yml", yaml_sample, id="yml"),
        pytest.param("doctree", custom_sample, id="doctree"),
    ],
)
def test_doctree_write(file_ext, content, tmp_path):
    sample_file = tmp_path / f"declarative_fixture.{file_ext}"
    sample_file.write_text(content)
    parse_doctree_file(sample_file, tmp_path)

    pages = ("docs/index.md", "docs/guides/foo.md", "docs/guides/bar.md")
    for page_path in pages:
        assert Path(tmp_path / page_path).exists()

    contents = []
    for page_path in pages:
        content = Path(tmp_path / page_path).read_text()
        contents.append(content)
        assert "# check-title" in content
        assert "check-content" in content
        assert "[[ project1 ]]" not in content
        assert "[[ project2 ]]" not in content

    print()
    print(f"To check manually cd to:\n{tmp_path}")
