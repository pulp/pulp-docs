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
- [x] **Reference Build**: figure out how to build each repository Reference section, or if that will be pre-build individually.
- [x] **REST Api Build**: building the restapi docs is not trivial, so I added a workaround (link to existing pages).
- [x] **Landing Page**: use [this](https://aws.github.io/copilot-cli/) as a base.
- [ ] **CI Build**: Create CI workflow that setup fixtures and build the demo prototype.
- [ ] **Ignore Missing**: assure repositories with missing data won't break the build, so we can do it gradually. 
- [ ] **Test w/ pulp_rpm fork**: assure it works with the real repository.

