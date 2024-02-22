---
hide:
  - toc
---
<div class="hero-header" markdown>

<h1 class="landing-page-h1"></h1>

## This section is for **users**

Common needs are to *create, sync, publish and interact with repositories*.



<div class="grid cards" markdown>

-   **Get Started**

    ---
    
    Complete the starter tutorial to learn in pratice the basics of managing content in Pulp.

    
-   **Understand the docs**
    
    ---

    Pulp has a rich ecosystem of plugins.
    Understanding the docs can help you find information more efficiently.

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

