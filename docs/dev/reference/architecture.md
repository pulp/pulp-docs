# Understanding Pulp Docs

This page explains some core design and concepts of the Pulp Docs tool.

## Architecture

The Pulp Docs tool is a python package that provides a cli, which we'll refer as `pulp-docs`.
At it's core it's an mkdocs plugin, which we'll call *PulpDocs* from now on.
Also, it extends from `mkdocs` cli by leveraging `click` composable features.

The main configuration file for the system is the Pulp Docs's `mkdocs.yml` file, which is the mkdocs entrypoint.
Through that, the *PulpDocs* plugin is registered and can act on the building process to perform various interventions, like the selection of components to use, the construction of the navigation and the creation of dynamic pages.
The main mechanism used for such interventions is the mkdocs' event/hook API.

As mentioned, the `pulp-docs` cli extends `mkdocs` cli.
The extra features it provides are also based on the PulpDocs plugin definition in the `mkdocs.yml`.

To be an effective part of the PulpDocs website, a component must satisfy two requirements:

1. Be registered as a *PulpDocs* component in the `mkdocs.yml`
1. Contain `docs/` directory following the [Pulp Docs Content Structure](#pulp-docs-content-structure)

The registration is centralized and it includes essential information of a component, like how to fetch it, what kind of component it is and how to display it's name.

## Pulp Docs Content Structure

The structure is based on Diataxis principles, where content is supposed to satisfy a specific [Persona](#persona)
and one of the [Basic User Needs](#basic-user-needs).
Although Diataxis doesn't enforce a specific structure, currently *PulpDocs* requires content to fit into a strict directory tree.

Below is the structure where content should fit in.
Empty directories are ignored and special `index.md` files can be omitted.

```bash
docs/
  index.md  # Component homepage
  user/
    guides/
    learn/
    reference/
    tutorials/
  admin/
    guides/
    learn/
    reference/
    tutorials/
  dev/
    index.md  # Component homepage for devs
    guides/
    learn/
    reference/
    tutorials/
```

## Concepts

* <a id="pulpdocs-plugin" href="#pulpdocs-plugin">PulpDocs</a>: The Pulp Docs mkdocs plugin.
* <a id="persona" href="#persona">Persona</a>: A user class with a specific set of needs.
* <a id="basic-user-needs" href="#basic-user-needs">Basic User Needs</a>: The 4 categories that expresses the need of aquisition/application of skills and the cognition/action aspect of that need: Tutorial, How-To-Guide, Explanation, Reference. See <https://diataxis.fr/compass/>.

## Further Reading

- [Mkdocs Plugins](https://www.mkdocs.org/dev-guide/plugins/#developing-plugins>) - Understand how an Mkdocs Plugin plugin work.
- [Diataxis](https://diataxis.fr/start-here/) - Understand the underlying principles for organizing content
- [The new Pulp "Unified Docs"](https://hackmd.io/eE3kG8qhT9eohRYbtooNww?view) - Original design document for this project
