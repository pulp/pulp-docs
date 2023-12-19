# Unified Documentation builder for Pulp Project

This is a demo of using [Diataxis](#) ideas to scafold a new unified documentation for the Pulp Project with mkdocs.
The primary concerts of the demo is to orient content organization.

## Runninng Locally

### 1. Setup Fixture

Here we'll setup the fixtures, which are generated repositories which contain:

- `/docs` folder populated with fake data. Complies with proposed persona x content-types matrix.
- `/docs/doctree.json` a metadata file containing mainly file listings. Used in pre-build step to create the main `mkdocs.yml` 

```bash
$ pip install -r requirements.txt
$ doc-builder generate-fixtures # TODO
```

### 2. Run Server

```bash
$ mkdocs serve
```


## TODO

- [x] **Aggregation**: aggregate content from repositories in the desired main-schema.
- [ ] **Reference Build**: figure out how to build each repository Reference section, or if that will be pre-build individually.
- [ ] **Ignore Missing**: assure repositories with missing data won't break the build, so we can do it gradually. 
- [ ] **REST Api Build**: figure out how to build each repository REST Api section, or if that will be pre-build individually. Maybe research about a unified API docs. That should be more challenging.
- [ ] **Landing Page**: use [this](https://aws.github.io/copilot-cli/) as a base.

