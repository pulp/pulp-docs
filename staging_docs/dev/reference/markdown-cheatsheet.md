# Markdown Cheatsheet

There are basic markdown features recommended for use in Pulp.

### Internal links

=== "Template"

    ```markdown
    [My Link](site:{repo-name}/docs/{persona}/{content-type}/some-page.md).
    ```

=== "Sample"

    ```markdown
    [My Link](site:pulp-docs/docs/dev/reference/markdown-cheatsheet.md).
    ```

=== "Sample Rendered"

    ```markdown
    [My Link](http://127.0.0.1:8000/pulp-docs/docs/dev/reference/markdown-cheatsheet/).
    ```

- This is enabled by [mkdocs-site-urls](https://github.com/octoprint/mkdocs-site-urls) plugin.
- This is preferred over *relative* links because of our complex structure. See tradeoffs [here](https://github.com/pulp/pulp-docs/issues/2)


### Codeblocks


=== "Raw"

    ````
    ```
    <location "/pulp/api/v3/foo_route">
    proxypass /pulp/api http://${pulp-api}/pulp/api
    proxypassreverse /pulp/api http://${pulp-api}/pulp/api
    requestheader set foo "asdf"
    </location>
    ```
    ````

    ---

    ```
    <location "/pulp/api/v3/foo_route">
    proxypass /pulp/api http://${pulp-api}/pulp/api
    proxypassreverse /pulp/api http://${pulp-api}/pulp/api
    requestheader set foo "asdf"
    </location>
    ```

=== "Python Language"

    ````
    ```python
    serializer = mymodelserializer(data=data)
    serializer.is_valid(raise_exception=true)
    instance = serializer.create(serializer.validated_data)
    ```
    ````

    ---

    ```python
    serializer = mymodelserializer(data=data)
    serializer.is_valid(raise_exception=true)
    instance = serializer.create(serializer.validated_data)
    ```

=== "Python REPL"

    ````
    ```python
    >>> serializer = mymodelserializer(data=data)
    >>> serializer.is_valid(raise_exception=true)
    >>> instance = serializer.create(serializer.validated_data)
    Some output
    ```
    ````

    ---

    ```python
    >>> serializer = mymodelserializer(data=data)
    >>> serializer.is_valid(raise_exception=true)
    >>> instance = serializer.create(serializer.validated_data)
    Some output
    ```

=== "With 'Title'"

    ````
    ```bash title="script.sh"
    pulp file repository update --name myrepo --retained-versions 1
    ```
    ````

    ---

    ```bash title="script.sh"
    pulp file repository update --name myrepo --retained-versions 1
    ```

### Tabbed content


<div class="grid" markdown>

````
=== "Run"

    ```bash
    cat myfile.txt
    ```

=== "Output"

    ```bash
    line1
    line2
    line3
    ```
````

=== "Run"

    ```bash
    cat myfile.txt
    ```

=== "Output"

    ```bash
    line1
    line2
    line3
    ```

</div>

- [See mkdocs-material](https://squidfunk.github.io/mkdocs-material/reference/content-tabs/#usage)
- Each tab title must be in quotes
- Each tab block must have 4 spaces of indent
- Put space around `=== "Title"`

### Admonitions

[See mkdocs-material](https://squidfunk.github.io/mkdocs-material/reference/admonitions/#supported-types)

Use them wisely.

