# Getting Started

## Install the package

Install it as any python package using your preferred method.

=== "pipx"

    ```bash
    pipx install git+https://github.com/pulp/pulp-docs --include-deps
    ```

=== "pip"

    ```bash
    pip --user install git+https://github.com/pulp/pulp-docs
    ```

## Start serving

By default, `pulp-docs` will try to use repos in the parent dir that matches on of the supported plugins.

Assure you are in a supported repo directory and run:

```bash
pulp-docs serve
```
