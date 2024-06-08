import re
from pathlib import Path
def read_files():
    return list(Path("staging_docs/sections/blog/posts/").glob("*.md"))

def fix_blog_posts():
    """
    Problems:
    * add heading zero to filenames missing it: yyyy-mm-d
    * delete "-  date:" lines from frontmatter
    * add new based on filename
    * quote floats that should be strings, like "-  2.0"
        
    """
    for file in read_files():
        this_date_split = file.name.split("-")[:3]
        if len(this_date_split[-1]) == 1:
            this_date_split[-1] = "0" + this_date_split[-1]
        this_date = "-".join(this_date_split)

        raw = file.read_text()
        # fix floats
        raw = re.sub(r"\n\s+-\s*(\d+\.\d+)", r'\n  - "\1"', raw, 1)

        # use aware TZ
        if "- date:" not in raw:
            raw = re.sub(r"---\s*\n", f"---\ndate: {this_date}T20:55:50+00:00\n", raw, 1)

        # add excerpt separator
        raw = re.sub(r"\n---\s*\n", "\n---\n<!-- more -->\n", raw, 1)
        file.write_text(raw)

def fix_floats():
    for file in read_files():
        raw = file.read_text()
        raw = re.sub(r"\n  -\s*(\d+\.\d+)", r'\n  - "\1"', raw, 1)
        file.write_text(raw)
        
    
fix_blog_posts()
