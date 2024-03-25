---
hide:
  - toc
---

# Developer Guide {.hide-h1}

<div class="hero-header" markdown>

## This section is for Pulp **developers**

Common needs are to *improve docs, fix bugs and add features*.



<div class="grid cards" markdown>

-   **Contributing**

    ---
    
    Learn the basic for contributing to Pulp: opening PRs, code style, releases cycles and versioning.

    
-   **Deep Dive**
    
    ---

    Dive-in into Pulp code and architecture to help extend, improve and move the project foward.

    
</div>
</div>

---

## Quick Links


{% for repo_type in ("core", "content") %}
Repo | Version | Rest API | Github Page | Changelog
--- | --- | --- | --- | --- 
{% for repo in get_repos(repo_type) -%}
{{ repo.title }} | `{{ repo.version }}` | <a href="{{ repo.rest_api_url}}" target="_blank">:link:</a> | [:link:]({{ repo.codebase_url }}) | [:link:]({{ repo.changelog_url }})
{% endfor %}
{% endfor %}

Repo | Version | Code (Github) | Changelog
--- | --- | --- | --- 
{% for repo in get_repos("other") -%}
{{ repo.title }} | `{{ repo.version }}` | [:link:]({{ repo.codebase_url }}) | [:link:]({{ repo.changelog_url }})
{% endfor %}

