# Unified Documentation builder for Pulp Project

This is a demo of using [Diataxis](#) ideas to scafold a new unified documentation for the Pulp Project with mkdocs.
The primary concerts of the demo is to orient content organization.

## Runninng Locally

Fixtures are fake respositories with code and docs. They are located in `tests/fixtures/`.

Hopefully, this should run the fixture setup:

```bash
$ pip install -r requirements.txt
$ mkdocs serve
```

### 2. Run Server

```bash
$ mkdocs serve
```

## TODO

- Basic features:
  - [x] **Aggregation**: aggregate content from repositories in the desired main-schema.
  - [x] **Reference Build**: figure out how to build each repository Reference section, or if that will be pre-build individually.
  - [x] **REST Api Build**: building the restapi docs is not trivial, so I added a workaround (link to existing pages).
  - [ ] **GitHub Downloader**: downloader to get the latests release codebase from a repo. (currently mocking w/ local copies)
  - [ ] **Flexbile Configuration**: currently, the fixture repos are hardcoded
- Others:
  - [ ] **`pulp-docs build + serve`**: create this command to build the docs
  - [ ] **CI Build**: create CI.
  - [ ] **Test with forks**: assure it works with the real repository.

