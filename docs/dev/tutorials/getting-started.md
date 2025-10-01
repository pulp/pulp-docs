# Getting Started

## Install pulp-docs

Install the distribution package from git using your preferred tool.

=== "pipx"

    ```bash
    pipx install git+https://github.com/pulp/pulp-docs@main
    ```

=== "uv tool"

    ```bash
    uv tool install git+https://github.com/pulp/pulp-docs@main
    ```

=== "pip"

    ```bash
    pip --user install git+https://github.com/pulp/pulp-docs@main
    ```

Then, make sure you can run:

```bash
$ pulp-docs
Usage: pulp-docs [OPTIONS] COMMAND [ARGS]...
(...)
```

## Serve draft docs

As a pulp developer, you might not have *all* of the Pulp components checked out on your workspace.
Or even if you have, you might want to preview only a subset of them, like just the one you're working on.
Here we'll show a few possibilities for serving locally.

From the root of some component repository run:

```bash
# requires all components to be present
pulp-docs serve

# doesn't require all components to be present
pulp-docs serve --draft

# select only pulp_rpm and look for it at the parent dir
pulp-docs serve --draft --path pulp_rpm@..

# select only pulpcore and pulp_rpm and look for them at the parent dir
pulp-docs serve --draft --path pulp_rpm@..:pulpcore@..
```

!!! tip

    Append `--dry-run` to preview what plugins are being selected before start serving.

Refer to `--help` to explore more options.

## Run the CI build

So maybe your component's docs-CI fails and you are in a "But it works on my machine!" situation.
To more closely reproduce what the CI does, you'll need to checkout `pulp-docs` and make sure it has the latest changes.
Hopefully, there will be some general instruction on the CI logs too.

In any case, here is an example for pulpcore.
Note that the component and the pulp-docs checkout should be siblings.

```bash
$ git clone https://github.com/pulp/pulp-docs
$ ls
pulpcore pulp-docs
$ cd pulp-docs
$ make docs-ci COMPONENT=pulpcore

# you might want to serve the built with something like:
$ python -m http.server -d site
```
