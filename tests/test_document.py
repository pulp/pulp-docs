from mockrepos.main import Document
from pathlib import Path


def test_create_document(tmp_path):
    document = Document(tmp_path, "how-to-do-that", "guide")
    assert document

    document.create()
    assert Path(tmp_path / "how-to-do-that.md").exists()
