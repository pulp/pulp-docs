# Create plugin Overview Pages

There are two plugin overview pages:

- One for "User Manual" (e.g, `User Manual > Plugins > RPM`)
- One for "Developer Manual" (e.g, `Developer Manual > Plugins > RPM`)

These pages contains an introductory text for its target audicence and a generated ToC.
Also, note that:

- If no custom overview page is found, one will be generated.
- A ToC will always be appended this file, even if you provide a custom page.

## Create plugin overviews

Create files named `index.md` in the appropriate directories.

```bash
# "User Manual" Overview
touch docs/index.md

# "Dev Manual" Overview
touch docs/dev/index.md
```

## Writing style tips

Things to keep in mind:

- **Audience:** Target newcomers. Experienced users will probably use the ToC or the search.
- **Format:** Synopsis + Roadmap. Tell what your plugin is, what it does and a simple roadmap for starting.
- **Size:** Keep it brief. This should an easy win for the user before he starts this journey.
