def test_create_tree(create_tree):
    tree = """
    === docs/index.md
    # hello world

    [foo](bar.md)

    === docs/foo.md
    This is the foo file
    """
    rootdir, files = create_tree(tree)
    created_file_content = {}
    for file in rootdir.rglob("*"):
        if not file.is_file():
            continue
        content = file.read_text()
        created_file_content[str(file.relative_to(rootdir))] = content

    assert len(files) == 2
    assert sorted(created_file_content.keys()) == ["docs/foo.md", "docs/index.md"]

    assert "[foo](bar.md)" in created_file_content["docs/index.md"]
    assert "[foo](bar.md)" not in created_file_content["docs/foo.md"]

    assert "This is the foo file" in created_file_content["docs/foo.md"]
    assert "This is the foo file" not in created_file_content["docs/index.md"]
